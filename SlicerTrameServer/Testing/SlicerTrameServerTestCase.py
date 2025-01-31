import unittest
from pathlib import Path
import qt
import time
import slicer

from SlicerTrameServer import Widget


class SlicerTrameServerTestCase(unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.maxDiff = None

    def test_can_show_widget(self):
        widget = Widget()
        widget.show()

    def test_can_launch_slicer_trame_example(self):
        widget = Widget()
        widget.startTrameServer(
            Path(__file__).parent.joinpath("minimal_trame_slicer_app.py").as_posix(),
            port=0,
        )

        start = time.time()

        while (time.time() - start) < 10:
            slicer.app.processEvents(qt.QEventLoop.AllEvents, 100)

        self.assertEqual(widget.getLastError(), "")
