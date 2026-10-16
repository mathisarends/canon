import re

from fastapi_streams.codegen.openapi import ContractError

_RESERVED = {
    "break",
    "case",
    "catch",
    "class",
    "const",
    "continue",
    "debugger",
    "default",
    "delete",
    "do",
    "else",
    "enum",
    "export",
    "extends",
    "false",
    "finally",
    "for",
    "function",
    "if",
    "import",
    "in",
    "instanceof",
    "new",
    "null",
    "return",
    "super",
    "switch",
    "this",
    "throw",
    "true",
    "try",
    "typeof",
    "var",
    "void",
    "while",
    "with",
    "yield",
    "let",
    "static",
    "implements",
    "interface",
    "package",
    "private",
    "protected",
    "public",
    "await",
    "constructor",
    "prototype",
    "__proto__",
    "then",
}


def words(value: str) -> list[str]:
    return re.findall(r"[A-Za-z0-9]+", re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", value))


def identifier(value: str, *, upper: bool = False) -> str:
    parts = words(value)
    if not parts:
        raise ContractError(f"Cannot make a TypeScript identifier from {value!r}")
    name = "".join(part[:1].upper() + part[1:] for part in parts)
    if not upper:
        name = name[:1].lower() + name[1:]
    if name[0].isdigit() or name in _RESERVED:
        name = "_" + name
    return name


def slug(value: str) -> str:
    return "-".join(part.lower() for part in words(value)) or "streams"
