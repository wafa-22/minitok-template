r"""Part A1 — Token specification loader and validator.

A token specification is a JSON object:

{
  "tokens": [
    {"name": "WS",    "regex": "( |\t|\n)*",        "skip": true},
    {"name": "FLOAT", "regex": "<digit>*.<digit>*", "skip": false},
    {"name": "INT",   "regex": "<digit>*",          "skip": false},
    {"name": "IDENT", "regex": "<letter>(<letter>|<digit>|_)*", "skip": false},
    {"name": "OP",    "regex": "==|=|\+|-|\*|/|<|>", "skip": false}
  ]
}

Regex syntax (a small extension of Sipser §1.3):
  literals          letters, digits, and the operator characters + - * / < > =
                    when they are NOT acting as operators (use \\ to escape
                    operator chars: \\* means literal asterisk)
  <letter>          shorthand class: a-z A-Z
  <digit>           shorthand class: 0-9
  a|b               union
  ab                concatenation
  a*                Kleene star (in this spec: ONE or more repetitions, i.e.
                    the regular operation a(a)*  — "plus" — because a token
                    must be non-empty; see README §A2)
  ( ... )           grouping
  Precedence: * > concatenation > |

`skip: true` token classes (typically whitespace/comments) are recognized
and discarded by the scanner instead of being emitted.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path


class SpecError(ValueError):
    """Raised when a token specification is invalid."""


@dataclass
class TokenClass:
    name: str
    regex: str
    skip: bool = False


@dataclass
class TokenSpec:
    tokens: list[TokenClass] = field(default_factory=list)

    @property
    def names(self) -> list[str]:
        return [t.name for t in self.tokens]


def can_match_empty(regex):
    """Check whether a regex can match an empty string."""
    i = 0

    def expression():
        nonlocal i
        empty = sequence()

        while i < len(regex) and regex[i] == "|":
            i += 1
            empty = sequence() or empty

        return empty

    def sequence():
        nonlocal i
        empty = True

        while i < len(regex) and regex[i] not in ")|":
            empty = atom() and empty

        return empty

    def atom():
        nonlocal i

        if regex[i] == "(":
            i += 1
            empty = expression()

            if i >= len(regex) or regex[i] != ")":
                raise SpecError("Unbalanced parentheses")

            i += 1

        elif regex[i] == "\\":
            i += 1
            if i >= len(regex):
                raise SpecError("Invalid escape")
            i += 1
            empty = False

        elif regex[i] == "<":
            end = regex.find(">", i)
            if end == -1:
                raise SpecError("Invalid shorthand")
            i = end + 1
            empty = False

        else:
            i += 1
            empty = False

        # In MiniTok, * means one or more.
        if i < len(regex) and regex[i] == "*":
            i += 1

        return empty

    result = expression()

    if i != len(regex):
        raise SpecError("Invalid regex")

    return result

def load_spec(source: str | Path) -> TokenSpec:
    """Load and validate a token specification from a JSON file path or a
    JSON string.

    Must raise SpecError (with a helpful message) for:
      - malformed JSON
      - missing/empty "tokens" list
      - duplicate token names
      - empty regex strings
      - regexes that can match the empty string (tokens must be non-empty)
      - unknown shorthand classes or unbalanced parentheses

    Returns a TokenSpec preserving the declared order (order defines
    priority for maximal-munch tie-breaking: earlier = higher priority).
    """
    # TODO(PART A1): implement
 #raise NotImplementedError("load_spec is not implemented yet (Part A1)")

    # Read the JSON data
    try:
        if isinstance(source, Path):
            text = source.read_text(encoding="utf-8")
        elif source.strip().startswith("{"):
            text = source
        else:
            text = Path(source).read_text(encoding="utf-8")

        data = json.loads(text)

    except json.JSONDecodeError:
        raise SpecError("Invalid JSON format")
    except OSError:
        raise SpecError("Cannot read specification file")

    if not isinstance(data, dict):
        raise SpecError("Specification must be an object")

    if "tokens" not in data or not isinstance(data["tokens"], list):
        raise SpecError("Missing or invalid tokens list")

    if len(data["tokens"]) == 0:
        raise SpecError("Tokens list cannot be empty")


    tokens = []
    names = set()

    for item in data["tokens"]:
        if not isinstance(item, dict):
            raise SpecError("Invalid token")

        name = item.get("name")
        regex = item.get("regex")
        skip = item.get("skip", False)

        if not isinstance(name, str) or not name:
            raise SpecError("Invalid token name")

        if name in names:
            raise SpecError("Duplicate token name: " + name)

        if not isinstance(regex, str) or not regex:
            raise SpecError("Invalid regex for " + name)

        if can_match_empty(regex):
            raise SpecError("Regex cannot match empty string: " + name)

        if not isinstance(skip, bool):
            raise SpecError("Invalid skip value")

        # Check parentheses
        depth = 0
        i = 0

        while i < len(regex):
            if regex[i] == "\\":
                i += 2
                continue

            if regex[i] == "(":
                depth += 1
            elif regex[i] == ")":
                depth -= 1
                if depth < 0:
                    raise SpecError("Unbalanced parentheses")

            i += 1

        if depth != 0:
            raise SpecError("Unbalanced parentheses")

        # Check shorthand classes
        import re

        classes = re.findall(r"<([a-zA-Z]+)>", regex)

        for cls in classes:
            if cls not in ("letter", "digit"):
                raise SpecError("Unknown shorthand: " + cls)

        names.add(name)
        tokens.append(TokenClass(name, regex, skip))

    return TokenSpec(tokens)
