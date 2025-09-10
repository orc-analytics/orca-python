import os
from typing import Tuple

from orca_python.exceptions import MissingDependency


def getenvs() -> Tuple[bool, str, str, str]:
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

    env = os.getenv("ENV", "")
    if env == "production":
        is_production = True
    else:
        is_production = False

    return is_production, orcaserver, port, host


is_production, ORCASERVER, PORT, HOST = getenvs()
