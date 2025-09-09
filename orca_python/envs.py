import os
from typing import Tuple

from orca_python.exceptions import MissingDependency


def getenvs() -> Tuple[str, ...]:
    orcaserver = os.getenv("ORCA_CORE", "")
    if orcaserver == "":
        raise MissingDependency("ORCA_CORE is required")
    orcaserver = orcaserver.lstrip("grpc://")

    port = os.getenv("PROCESSOR_PORT", "")
    if port == "":
        raise MissingDependency("PROCESSOR_PORT required")

    host = os.getenv("PROCESSOR_ADDRESS", "")
    if host == "":
        raise MissingDependency("PROCESSOR_ADDRESS is required")

    return orcaserver, port, host


ORCASERVER, PORT, HOST = getenvs()
