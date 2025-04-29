import os
from typing import Tuple

from orca_python.exceptions import MissingDependency


def getenvs() -> Tuple[str, str]:
    orcaserver = os.getenv("ORCASERVER", "")
    if orcaserver == "":
        MissingDependency("ORCASERVER is required")
    port = os.getenv("PORT", "")
    if port == "":
        MissingDependency("PORT required")
    return orcaserver, port


ORCASERVER, PORT = getenvs()
ORCASERVER = "dns:///localhost:3335"
