"""A small, safe, deterministic subset of JSONLogic (https://jsonlogic.com).

Only comparison and boolean operators are supported. There is no arbitrary code, and
the same subset can be evaluated in TypeScript with json-logic-js. Comparisons with a
missing (None) value are False rather than errors, so an absent feature never fires a
rule by accident.
"""

from collections.abc import Callable, Mapping
from itertools import pairwise
from typing import Any


class JsonLogicError(ValueError):
    pass


def _var(path: str, data: Mapping[str, Any]) -> Any:
    value: Any = data
    for part in path.split("."):
        if not isinstance(value, Mapping) or part not in value:
            return None
        value = value[part]
    return value


def _compare(op: Callable[[Any, Any], bool]) -> Callable[..., bool]:
    def run(*args: Any) -> bool:
        if any(a is None for a in args):
            return False
        try:
            return all(op(a, b) for a, b in pairwise(args))
        except TypeError:
            return False

    return run


_OPS: dict[str, Callable[..., bool]] = {
    "==": _compare(lambda a, b: a == b),
    "!=": _compare(lambda a, b: a != b),
    "<": _compare(lambda a, b: a < b),
    "<=": _compare(lambda a, b: a <= b),
    ">": _compare(lambda a, b: a > b),
    ">=": _compare(lambda a, b: a >= b),
    "in": lambda item, collection: item is not None and item in (collection or []),
    "and": lambda *xs: all(bool(x) for x in xs),
    "or": lambda *xs: any(bool(x) for x in xs),
    "!": lambda x: not bool(x),
}


def evaluate(rule: Any, data: Mapping[str, Any]) -> Any:
    if isinstance(rule, list):
        return [evaluate(item, data) for item in rule]
    if not isinstance(rule, dict):
        return rule
    if len(rule) != 1:
        raise JsonLogicError(f"a rule node must have exactly one operator: {rule}")
    ((op, args),) = rule.items()
    if op == "var":
        return _var(str(args[0] if isinstance(args, list) else args), data)
    if op not in _OPS:
        raise JsonLogicError(f"unsupported operator: {op!r}")
    values = [evaluate(a, data) for a in (args if isinstance(args, list) else [args])]
    return _OPS[op](*values)


def referenced_vars(rule: Any) -> set[str]:
    """Every `var` path a rule reads (for linting against the feature contract)."""
    if isinstance(rule, list):
        return set().union(*(referenced_vars(item) for item in rule)) if rule else set()
    if not isinstance(rule, dict):
        return set()
    ((op, args),) = rule.items()
    if op == "var":
        return {str(args[0] if isinstance(args, list) else args)}
    return referenced_vars(args)
