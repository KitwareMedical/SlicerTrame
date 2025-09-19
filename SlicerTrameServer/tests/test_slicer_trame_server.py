import os
import signal
import subprocess
import time
from pathlib import Path

import pytest
import qt
import slicer

from SlicerTrameServer import Widget, minimalExamplePath


@pytest.fixture
def a_widget():
    return Widget()


def test_can_show_widget(a_widget):
    a_widget.show()
    assert a_widget.startButton.isEnabled()
    assert not a_widget.stopButton.isEnabled()


def test_can_launch_slicer_trame_example(a_widget):
    a_widget.startTrameServer(
        minimalExamplePath().as_posix(),
        port=0,
    )

    start = time.time()

    while (time.time() - start) < 10:
        slicer.app.processEvents(qt.QEventLoop.AllEvents, 100)

    assert not a_widget.startButton.isEnabled()
    assert a_widget.stopButton.isEnabled()


def test_can_download_trame_example_files(tmpdir):
    dest_dir = Path(tmpdir)
    zip_path = dest_dir / "a" / "subfolder" / "src.zip"

    Widget._downloadExampleFiles(zip_path, dest_dir)

    assert zip_path.exists()
    assert list(dest_dir.glob("*.py"))
    assert len(os.listdir(tmpdir)) > 0


@pytest.fixture
def a_bootstrap(tmpdir):
    dest_file = Path(tmpdir) / "slicer_trame_bootstrap.py"

    # Create the bootstrap file
    Widget.createBootstrapFile(dest_file, "EXAMPLE_COMMAND")

    # Check that the bootstrap exists and is not empty
    assert dest_file.exists()
    assert dest_file.read_text()
    return dest_file


@pytest.fixture
def a_trame_slicer_script():
    return "import trame_slicer; import slicer; import LayerDMLib;"


def test_can_run_bootstrapped_script(a_bootstrap, tmpdir, a_trame_slicer_script):
    my_script_file = Path(tmpdir) / "my_script.py"
    my_script_file.write_text(a_trame_slicer_script)
    bootstrap_command = Widget.createBootstrapCommandArgs(a_bootstrap)
    result = subprocess.run([*bootstrap_command, my_script_file.as_posix()], capture_output=True, text=True)
    assert result.returncode == 0, f"Execution failed: {result.stderr}"


def test_can_run_bootstrapped_script_with_proposed_command(a_bootstrap, a_widget):
    a_widget.setServerPath(minimalExamplePath())
    bootstrap_command = a_widget._getCurrentBootstrappedCommand(a_bootstrap)
    proc = subprocess.Popen(bootstrap_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    try:
        start = time.time()
        while (time.time() - start) < 10:
            slicer.app.processEvents(qt.QEventLoop.AllEvents, 100)

        assert proc.poll() is None
    finally:
        os.kill(proc.pid, signal.SIGTERM)
