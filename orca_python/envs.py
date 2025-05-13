import os
from typing import Tuple

from orca_python.exceptions import MissingDependency


def getenvs() -> Tuple[str, ...]:

    orcaserver = os.getenv("ORCASERVER", "")
    if orcaserver == "":
        MissingDependency("ORCASERVER is required")
    orcaserver = orcaserver.lstrip("grpc://")

    port = os.getenv("PORT", "")
    if port == "":
        MissingDependency("PORT required")

    host = os.getenv("HOST", "")
    if host == "":
        MissingDependency("HOST is required")

    return orcaserver, port, host


ORCASERVER, PORT, HOST = getenvs()
