import fnmatch
import re
from typing import Any


class MatchCondition:
    """Matching condition base class"""

    def __eq__(self, other: str):
        raise NotImplementedError

    def __repr__(self) -> str:
        raise NotImplementedError


class Not(MatchCondition):
    """Inverted matching condition"""

    def __init__(self, condition: MatchCondition | Any):
        self.__condition = condition

    def __eq__(self, other: Any):
        return other != self.__condition

    def __contains__(self, item: Any):
        return item not in self.__condition

    def __repr__(self) -> str:
        return f'Not({self.__condition})'


class Regex(MatchCondition):
    """Regex pattern matching condition"""

    def __init__(self, re_pattern: str):
        self.__pattern = re_pattern
        self.__matcher = re.compile(re_pattern).match

    def __eq__(self, other: str):
        return self.__matcher(other) is not None

    def __repr__(self) -> str:
        return f'Regex({self.__pattern})'


class Glob(MatchCondition):
    """Glob pattern matching condition. Supports `*`, `?`, `[chars]` and `[!chars]` matching."""

    def __init__(self, glob_pattern: str):
        self.__pattern = glob_pattern
        re_pattern = fnmatch.translate(glob_pattern)
        self.__matcher = re.compile(re_pattern).match

    def __eq__(self, other: str):
        return self.__matcher(other) is not None

    def __repr__(self) -> str:
        return f'Glob({self.__pattern})'