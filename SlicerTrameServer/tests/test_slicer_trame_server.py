import os
import time
from pathlib import Path

import pytest
import qt
import slicer

from SlicerTrameServer import Widget, resourcesPath


@pytest.fixture
def a_widget():
    return Widget()


def test_can_show_widget(a_widget):
    a_widget.show()
    assert a_widget.startButton.isEnabled()
    assert not a_widget.stopButton.isEnabled()


def test_can_launch_slicer_trame_example(a_widget):
    a_widget.startTrameServer(
        resourcesPath().joinpath("Examples/minimal_trame_slicer_app.py").as_posix(),
        port=0,
    )

    start = time.time()

    while (time.time() - start) < 10:
        slicer.app.processEvents(qt.QEventLoop.AllEvents, 100)

    assert not a_widget.startButton.isEnabled()
    assert a_widget.stopButton.isEnabled()
    assert a_widget.getLastError() == ""


def test_can_download_trame_example_files(tmpdir):
    dest_dir = Path(tmpdir)
    zip_path = dest_dir / "a" / "subfolder" / "src.zip"

    Widget.downloadExampleFiles(zip_path, dest_dir)

    assert zip_path.exists()
    assert list(dest_dir.glob("*.py"))
    assert len(os.listdir(tmpdir)) > 0
