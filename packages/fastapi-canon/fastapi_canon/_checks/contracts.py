"""Read Canon declarations and compare them with explicit escaping exceptions."""

from __future__ import annotations

import ast
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from .analysis import ROUTE_METHODS, Analyzer, Flow, Unknown
from .source import Definition, Source

CANON_ROUTER = "fastapi_canon.CanonRouter"
ERROR = "fastapi_canon.Error"
REGISTRY = "fastapi_canon.ErrorRegistry"
DEPENDENCIES = {
    "fastapi.Depends",
    "fastapi.params.Depends",
    "fastapi.Security",
    "fastapi.params.Security",
}


@dataclass(frozen=True)
class Diagnostic:
    code: str
    message: str
    path: str
    line: int
    trace: tuple[str, ...] = ()


@dataclass
class Operation:
    function: str
    path: str
    line: int
    diagnostics: list[Diagnostic] = field(default_factory=list)

    @property
    def complete(self) -> bool:
        return not any(item.code == "CAN003" for item in self.diagnostics)


@dataclass
class Report:
    operations: list[Operation]

    @property
    def gaps(self) -> int:
        return sum(
            item.code != "CAN003"
            for operation in self.operations
            for item in operation.diagnostics
        )

    @property
    def incomplete(self) -> int:
        return sum(not operation.complete for operation in self.operations)

    def as_dict(self) -> dict[str, Any]:
        return {
            "operations": [
                {**asdict(operation), "complete": operation.complete}
                for operation in self.operations
            ],
            "contract_gaps": self.gaps,
            "incomplete_operations": self.incomplete,
        }


def keyword(node: ast.Call, name: str) -> ast.expr | None:
    return next((item.value for item in node.keywords if item.arg == name), None)


