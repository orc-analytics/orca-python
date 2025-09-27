import os
import re
from typing import Tuple, Optional

from orca_python.exceptions import BadEnvVar, MissingEnvVar


def _parse_connection_string(connection_string: str) -> Optional[Tuple[str, int]]:
    """
    Parse a connection string of the form 'address:port'.
    """
    # check for leading/trailing whitespace
    if connection_string != connection_string.strip():
        return None

    # use regex to find the port at the end
    port_pattern = r":(\d+)$"
    match = re.search(port_pattern, connection_string)

    if not match:
        return None

    # extract port
    port = int(match.group(1))

    # get address by removing the port part
    address = connection_string[: match.start()]

    # valdate that address is not empty
    if not address:
        return None

    return (address, port)


def getenvs() -> Tuple[bool, str, str, str]:
    orca_core = os.getenv("ORCA_CORE", "")
    if orca_core == "":
        raise MissingEnvVar("ORCA_CORE is required")
    orca_core = orca_core.lstrip("grpc://")

    proc_address = os.getenv("PROCESSOR_ADDRESS", "")
    if proc_address == "":
        raise MissingEnvVar("PROCESSOR_ADDRESS is required")

    res = _parse_connection_string(proc_address)
    if res is None:
        raise BadEnvVar(
            "PROCESSOR_ADDRESS is not a valid address of the form <ip>:<port>"
        )
    processor_address, processor_port = res

    env = os.getenv("ENV", "")
    if env == "production":
        is_production = True
    else:
        is_production = False

    return is_production, orca_core, processor_address, processor_port


is_production, ORCA_CORE, PROCESSOR_HOST, PROCESSOR_PORT = getenvs()
