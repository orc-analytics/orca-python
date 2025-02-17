import re
from typing import Any, Dict, List, Callable

SingletonAlgorithms: Dict[str, List[Callable[..., Any]] | None] = dict()

# Regex patterns for validation
ALGORITHM_NAME = r"^[A-Z][a-zA-Z0-9]*$"
SEMVER_PATTERN = r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$"

# need a global state to track the algorithms
def algorithm(name: str, version: str, depends_on: List[Callable[..., Any]] | None = None) -> Callable[..., Any]:
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
    compound_algorithm_name = f"{name}_{version}"
    
    if compound_algorithm_name in SingletonAlgorithms:
        raise ValueError(f"Algorithm `{algorithm}` of version `{version}` is already registered")

    SingletonAlgorithms[compound_algorithm_name] = depends_on

    def inner(func):
        return func

    return inner