class Checker:
    def __init__(self, source: Source) -> None:
        self.source = source
        self.analyzer = Analyzer(source)

    def check(self) -> Report:
        operations: list[Operation] = []
        for function in [*self.source.definitions.values(), *self.source.nested]:
            if not isinstance(function.node, ast.FunctionDef | ast.AsyncFunctionDef):
                continue
            for decorator in function.node.decorator_list:
                if (
                    not isinstance(decorator, ast.Call)
                    or not isinstance(decorator.func, ast.Attribute)
                    or decorator.func.attr not in ROUTE_METHODS
                ):
                    continue
                module, router = self.source.value(
                    decorator.func.value, function.module
                )
                operation = Operation(
                    function.name,
                    str(self.source.paths[function.module]),
                    decorator.lineno,
                )
                if function in self.source.nested:
                    operations.append(operation)
                    self._unknown(
                        operation,
                        "nested route declarations require runtime factory execution",
                    )
                    continue
                constructor = (
                    self.source.resolve(router.func, module)
                    if isinstance(router, ast.Call)
                    else None
                )
                if constructor not in {
                    CANON_ROUTER,
                    "fastapi_canon.router.CanonRouter",
                }:
                    if constructor in {
                        "fastapi.APIRouter",
                        "fastapi.routing.APIRouter",
                        "fastapi.FastAPI",
                    }:
                        continue
                    operations.append(operation)
                    self._unknown(
                        operation, "unresolved or unsupported router declaration"
                    )
                    continue
                assert isinstance(router, ast.Call)
                operations.append(operation)
                self._operation(operation, function, decorator, module, router)
        return Report(operations)

    def _unknown(
        self, operation: Operation, message: str, line: int | None = None
    ) -> None:
        operation.diagnostics.append(
            Diagnostic("CAN003", message, operation.path, line or operation.line)
        )

    def _sequence(
        self,
        node: ast.expr | None,
        module: str,
        operation: Operation,
        seen: frozenset[int] = frozenset(),
    ) -> list[tuple[str, ast.expr]]:
        if node is None:
            return []
        module, node = self.source.value(node, module)
        if id(node) in seen:
            self._unknown(operation, "recursive contract sequence")
            return []
        seen = seen | {id(node)}
        if isinstance(node, ast.List | ast.Tuple | ast.Set):
            result: list[tuple[str, ast.expr]] = []
            for element in node.elts:
                if isinstance(element, ast.Starred):
                    result.extend(
                        self._sequence(element.value, module, operation, seen)
                    )
                else:
                    result.append((module, element))
            return result
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
            return self._sequence(node.left, module, operation, seen) + self._sequence(
                node.right, module, operation, seen
            )
        self._unknown(operation, f"unresolved contract sequence: {ast.unparse(node)}")
        return []

    def _errors(
        self, node: ast.expr | None, module: str, operation: Operation
    ) -> dict[str, str]:
        result: dict[str, str] = {}
        for scope, element in self._sequence(node, module, operation):
            identity = self.source.resolve(element, scope)
            scope, definition = self.source.value(element, scope)
            if not isinstance(definition, ast.Call) or self.source.resolve(
                definition.func, scope
            ) not in {
                ERROR,
                "fastapi_canon.error.Error",
                "fastapi_canon.error.error.Error",
            }:
                self._unknown(
                    operation, f"unresolved Error definition: {ast.unparse(element)}"
                )
                continue
            exception_node = (
                definition.args[0]
                if definition.args
                else keyword(definition, "exception")
            )
            exception = (
                self.source.resolve(exception_node, scope) if exception_node else None
            )
            if (
                identity is None
                or exception is None
                or not self.source.exception(exception)
            ):
                self._unknown(
                    operation, f"unresolved Error exception: {ast.unparse(element)}"
                )
                continue
            result[exception] = identity
        return result

    def _dependencies(
        self, function: Definition, seen: frozenset[str] = frozenset()
    ) -> Flow:
        flow = Flow()
        if function.name in seen:
            flow.unknowns.append(
                Unknown("recursive dependency", function.name, function.node.lineno)
            )
            return flow
        node = function.node
        assert isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
        args = [*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs]
        values: list[ast.expr] = [arg.annotation for arg in args if arg.annotation]
        values.extend(node.args.defaults)
        values.extend(value for value in node.args.kw_defaults if value is not None)
        for expression in values:
            if isinstance(expression, ast.Constant) and isinstance(
                expression.value, str
            ):
                try:
                    expression = ast.parse(expression.value, mode="eval").body
                except SyntaxError:
                    flow.unknowns.append(
                        Unknown(
                            "unresolved dependency annotation",
                            function.name,
                            node.lineno,
                        )
                    )
                    continue
            module, expression = self.source.value(expression, function.module)
            for child in ast.walk(expression):
                if (
                    not isinstance(child, ast.Call)
                    or self.source.resolve(child.func, module) not in DEPENDENCIES
                ):
                    continue
                target = child.args[0] if child.args else keyword(child, "dependency")
                name = self.source.resolve(target, module) if target else None
                dependency = self.source.definitions.get(name or "")
                if dependency and isinstance(
                    dependency.node, ast.FunctionDef | ast.AsyncFunctionDef
                ):
                    flow.extend(self.analyzer.function(dependency))
                    flow.extend(self._dependencies(dependency, seen | {function.name}))
                else:
                    flow.unknowns.append(
                        Unknown(
                            "unresolved FastAPI dependency", function.name, child.lineno
                        )
                    )
        return flow

    def _router_dependencies(
        self, node: ast.Call, module: str, operation: Operation
    ) -> Flow:
        flow = Flow()
        for scope, dependency in self._sequence(
            keyword(node, "dependencies"), module, operation
        ):
            # Reuse the parameter-dependency reader with a synthetic annotated argument.
            argument = ast.arg(arg="dependency", annotation=dependency)
            function = ast.FunctionDef(
                name="dependencies",
                args=ast.arguments(
                    posonlyargs=[],
                    args=[argument],
                    kwonlyargs=[],
                    kw_defaults=[],
                    defaults=[],
                ),
                body=[],
                decorator_list=[],
                type_params=[],
            )
            function.lineno = operation.line
            flow.extend(
                self._dependencies(Definition(f"{scope}.dependencies", scope, function))
            )
        return flow

    def _operation(
        self,
        operation: Operation,
        function: Definition,
        decorator: ast.Call,
        module: str,
        router: ast.Call,
    ) -> None:
        self.source.touched = {function.module, module}
        for call in (router, decorator):
            if any(item.arg is None for item in call.keywords):
                self._unknown(
                    operation, "expanded keyword arguments may change the contract"
                )
        registry_node = keyword(router, "error_registry")
        catalog: dict[str, str] = {}
        if registry_node is not None:
            scope, registry = self.source.value(registry_node, module)
            if isinstance(registry, ast.Call) and self.source.resolve(
                registry.func, scope
            ) in {
                REGISTRY,
                "fastapi_canon.error.ErrorRegistry",
                "fastapi_canon.error.registry.ErrorRegistry",
            }:
                catalog = self._errors(keyword(registry, "errors"), scope, operation)
            else:
                self._unknown(operation, "unresolved ErrorRegistry declaration")
        declared = self._errors(keyword(router, "raises"), module, operation)
        declared.update(
            self._errors(keyword(decorator, "raises"), function.module, operation)
        )
        contracts_known = not operation.diagnostics
        flow = self.analyzer.function(function)
        flow.extend(self._dependencies(function))
        flow.extend(self._router_dependencies(router, module, operation))
        flow.extend(self._router_dependencies(decorator, function.module, operation))
        contracts_known = contracts_known and not any(
            self.source.uncertain.get(scope) for scope in self.source.touched
        )
        seen: set[tuple[str, str]] = set()
        for escape in flow.escapes:
            # Only application-defined exceptions are in scope, not implicit runtime failures.
            if escape.exception.startswith("builtins."):
                continue
            if not contracts_known:
                continue
            mapped = next(
                (
                    catalog[base]
                    for base in self.source.mro(escape.exception) or []
                    if base in catalog
                ),
                None,
            )
            code = "CAN001" if mapped else "CAN002"
            if mapped and mapped in declared.values():
                continue
            key = code, escape.exception
            if key in seen:
                continue
            seen.add(key)
            message = (
                f"{escape.exception}: {mapped} is missing from raises"
                if mapped
                else f"{escape.exception}: no Error mapping in the router registry"
            )
            origin = self.source.definitions[escape.trace[-1]]
            operation.diagnostics.append(
                Diagnostic(
                    code,
                    message,
                    str(self.source.paths[origin.module]),
                    escape.line,
                    escape.trace,
                )
            )
        for unknown in flow.unknowns:
            unknown_origin = self.source.definitions.get(unknown.function)
            path = (
                str(self.source.paths[unknown_origin.module])
                if unknown_origin
                else operation.path
            )
            diagnostic = Diagnostic(
                "CAN003", unknown.message, path, unknown.line, (unknown.function,)
            )
            if diagnostic not in operation.diagnostics:
                operation.diagnostics.append(diagnostic)
        for scope in sorted(self.source.touched):
            for message in dict.fromkeys(self.source.uncertain.get(scope, [])):
                operation.diagnostics.append(
                    Diagnostic("CAN003", message, str(self.source.paths[scope]), 1)
                )


def check(roots: list[Path]) -> Report:
    return Checker(Source.read(roots)).check()
