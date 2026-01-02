import re
import ast
import json
from typing import List
from pathlib import Path
from dataclasses import dataclass

from orca_python.main import StubInfo, BrokenRemoteAlgorithmStubs


def _load_stub_metadata(obj_name: str) -> StubInfo:
    """Load annotations and metadata from the .pyi stub file."""
    stub_file = Path.cwd() / ".orca" / "orca_python" / "registry" / "window_types.pyi"

    if not stub_file.exists():
        return StubInfo(annotations={}, metadata={})

    try:
        content = stub_file.read_text()
        tree = ast.parse(content)

        result: StubInfo = {"annotations": {}, "metadata": {}}

        # get the annotated assignment node
        for node in ast.walk(tree):
            if isinstance(node, ast.AnnAssign):
                # check if this is the target we're looking for
                if isinstance(node.target, ast.Name) and node.target.id == obj_name:
                    # get annotation
                    if node.annotation:
                        result["annotations"]["type"] = ast.unparse(node.annotation)

                    # get metadata from comment above assignment
                    lines = content.split("\n")
                    assign_line = node.lineno - 1  # 0-indexed

                    # look at previous lines for metadata comment
                    for i in range(assign_line - 1, max(0, assign_line - 5), -1):
                        line = lines[i].strip()
                        if match := re.search(r"#\s*METADATA:\s*(\{.*\})", line):
                            result["metadata"] = json.loads(match.group(1))
                            break

                    break

        return result
    except Exception as e:
        print(f"Error parsing stub: {e}")

    return StubInfo(annotations={}, metadata={})


def __getattr__(name):
    if name.startswith("_"):
        raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

    stub_info = _load_stub_metadata(name)

    @dataclass
    class StubMetadataField:
        __orca_is_remote__ = True
        name: str
        description: str

    class StubWindowType:
        __orca_is_remote__ = True
        name: str
        version: str
        description: str
        metadataFields: List[StubMetadataField]

        def __init__(self, window_name: str):
            self.__annotations__ = stub_info["annotations"]
            self.__orca_metadata__ = stub_info["metadata"]

            # assign the values that the main package expects from a window
            name = stub_info["metadata"].get("Name", None)
            version = stub_info["metadata"].get("Version", None)
            description = stub_info["metadata"].get("Description", None)
            metadataFields = stub_info["metadata"].get("MetadataFields", None)

            if (
                name is None
                or version is None
                or description is None
                or metadataFields is None
            ):
                raise BrokenRemoteAlgorithmStubs(
                    "Stubs appear broken. Regenerate them with `orca sync`."
                )

            self.name = name
            self.version = version
            self.description = description
            try:
                self.metadataFields = [
                    StubMetadataField(
                        name=v.get("Name"), description=v.get("Description")
                    )
                    for v in metadataFields
                ]
            except Exception as e:
                raise BrokenRemoteAlgorithmStubs(
                    f"Stubs appear broken: {e}. Regenerate with `orca sync`"
                )

            self.__name__ = window_name

    return StubWindowType(name)
