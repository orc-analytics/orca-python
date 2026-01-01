import re
import ast
import json
from typing import Any
from pathlib import Path


def _load_stub_metadata(func_name: str) -> dict[str, Any]:
    """Load annotations and metadata from the .pyi stub file."""
    stub_file = Path.cwd() / ".orca" / "orca_python" / "registry" / "algorithms.pyi"

    if not stub_file.exists():
        return {"annotations": {}, "metadata": {}}

    try:
        content = stub_file.read_text()
        tree = ast.parse(content)

        result = {"annotations": {}, "metadata": {}}

        # get the function node
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == func_name:
                # get annotations
                annotations = {}
                for arg in node.args.args:
                    if arg.annotation:
                        annotations[arg.arg] = ast.unparse(arg.annotation)
                if node.returns:
                    annotations["return"] = ast.unparse(node.returns)
                result["annotations"] = annotations

                # get metadata from comment above function
                # find the line number and look for comment above it
                lines = content.split("\n")
                func_line = node.lineno - 1  # 0-indexed

                # look at previous lines for metadata comment
                for i in range(func_line - 1, max(0, func_line - 5), -1):
                    line = lines[i].strip()
                    if match := re.search(r"#\s*METADATA:\s*(\{.*\})", line):
                        result["metadata"] = json.loads(match.group(1))
                        break

                break

        return result
    except Exception as e:
        print(f"Error parsing stub: {e}")

    return {"annotations": {}, "metadata": {}}


def __getattr__(name):
    if name.startswith("_"):
        raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

    stub_info = _load_stub_metadata(name)

    class StubAlgorithm:
        __orca_is_remote__ = True

        def __init__(self, func_name: str):
            self.__name__ = func_name
            self.__annotations__ = stub_info["annotations"]
            self.__orca_metadata__ = stub_info["metadata"]

        def __call__(self, *args, **kwargs):
            _, _ = args, kwargs
            raise NotImplementedError(
                f"{self.__name__} is only available as a remote algorithm. "
                f"Metadata: {self.__orca_metadata__}"
            )

    return StubAlgorithm(name)
