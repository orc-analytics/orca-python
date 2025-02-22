import re
from typing import Any, Dict, List, TypeVar, Callable, TypeAlias

from orca_client.exceptions import InvalidDependency, InvalidAlgorithmArgument

# Regex patterns for validation
ALGORITHM_NAME = r"^[A-Z][a-zA-Z0-9]*$"
SEMVER_PATTERN = r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$"
WINDOW_TRIGGER = r"^[A-Z][a-zA-Z0-9]*$"

Algorithm: TypeAlias = Callable[..., Any]

T = TypeVar("T", bound=Algorithm)


class Algorithms:
    def __init__(self) -> None:
        self._algorithms: Dict[str, Algorithm] = {}
        self._dependencies: Dict[str, List[Algorithm]] = {}
        self._triggers: Dict[str, List[Algorithm]] = {}

    def _has_algorithm(self, name: str) -> bool:
        return name in self._algorithms

    def _flush(self) -> None:
        self._algorithms = {}

    def _add_algorithm(self, name: str, algorithm: Algorithm) -> None:
        if name in self._algorithms:
            raise ValueError(f"Algorithm {name} already exists")
        self._algorithms[name] = algorithm

    def _add_dependency(self, algorithm: str, dependency: Algorithm) -> None:
        if algorithm not in self._dependencies:
            self._dependencies[algorithm] = [dependency]
        else:
            self._dependencies[algorithm].append(dependency)

    def _add_trigger(self, trigger: str, algorithm: Algorithm) -> None:
        if algorithm not in self._triggers:
            self._triggers[trigger] = [algorithm]
        else:
            self._triggers[trigger].append(algorithm)


_algorithmsSingleton = Algorithms()


def algorithm(
    name: str,
    version: str,
    window_trigger: str,
    depends_on: List[Callable[..., Any]] = [],
) -> Callable[[Algorithm], Any]:
    """
    Register a function as an Orca Algorithm

    Args:
        name: Name of the algorithm
        version: The algorithm version
        window_trigger: The window that triggers the Algorithm or DAG
        depends_on: List of algorithms whose results the algorithm depends on

    Returns:
        Wrapper around the algorithm.

    Raises:
        ValueError:
    """
    if not re.match(ALGORITHM_NAME, name):
        raise InvalidAlgorithmArgument(f"Algorithm name '{name}' must be in PascalCase")

    if not re.match(SEMVER_PATTERN, version):
        raise InvalidAlgorithmArgument(
            f"Version '{version}' must follow basic semantic "
            "versioning (e.g., '1.0.0') without release portions"
        )

    if not re.match(WINDOW_TRIGGER, window_trigger):
        raise InvalidAlgorithmArgument(
            f"Trigger '{window_trigger}' must be in PascalCase"
        )

    compound_algorithm_name = f"{name}_{version}"

    if _algorithmsSingleton._has_algorithm(compound_algorithm_name):
        raise ValueError(
            f"Algorithm `{name}` of version `{version}` is already registered"
        )

    def inner(algo: T) -> T:
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # setup ready for the algo
            # TODO

            # run the algo
            result = algo(*args, **kwargs)

            # tear down
            # TODO
            return result

        _algorithmsSingleton._add_algorithm(compound_algorithm_name, wrapper)
        _algorithmsSingleton._add_trigger(window_trigger, compound_algorithm_name)

        for dependency in depends_on:
            if dependency not in _algorithmsSingleton._algorithms.values():
                message = (
                    f"Cannot add function `{dependency.__name__}` to dependency stack. All dependencies must "
                    "be decorated with @algorithm before they can be used as dependencies."
                )
                raise InvalidDependency(message)
            _algorithmsSingleton._add_dependency(compound_algorithm_name, dependency)

        # TODO: Check for circular dependencies. It's not easy to create one in python as the function
        # needs to be defined before a dependency can be created, and you can only register depencenies
        # once. But when dependencies are grabbed from a server, circular dependencies will be possible

        return wrapper  # type: ignore

    return inner
