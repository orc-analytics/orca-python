import os
from pathlib import Path


def ensure_orca_link():
    # This assumes the user runs the script from their project root
    project_orca = Path.cwd() / ".orca"

    # 2. Locate where your package wants the symlink to be
    package_link = Path(__file__).parent / "orca_link"

    if project_orca.exists() and project_orca.is_dir():
        if not package_link.exists():
            try:
                os.symlink(project_orca, package_link)
                print(f"Linked {project_orca} to {package_link}")
            except OSError as e:
                print(f"Could not create symlink: {e}")
    else:
        # Handle the case where the folder is missing
        pass
