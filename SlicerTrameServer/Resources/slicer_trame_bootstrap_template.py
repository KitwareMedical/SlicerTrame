"""
Slicer Trame bootstrap.

Used to configure the environment and find the Slicer dependencies prior to script execution.

Usage example:
    {{SLICER_BOOTSTRAP_COMMAND}}
"""

import argparse
import os
import sys
import pickle
from pathlib import Path
import base64
import subprocess

# Use Slicer sys PATH
slicer_sys_path: list[str] = {{SLICER_SYS_PATH}}  # noqa
sys.path = slicer_sys_path

# Load Slicer environment
slicer_os_env: bytes = {{SLICER_OS_ENV}}  # noqa

os.environ.clear()
os.environ.update(pickle.loads(base64.decodebytes(slicer_os_env)))

# Set slicer PATH
slicer_app_path: str = {{SLICER_APP_PATH}}  # noqa


def run_script(script_path: Path, script_args):
    # bootstrap path with script folder first
    sys.path.insert(0, script_path.parent.as_posix())

    # Run the script
    subprocess.run([slicer_app_path, "--no-main-window", "--python-script", script_path.as_posix()] + script_args)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Bootstrap 3D Slicer environment and runs the input server script.")
    parser.add_argument("script_path", type=str, help="Path to Slicer trame server script file.")
    args, unknown_args = parser.parse_known_args()
    run_script(Path(args.script_path).resolve(), unknown_args)
