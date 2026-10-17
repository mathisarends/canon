import warnings

from fastapi_streams.codegen.ir import (
    Array,
    Contract,
    Intersection,
    Object,
    Reference,
    Type,
    Union,
)


class OptionalDiscriminatorWarning(UserWarning):
    """An event union may be missing the field used to select its variant."""


def warn_optional_discriminators(contract: Contract) -> None:
    """Diagnose event discriminators without changing the declared requiredness."""
    declarations = {item.name: item.type for item in contract.declarations}
    for operation in contract.operations:
        for name, field in sorted(_optional_fields(operation.event, declarations)):
            warnings.warn(
                f"{operation.operation_id} ({operation.method} "
                f"{operation.path}): event schema {name!r} has optional "
                f"discriminator {field!r}. Missing tags can prevent "
                "variant selection. The generated field remains optional; "
                "if the serializer always emits it, mark it required in "
                "the output schema. See docs/codegen.md#event-discriminators.",
                OptionalDiscriminatorWarning,
                stacklevel=2,
            )


def _optional_fields(
    type_: Type, declarations: dict[str, Type]
) -> set[tuple[str, str]]:
    seen: set[str] = set()
    result: set[tuple[str, str]] = set()

    def visit(node: Type) -> None:
        if isinstance(node, Reference):
            if node.name not in seen:
                seen.add(node.name)
                visit(declarations[node.name])
        elif isinstance(node, Array):
            visit(node.item)
        elif isinstance(node, Object):
            for field in node.fields:
                visit(field.type)
            if node.additional is not None:
                visit(node.additional)
        elif isinstance(node, Union | Intersection):
            if isinstance(node, Union) and node.discriminator:
                for member in node.members:
                    model = _resolve(member, declarations)
                    if not isinstance(model, Object):
                        continue
                    field = next(
                        (f for f in model.fields if f.name == node.discriminator), None
                    )
                    if field is not None and not field.required:
                        name = (
                            member.name if isinstance(member, Reference) else "inline"
                        )
                        result.add((name, field.name))
            for member in node.members:
                visit(member)

    visit(type_)
    return result


def _resolve(type_: Type, declarations: dict[str, Type]) -> Type:
    seen: set[str] = set()
    while isinstance(type_, Reference) and type_.name not in seen:
        seen.add(type_.name)
        type_ = declarations[type_.name]
    return type_
