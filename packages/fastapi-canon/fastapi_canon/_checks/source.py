"""A deliberately bounded Python symbol index; never imports inspected code."""

from __future__ import annotations

import ast
import builtins
from dataclasses import dataclass, field
from pathlib import Path

type FunctionNode = ast.FunctionDef | ast.AsyncFunctionDef
type Environment = dict[str, str]


def _walk_error(error: OSError) -> None:
    raise error


@dataclass
class Definition:
    name: str
    module: str
    node: FunctionNode | ast.ClassDef
    owner: str | None = None


@dataclass
class Source:
    paths: dict[str, Path] = field(default_factory=dict)
    definitions: dict[str, Definition] = field(default_factory=dict)
    bindings: dict[str, tuple[str, ast.expr] | str] = field(default_factory=dict)
    uncertain: dict[str, list[str]] = field(default_factory=dict)
    nested: list[Definition] = field(default_factory=list)
    touched: set[str] = field(default_factory=set)

    @classmethod
    def read(cls, roots: list[Path]) -> Source:
        source = cls()
        for root in roots:
            root = root.resolve()
            if not root.is_dir():
                raise ValueError(f"source root is not a directory: {root}")
            for directory, directories, files in root.walk(on_error=_walk_error):
                directories[:] = sorted(
                    name
                    for name in directories
                    if not name.startswith(".")
                    and name not in {"__pycache__", "node_modules"}
                )
                for filename in sorted(files):
                    if not filename.endswith(".py"):
                        continue
                    path = directory / filename
                    parts = path.relative_to(root).with_suffix("").parts
                    package = filename == "__init__.py"
                    module = ".".join(parts[:-1] if package else parts)
                    if module in source.paths:
                        if source.paths[module] == path:
                            continue
                        raise ValueError(f"duplicate module {module!r}: {path}")
                    source.paths[module] = path
                    tree = ast.parse(path.read_text("utf-8-sig"), filename=str(path))
                    source._index(module, tree.body, package=package)
                    indexed = {id(item.node) for item in source.definitions.values()}
                    source.nested.extend(
                        Definition(
                            f"{module}.<local>.{node.name}:{node.lineno}", module, node
                        )
                        for node in ast.walk(tree)
                        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
                        and id(node) not in indexed
                    )
        return source

    def _index(self, module: str, body: list[ast.stmt], *, package: bool) -> None:
        for node in body:
            if isinstance(node, ast.Import):
                for alias in node.names:
                    local = alias.asname or alias.name.split(".")[0]
                    self.bindings[f"{module}.{local}"] = (
                        alias.name if alias.asname else local
                    )
            elif isinstance(node, ast.ImportFrom):
                prefix = module.split(".") if package else module.split(".")[:-1]
                if node.level:
                    prefix = prefix[: len(prefix) - node.level + 1]
                    target = ".".join(
                        [*prefix, *([node.module] if node.module else [])]
                    )
                else:
                    target = node.module or ""
                for alias in node.names:
                    self.bindings[f"{module}.{alias.asname or alias.name}"] = (
                        f"{target}.{alias.name}"
                    )
            elif isinstance(node, ast.Assign):
                for target_node in node.targets:
                    if isinstance(target_node, ast.Name):
                        if f"{module}.{target_node.id}" in self.bindings:
                            self.uncertain.setdefault(module, []).append(
                                f"reassigned module binding: {target_node.id}"
                            )
                        self.bindings[f"{module}.{target_node.id}"] = module, node.value
                    else:
                        self.uncertain.setdefault(module, []).append(
                            "unsupported module assignment"
                        )
            elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                if node.value is not None:
                    self.bindings[f"{module}.{node.target.id}"] = module, node.value
            elif isinstance(node, ast.TypeAlias) and isinstance(node.name, ast.Name):
                self.bindings[f"{module}.{node.name.id}"] = module, node.value
            elif isinstance(
                node,
                ast.AugAssign
                | ast.Delete
                | ast.For
                | ast.While
                | ast.Try
                | ast.With
                | ast.Match,
            ):
                self.uncertain.setdefault(module, []).append(
                    "dynamic module declarations"
                )
            elif isinstance(
                node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef
            ):
                name = f"{module}.{node.name}"
                self.definitions[name] = Definition(name, module, node)
                if isinstance(node, ast.ClassDef):
                    for member in node.body:
                        if isinstance(member, ast.FunctionDef | ast.AsyncFunctionDef):
                            key = f"{name}.{member.name}"
                            self.definitions[key] = Definition(
                                key, module, member, name
                            )
            elif isinstance(node, ast.If):
                # In particular, imports guarded by TYPE_CHECKING remain available.
                self._index(module, node.body, package=package)
                self._index(module, node.orelse, package=package)
                if ast.unparse(node.test) not in {
                    "TYPE_CHECKING",
                    "typing.TYPE_CHECKING",
                }:
                    self.uncertain.setdefault(module, []).append(
                        "conditional module declarations"
                    )
            elif (
                isinstance(node, ast.Expr)
                and isinstance(node.value, ast.Call)
                and isinstance(node.value.func, ast.Attribute)
                and node.value.func.attr
                in {
                    "append",
                    "extend",
                    "insert",
                    "update",
                    "add_api_route",
                }
            ):
                self.uncertain.setdefault(module, []).append(
                    "dynamic module declarations or contract mutation"
                )

    def canonical(self, name: str, seen: frozenset[str] = frozenset()) -> str:
        module = name.rpartition(".")[0]
        if module in self.paths:
            self.touched.add(module)
        if name in seen:
            return name
        binding = self.bindings.get(name)
        if isinstance(binding, str):
            return self.canonical(binding, seen | {name})
        if binding is not None and isinstance(binding[1], ast.Name | ast.Attribute):
            return self.resolve(binding[1], binding[0], seen=seen | {name}) or name
        # Resolve module aliases and re-exported classes in dotted references.
        prefix, separator, member = name.rpartition(".")
        if separator and prefix in self.bindings and prefix not in seen:
            resolved = self.canonical(prefix, seen | {name})
            if resolved != prefix:
                return self.canonical(f"{resolved}.{member}", seen | {name})
        return name

    def resolve(
        self,
        node: ast.expr,
        module: str,
        env: Environment | None = None,
        *,
        seen: frozenset[str] = frozenset(),
    ) -> str | None:
        self.touched.add(module)
        env = env or {}
        text = ast.unparse(node)
        if text in env:
            return env[text] or None
        if isinstance(node, ast.Name):
            local = f"{module}.{node.id}"
            if local in self.bindings or local in self.definitions:
                return self.canonical(local, seen)
            if hasattr(builtins, node.id):
                return f"builtins.{node.id}"
        elif isinstance(node, ast.Attribute):
            parent = self.resolve(node.value, module, env, seen=seen)
            if parent:
                candidate = self.canonical(f"{parent}.{node.attr}", seen)
                if candidate in self.definitions or parent not in self.definitions:
                    return candidate
                method = self.method(parent, node.attr)
                return method.name if method else candidate
        return None

    def value(self, node: ast.expr, module: str) -> tuple[str, ast.expr]:
        seen: set[str] = set()
        while name := self.resolve(node, module):
            if name in seen:
                break
            seen.add(name)
            binding = self.bindings.get(name)
            if binding is None or isinstance(binding, str):
                break
            module, node = binding
        return module, node

    def annotation(
        self, node: ast.expr, module: str, seen: frozenset[int] = frozenset()
    ) -> str | None:
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            try:
                node = ast.parse(node.value, mode="eval").body
            except SyntaxError:
                return None
        module, node = self.value(node, module)
        if id(node) in seen:
            return None
        seen = seen | {id(node)}
        if isinstance(node, ast.Subscript):
            wrapper = self.resolve(node.value, module)
            if wrapper in {
                "typing.Annotated",
                "typing_extensions.Annotated",
                "dishka.FromDishka",
                "dishka.integrations.fastapi.FromDishka",
            }:
                first = (
                    node.slice.elts[0]
                    if isinstance(node.slice, ast.Tuple)
                    else node.slice
                )
                return self.annotation(first, module, seen)
            return None
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
            # Optional[T] after a guard still has T's methods; absence adds no
            # application-defined explicit exceptions to the supported subset.
            if isinstance(node.right, ast.Constant) and node.right.value is None:
                return self.annotation(node.left, module, seen)
            if isinstance(node.left, ast.Constant) and node.left.value is None:
                return self.annotation(node.right, module, seen)
        return self.resolve(node, module)

    def mro(self, name: str, seen: frozenset[str] = frozenset()) -> list[str] | None:
        if name in seen:
            return None
        if name.startswith("builtins."):
            value = getattr(builtins, name.split(".")[1], None)
            if isinstance(value, type):
                return [f"builtins.{base.__name__}" for base in value.__mro__]
        definition = self.definitions.get(name)
        if definition is None or not isinstance(definition.node, ast.ClassDef):
            return None
        bases = [
            self.resolve(base, definition.module) for base in definition.node.bases
        ]
        if not bases:
            bases = ["builtins.object"]
        sequences: list[list[str]] = []
        for base in bases:
            order = self.mro(base, seen | {name}) if base else None
            if order is None:
                return None
            sequences.append(order.copy())
        sequences.append([base for base in bases if base is not None])
        result = [name]
        while remaining := [sequence for sequence in sequences if sequence]:
            candidate = next(
                (
                    seq[0]
                    for seq in remaining
                    if all(seq[0] not in other[1:] for other in remaining)
                ),
                None,
            )
            if candidate is None:
                return None
            result.append(candidate)
            for sequence in remaining:
                if sequence[0] == candidate:
                    sequence.pop(0)
        return result

    def method(self, owner: str, name: str) -> Definition | None:
        # Direct methods can be resolved even when an external base is unknown.
        for base in self.mro(owner) or [owner]:
            definition = self.definitions.get(f"{base}.{name}")
            if definition is not None:
                return definition
        return None

    def exception(self, name: str) -> bool:
        return "builtins.Exception" in (self.mro(name) or [])

    def environment(self, function: Definition) -> Environment:
        assert isinstance(function.node, ast.FunctionDef | ast.AsyncFunctionDef)
        env: Environment = {}
        arguments = function.node.args
        for arg in [*arguments.posonlyargs, *arguments.args, *arguments.kwonlyargs]:
            env[arg.arg] = ""
            if arg.annotation is not None:
                resolved = self.annotation(arg.annotation, function.module)
                if resolved:
                    env[arg.arg] = resolved
        if function.owner:
            env["self"] = function.owner
            constructor = self.method(function.owner, "__init__")
            if constructor and isinstance(constructor.node, ast.FunctionDef):
                constructor_env: Environment = {"self": function.owner}
                for arg in (
                    constructor.node.args.posonlyargs
                    + constructor.node.args.args
                    + constructor.node.args.kwonlyargs
                ):
                    if arg.annotation:
                        resolved = self.annotation(arg.annotation, constructor.module)
                        if resolved:
                            constructor_env[arg.arg] = resolved
                for statement in constructor.node.body:
                    if isinstance(statement, ast.Assign):
                        resolved = self.resolve(
                            statement.value, constructor.module, constructor_env
                        )
                        if resolved:
                            for target in statement.targets:
                                if isinstance(target, ast.Attribute):
                                    env[ast.unparse(target)] = resolved
        return env
