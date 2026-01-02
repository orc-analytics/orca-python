import re
import ast
import json
from pathlib import Path

from orca_python.main import StubInfo
from orca_python.exceptions import BrokenRemoteAlgorithmStubs


class StubMetadataField:
    __orca_is_remote__ = True
    name: str
    description: str

    def __init__(self, field_name: str, stub_info: StubInfo):
        self.__name__ = field_name
        self.__annotations__ = stub_info["annotations"]
        self.__orca_metadata__ = stub_info["metadata"]
        name = stub_info["metadata"].get("Name", None)
        description = stub_info["metadata"].get("Description", None)
        if name is None or description is None:
            raise BrokenRemoteAlgorithmStubs(
                "Stubs appear broken. Regenerate with `orca sync`."
            )
        self.name = name
        self.description = description


def _load_stub_metadata(obj_name: str) -> StubInfo:
    """Load annotations and metadata from the .pyi stub file."""
    stub_file = (
        Path.cwd() / ".orca" / "orca_python" / "registry" / "metadata_fields.pyi"
    )

    if not stub_file.exists():
        return {"annotations": {}, "metadata": {}}

    try:
        content = stub_file.read_text()
        tree = ast.parse(content)

        result: StubInfo = {"annotations": {}, "metadata": {}}

        # get the annotated assignment node (e.g., asset_id: MetadataField)
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


def __getattr__(name: str) -> StubMetadataField:
    if name.startswith("_"):
        raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

    stub_info = _load_stub_metadata(name)

    return StubMetadataField(name, stub_info)
