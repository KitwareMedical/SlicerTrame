import time

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
