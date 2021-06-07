"""Support for type parsing used in Application classes and elsewhere."""

# type annotations
from __future__ import annotations
from typing import TYPE_CHECKING

# standard libraries
import re

# static analysis
if TYPE_CHECKING:
    from typing import Any, Union 
    F = Union[float, str]
    I = Union[int, str]
    T = Union[bool, int, float, None, str]

# define library (public) interface
__all__ = ['DictStr', 'DictAny', 'DictDictStr', 'DictDictAny', 'DictListStr', 'DictListAny',
           'ListInt', 'ListFloat', 'ListStr', 'ListAny', 'SafeInt', 'SafeFloat', 'SafeAny', ]

def none(arg: Any) -> None:
    """Coerce if should convert to NoneType."""
    if str(arg).lower() not in (str(None).lower(), 'null'):
        raise ValueError()
    return None

def logical(arg: Any) -> bool:
    """Coerce if should convert to bool."""
    if str(arg).lower() not in (str(b).lower() for b in {True, False}):
        raise ValueError()
    return bool(arg)

def SafeInt(value: Any) -> I:
    """Provide pythonic conversion to int that fails to str."""
    try:
        return int(value)
    except ValueError:
        return str(value)

def SafeFloat(value: Any) -> F:
    """Provide pythonic conversion to float that fails to str."""
    try:
        return float(value)
    except ValueError:
        return str(value)

def SafeAny(arg: Any) -> T:
    """Provide pythonic conversion to sensical type that fails to str."""
    arg = str(arg)
    for func in (logical, int, float, none):
        try:
            return func(arg) # type: ignore
        except ValueError:
            next
    return arg

def ListInt(s: str) -> list[int]:
    """Parse a string of format <VALUE, ...> into a list of ints.""" 
    return [int(i) for i in re.split(r',\s|,|\s', s)]

def ListFloat(s: str) -> list[float]:
    """Parse a string of format <VALUE, ...> into a list of floats.""" 
    return [float(i) for i in re.split(r',\s|,|\s', s)]

def ListStr(s: str) -> list[str]:
    """Parse a string of format <VALUE, ...> into a list of strings."""
    return list(re.split(',', s))

def ListAny(s: str) -> list[T]:
    """Parse a string of format <VALUE, ...> into a list of actual types.""" 
    return [SafeAny(i) for i in re.split(r',\s|,|\s', s)]

def DictStr(s: str) -> dict[str, str]:
    """Parse a string of format <KEY=VALUE, ...> into a dictionary of strings."""
    return dict((k.strip(), v.strip()) for k, v in (re.split(r'=\s|=', i) for i in re.split(r',\s|,', s)))

def DictAny(s: str) -> dict[str, T]:
    """Parse a string of format <KEY=VALUE, ...> into a dictionary of actual types."""
    return dict((k.strip(), SafeAny(v.strip())) for k, v in (re.split(r'=\s|=', i) for i in re.split(r',\s|,', s)))

def DictDictStr(s: str) -> dict[str, dict[str, str]]:
    """Parse a string of format <OPT={KEY=VALUE, ...}, ...> into a nested dictionary of strings."""
    return dict((k.strip(), DictStr(v.strip())) for k, v in [re.split(r'={|=\s{', i) for i in re.split(r'},|}\s,', s[:-1])])

def DictDictAny(s: str) -> dict[str, dict[str, T]]:
    """Parse a string of format <OPT={KEY=VALUE, ...}, ...> into a nested dictionary of actual types."""
    return dict((k.strip(), DictAny(v.strip())) for k, v in [re.split(r'={|=\s{', i) for i in re.split(r'},|}\s,', s[:-1])])

def DictListStr(s: str) -> dict[str, list[str]]:
    """Parse a string of format <OPT=(VALUE, ...), ...> into a dictionary of lists of strings."""
    return dict((k.strip(), ListStr(v.strip())) for k, v in [re.split(r'=\(|=\s\(', i) for i in re.split(r'\),|\)\s,', s[:-1])])

def DictListAny(s: str) -> dict[str, list[T]]:
    """Parse a string of format <OPT=(VALUE, ...), ...> into a dictionary of lists of strings."""
    return dict((k.strip(), ListAny(v.strip())) for k, v in [re.split(r'=\(|=\s\(', i) for i in re.split(r'\),|\)\s,', s[:-1])])
