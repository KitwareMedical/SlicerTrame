import sys
from pathlib import Path
from typing import Optional, Callable, Union

import slicer
import qt
from slicer.ScriptedLoadableModule import *
from slicer.i18n import tr as _, translate

try:
    import trame_slicer
except ImportError:
    slicer.util.delayDisplay("Installing trame-slicer")
    slicer.util.pip_install("git+https://github.com/KitwareMedical/trame-slicer.git")


class SlicerTrameServer(ScriptedLoadableModule):
    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)
        self.parent.title = _("SlicerTrameServer")
        self.parent.categories = [translate("qSlicerAbstractCoreModule", "Examples")]
        self.parent.contributors = ["Thibault Pelletier (Kitware SAS)"]
        self.parent.helpText = _("")
        self.parent.acknowledgementText = _("")


class Widget(qt.QWidget):
    def __init__(self, verbose=False, parent=None):
        super().__init__(parent)

        layout = qt.QFormLayout(self)
        self.serverPathLineEdit = qt.QLineEdit(self)
        self.serverPathLineEdit.toolTip = _(
            "Path to the Slicer trame server entry point."
        )
        layout.addRow("Server script path:", self.serverPathLineEdit)

        self.serverPort = qt.QSpinBox(self)
        self.serverPort.value = 0
        self.serverPort.toolTip = _("Port where the server will be bound")
        layout.addRow("Server port:", self.serverPort)

        startButton = qt.QPushButton(_("Start Server"))
        startButton.clicked.connect(self.startServer)
        layout.addRow(startButton)

        self.currentInfoTextEdit = qt.QTextEdit(self)
        self.currentInfoTextEdit.setReadOnly(True)
        self.currentInfoTextEdit.setLineWrapMode(qt.QTextEdit.NoWrap)
        layout.addRow(self.currentInfoTextEdit)

        self.process = qt.QProcess()
        self.process.setProcessChannelMode(qt.QProcess.SeparateChannels)
        self.process.finished.connect(self._finished)

        self.process.readyReadStandardError.connect(self._onReadyReadErrorOutput)
        self.process.readyReadStandardOutput.connect(self._onReadyReadStandardOutput)

        self._verbose = verbose
        self._lastError = ""

    def startServer(self, *_):
        self.startTrameServer(self.serverPathLineEdit.text, self.serverPort.value)

    def startTrameServer(self, scriptPath: Union[Path, str], port: int):
        scriptPath = Path(scriptPath)
        if not scriptPath.is_file():
            slicer.util.errorDisplay(
                f"Server path doesn't exist : {scriptPath.as_posix()}"
            )
            return

        args = [
            "--python-script",
            scriptPath.resolve().as_posix(),
            "--port",
            port,
            "--no-main-window",
        ]
        self._startProcess(
            self._slicerPath().as_posix(),
            args,
            qt.QProcess.Unbuffered | qt.QProcess.ReadOnly,
        )

    def _onProgressInfo(self, infoMsg):
        """
        Prints progress information in module log console and in separate log dialog.
        """
        infoMsg += "\n"
        if self._verbose:
            print(infoMsg)

        self.currentInfoTextEdit.insertPlainText(infoMsg)
        self._moveTextEditToEnd(self.currentInfoTextEdit)
        slicer.app.processEvents()

    def _onErrorInfo(self, errorMsg):
        self._onProgressInfo(errorMsg)
        slicer.util.errorDisplay(errorMsg)

    @staticmethod
    def _moveTextEditToEnd(textEdit):
        textEdit.verticalScrollBar().setValue(textEdit.verticalScrollBar().maximum)

    def _startProcess(self, program, args, openMode: qt.QIODevice.OpenMode):
        self._stopProcess()
        self.process.start(program, args, openMode)

    def _stopProcess(self):
        if self.process.state() == self.process.Running:
            self._onProgressInfo("Killing process.")
            self.process.kill()

    def _onReadyReadStandardOutput(self):
        self._report(self.process.readAllStandardOutput(), self._onProgressInfo)

    def _onReadyReadErrorOutput(self):
        self._lastError = self._report(
            self.process.readAllStandardError(), self._onProgressInfo
        )

    @staticmethod
    def _report(stream: "qt.QByteArray", outSignal: Callable[[str], None]) -> str:
        info = qt.QTextCodec.codecForUtfText(stream).toUnicode(stream)
        if info:
            outSignal(info)
        return info

    def _finished(self, _):
        self._onProgressInfo("*" * 80)

    def getLastError(self) -> str:
        return self._lastError

    @classmethod
    def _slicerPath(cls) -> Path:
        return Path(slicer.app.applicationFilePath())


class SlicerTrameServerWidget(ScriptedLoadableModuleWidget):
    def __init__(self, parent=None) -> None:
        ScriptedLoadableModuleWidget.__init__(self, parent)
        self.ui: Optional[qt.QWidget] = None

    def setup(self) -> None:
        ScriptedLoadableModuleWidget.setup(self)
        self.layout.addWidget(Widget())
        self.layout.addStretch()
