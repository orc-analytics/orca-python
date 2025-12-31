import os
import re
import json
from typing import Tuple, Optional
from logging import getLogger
from pathlib import Path
from dataclasses import dataclass

from orca_python.exceptions import BadEnvVar, BadConfigFile, MissingEnvVar

LOGGER = getLogger(__name__)


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


@dataclass
class ConfigData:
    projectName: str
    orcaConnectionString: str
    processorPort: int
    processorConnectionString: str


def parseConfigFile() -> Tuple[bool, str, str, int, int]:
    currentDir = Path.cwd()
    configFile = currentDir / "orca.json"
    hasConfig = False

    if configFile.exists():
        hasConfig = True
        try:
            with open(configFile, "r") as f:
                configData = ConfigData(**json.load(f))
        except Exception as e:
            LOGGER.error(f"Could not parse config file: {e}")
            raise BadConfigFile(f"Could not parse config file: {e}")
    else:
        return (False, "", "", 0, 0)

    res = _parse_connection_string(configData.processorConnectionString)
    if res is None:
        raise BadConfigFile(
            "processorConnectionString is not a valid address of the form <ip>:<port>"
        )
    processor_address, processor_port = res

    return (
        hasConfig,
        configData.orcaConnectionString,
        processor_address,
        processor_port,
        configData.processorPort,
    )


def getenvs(strict: bool = False) -> Tuple[bool, str, str, int | None, int | None]:
    orca_core = os.getenv("ORCA_CORE", "")
    if strict and orca_core == "":
        raise MissingEnvVar("ORCA_CORE is required")
    orca_core = orca_core.lstrip("grpc://")

    proc_address = os.getenv("PROCESSOR_ADDRESS", "")
    if strict and proc_address == "":
        raise MissingEnvVar("PROCESSOR_ADDRESS is required")

    processor_address = ""
    processor_port = None
    if proc_address != "":
        res = _parse_connection_string(proc_address)
        if res is None:
            raise BadEnvVar(
                "PROCESSOR_ADDRESS is not a valid address of the form <ip>:<port>"
            )
        processor_address, processor_port = res

    _processor_external_port = os.getenv("PROCESSOR_EXTERNAL_PORT", "")
    if strict and _processor_external_port != "":
        if not _processor_external_port.isdigit():
            raise BadEnvVar("PROCESSOR_EXTERNAL_PORT is not a valid number")
        processor_external_port = int(_processor_external_port)
    elif _processor_external_port == "":
        processor_external_port = None
    else:
        processor_external_port = processor_port

    env = os.getenv("ENV", "")
    if env == "production":
        is_production = True
    else:
        is_production = False

    return (
        is_production,
        orca_core,
        processor_address,
        processor_port,
        processor_external_port,
    )


# config file takes priority. Env vars can overwrite. And if config file not
# present, all the env vars have to be there.
hasConfig, ORCA_CORE, PROCESSOR_HOST, PROCESSOR_PORT, PROCESSOR_EXTERNAL_PORT = (
    parseConfigFile()
)
if hasConfig:
    (
        is_production,
        _ORCA_CORE,
        _PROCESSOR_HOST,
        _PROCESSOR_PORT,
        _PROCESSOR_EXTERNAL_PORT,
    ) = getenvs()
    if _ORCA_CORE != '':
        ORCA_CORE= ORCA_CORE
    if _PROCESSOR_HOST != '':
        PROCESSOR_HOST = _PROCESSOR_HOST
    if _PROCESSOR_PORT is not None:
        PROCESSOR_PORT = _PROCESSOR_PORT
    if _PROCESSOR_EXTERNAL_PORT is not None:
        PROCESSOR_EXTERNAL_PORT = _PROCESSOR_EXTERNAL_PORT
else:
    (
        is_production,
        ORCA_CORE,
        PROCESSOR_HOST,
        PROCESSOR_PORT,
        PROCESSOR_EXTERNAL_PORT,
    ) = getenvs(strict=True)
