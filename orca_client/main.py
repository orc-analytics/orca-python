import re
from typing import Any, Dict, List, TypeVar, Callable, TypeAlias
from orca_client.exceptions import InvalidDependency

# Regex patterns for validation
ALGORITHM_NAME = r"^[A-Z][a-zA-Z0-9]*$"
SEMVER_PATTERN = r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$"

Algorithm: TypeAlias = Callable[..., Any]

T = TypeVar("T", bound=Callable)


class Algorithms:
    def __init__(self) -> None:
        self._algorithms: Dict[str, Algorithm] = {}
        self._dependencies: Dict[str, List[str]]


    def has_algorithm(self, name) -> bool:
        return name in self._algorithms

    def flush(self) -> None:
        self._algorithms = {}

    def _add_algorithm(self, name: str, algorithm: Algorithm) -> None:
        if name in self._algorithms:
            raise ValueError(f"Algorithm {name} already exists")
        self._algorithms[name] = algorithm

_algorithmsSingleton = Algorithms()


def algorithm(
    name: str, version: str, depends_on: List[Callable[..., Any]] | None = None
) -> Callable[[Algorithm], Any]:
    """
    Register a function as an Orca Algorithm

    Args:
        name: Name of the algorithm
        version: The algorithm version
        depends_on: List of algorithms whose results the algorithm depends on

    Returns:

    Raises:
        ValueError:
    """
    if not re.match(ALGORITHM_NAME, name):
        raise ValueError(f"Algorithm name '{name}' must be in PascalCase")

    if not re.match(SEMVER_PATTERN, version):
        raise ValueError(
            f"Version '{version}' must follow basic semantic "
            "versioning (e.g., '1.0.0') without release portions"
        )

    if depends_on:
        for dependency in depends_on:
            if dependency not in _algorithmsSingleton._algorithms.values():
                message = (
                    f"Cannot add function `{dependency.__name__}` to dependency stack. All dependencies must "
                    "be decorated with @algorithm before they can be used as dependencies."
                )
                raise InvalidDependency(message)

        # TODO: Check for circular dependencies. It's not easy to create one in python as the function
        # needs to be defined before a dependency can be created, and you can only register depencenies
        # once. But when dependencies are grabbed from a server, circular dependencies will be possible

    compound_algorithm_name = f"{name}_{version}"

    if _algorithmsSingleton.has_algorithm(compound_algorithm_name):
        raise ValueError(
            f"Algorithm `{name}` of version `{version}` is already registered"
        )

    def inner(algo: T):
        def wrapper(*args, **kwargs):
            # setup ready for the algo
            # TODO

            # run the algo
            result = algo(*args, **kwargs)

            # tear down
            # TODO
            return result

        _algorithmsSingleton._add_algorithm(compound_algorithm_name, wrapper)
        return wrapper

    return inner
