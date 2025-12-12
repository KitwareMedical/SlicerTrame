import os
import signal
import subprocess
import time
from pathlib import Path

import pytest

from SlicerPythonTestRunnerLib import runTestInSlicerContext
from .conftest import get_server_widget, get_bootstrap


@pytest.fixture
def trame_slicer_script():
    return "import trame_slicer; import slicer; import LayerDMLib;"


@runTestInSlicerContext()
def test_can_show_widget(request):
    widget = get_server_widget(request)
    widget.show()
    assert widget.startButton.isEnabled()
    assert not widget.stopButton.isEnabled()


@runTestInSlicerContext()
def test_can_launch_slicer_trame_example(request):
    from SlicerTrameServer import minimalExamplePath
    import slicer
    import qt

    widget = get_server_widget(request)
    widget.startTrameServer(minimalExamplePath().as_posix(), serverPort=0, serverHost="")

    start = time.time()

    while (time.time() - start) < 10:
        slicer.app.processEvents(qt.QEventLoop.AllEvents, 100)

    assert not widget.startButton.isEnabled()
    assert widget.stopButton.isEnabled()


@runTestInSlicerContext()
def test_can_download_trame_example_files(tmpdir):
    from SlicerTrameServer import Widget

    dest_dir = Path(tmpdir)
    zip_path = dest_dir / "a" / "subfolder" / "src.zip"

    Widget._downloadExampleFiles(zip_path, dest_dir)

    assert zip_path.exists()
    assert list(dest_dir.glob("*.py"))
    assert len(os.listdir(tmpdir)) > 0

    # Check that no tests are downloaded
    assert not list(dest_dir.glob("test_*.py"))


@runTestInSlicerContext()
def test_can_run_bootstrapped_script_with_proposed_command(request):
    from SlicerTrameServer import minimalExamplePath
    import slicer
    import qt

    widget = get_server_widget(request)
    bootstrap = get_bootstrap(request)

    widget.setServerPath(minimalExamplePath())
    bootstrap_command = widget._getCurrentBootstrappedCommand(bootstrap)
    proc = subprocess.Popen(bootstrap_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    try:
        start = time.time()
        while (time.time() - start) < 10:
            slicer.app.processEvents(qt.QEventLoop.AllEvents, 100)

        assert proc.poll() is None
    finally:
        os.kill(proc.pid, signal.SIGTERM)


@runTestInSlicerContext()
def test_bootstrap_command_contains_host_if_present(request):
    from SlicerTrameServer import minimalExamplePath

    widget = get_server_widget(request)
    bootstrap = get_bootstrap(request)
    widget.setServerPath(minimalExamplePath())
    widget.setServerConfig(serverPort=42, serverHost="1.2.3.4")
    bootstrap_command = widget._getCurrentBootstrappedCommand(bootstrap)
    assert "--host" in bootstrap_command
    assert "1.2.3.4" in bootstrap_command
    assert "--port" in bootstrap_command
    assert "42" in bootstrap_command


@runTestInSlicerContext()
def test_bootstrap_command_doesnt_contain_host_if_missing(request):
    from SlicerTrameServer import minimalExamplePath

    widget = get_server_widget(request)
    bootstrap = get_bootstrap(request)
    widget.setServerPath(minimalExamplePath())
    widget.setServerConfig(serverPort=42, serverHost="")
    bootstrap_command = widget._getCurrentBootstrappedCommand(bootstrap)
    assert "--host" not in bootstrap_command


@runTestInSlicerContext()
def test_bootstrap_command_contains_extra_args(request):
    from SlicerTrameServer import minimalExamplePath

    widget = get_server_widget(request)
    bootstrap = get_bootstrap(request)
    widget.setServerPath(minimalExamplePath())
    widget.setServerExtraArgs("--server")
    bootstrap_command = widget._getCurrentBootstrappedCommand(bootstrap)
    assert "--server" in bootstrap_command
