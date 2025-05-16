from pathlib import Path
from typing import Optional, Callable, Union

import ctk
import qt
import slicer
from slicer.ScriptedLoadableModule import (
    ScriptedLoadableModule,
    ScriptedLoadableModuleWidget,
)
from slicer.i18n import tr as _, translate


class SlicerTrameServer(ScriptedLoadableModule):
    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)
        self.parent.title = _("SlicerTrameServer")
        self.parent.categories = [translate("qSlicerAbstractCoreModule", "Servers")]
        self.parent.contributors = ["Thibault Pelletier (Kitware SAS)"]
        self.parent.helpText = _("")
        self.parent.acknowledgementText = _("")


def resourcesPath() -> Path:
    return Path(__file__).parent / "Resources"


def iconPath(icon_name: str) -> str:
    return resourcesPath().joinpath("Icons", icon_name).as_posix()


def icon(icon_name: str) -> "qt.QIcon":
    return qt.QIcon(iconPath(icon_name))


class Widget(qt.QWidget):
    def __init__(self, verbose=False, parent=None):
        super().__init__(parent)

        self._serverPathSettingsKey = "SlicerTrameServer/ScriptPath"
        self._serverPortSettingsKey = "SlicerTrameServer/ServerPort"

        layout = qt.QFormLayout(self)
        self._serverPathLineEdit = ctk.ctkPathLineEdit(self)
        self._serverPathLineEdit.filters = ctk.ctkPathLineEdit.Files
        self._serverPathLineEdit.nameFilters = ["*.py"]
        self._serverPathLineEdit.toolTip = _("Path to the Slicer trame server entry point.")
        self._serverPathLineEdit.currentPath = self._setting(self._serverPathSettingsKey, defaultValue="")
        layout.addRow("Server script path:", self._serverPathLineEdit)

        self._serverPort = qt.QSpinBox(self)
        self._serverPort.setRange(0, 65535)
        self._serverPort.toolTip = _("Port where the server will be bound")
        self._serverPort.value = self._setting(self._serverPortSettingsKey, defaultValue=0)
        layout.addRow("Server port:", self._serverPort)

        self.startButton = qt.QPushButton(_("Start Server"))
        self.startButton.clicked.connect(self._startServer)
        self.startButton.setIcon(icon("start_icon.png"))

        self.stopButton = qt.QPushButton(_("Stop"))
        self.stopButton.setIcon(icon("stop_icon.png"))
        self.stopButton.clicked.connect(self._stopProcess)

        layout.addRow(self.startButton)
        layout.addRow(self.stopButton)

        self._currentInfoTextEdit = qt.QTextEdit(self)
        self._currentInfoTextEdit.setReadOnly(True)
        self._currentInfoTextEdit.setLineWrapMode(qt.QTextEdit.NoWrap)
        layout.addRow(self._currentInfoTextEdit)

        self._process = qt.QProcess()
        self._process.setProcessChannelMode(qt.QProcess.SeparateChannels)
        self._process.started.connect(self._onProcessStarted)
        self._process.finished.connect(self._onProcessFinished)

        self._process.readyReadStandardError.connect(self._onReadyReadErrorOutput)
        self._process.readyReadStandardOutput.connect(self._onReadyReadStandardOutput)

        self._verbose = verbose
        self._lastError = ""
        self._onProcessFinished()
        self._ensureRequirements()

    @staticmethod
    def _saveSetting(key, value):
        settings = qt.QSettings()
        settings.setValue(key, value)
        settings.sync()

    @staticmethod
    def _setting(key, defaultValue):
        try:
            return type(defaultValue)(qt.QSettings().value(key, defaultValue))
        except ValueError:
            return defaultValue

    def _startServer(self, *_):
        self.startTrameServer(self._serverPathLineEdit.currentPath, self._serverPort.value)

    def _onProcessStarted(self):
        self.startButton.setEnabled(False)
        self.stopButton.setEnabled(True)

    def _onProcessFinished(self, *_):
        self.startButton.setEnabled(True)
        self.stopButton.setEnabled(False)

    def startTrameServer(self, scriptPath: Union[Path, str], port: int):
        scriptPath = Path(scriptPath)
        if not scriptPath.is_file():
            if self._verbose:
                slicer.util.errorDisplay(f"Server path doesn't exist : {scriptPath.as_posix()}")
            return

        self._currentInfoTextEdit.clear()
        self._saveSetting(self._serverPathSettingsKey, scriptPath.as_posix())
        self._saveSetting(self._serverPortSettingsKey, port)

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

        self._currentInfoTextEdit.insertPlainText(infoMsg)
        self._moveTextEditToEnd(self._currentInfoTextEdit)
        slicer.app.processEvents()

    def _onErrorInfo(self, errorMsg):
        self._onProgressInfo(errorMsg)
        slicer.util.errorDisplay(errorMsg)

    @staticmethod
    def _moveTextEditToEnd(textEdit):
        textEdit.verticalScrollBar().setValue(textEdit.verticalScrollBar().maximum)

    def _startProcess(self, program, args, openMode: qt.QIODevice.OpenMode):
        self._stopProcess()
        self._process.start(program, args, openMode)

    def _stopProcess(self):
        if self._process.state() == self._process.Running:
            self._currentInfoTextEdit.clear()
            self._onProgressInfo("Killing process.")
            self._process.kill()

    def _onReadyReadStandardOutput(self):
        self._report(self._process.readAllStandardOutput(), self._onProgressInfo)

    def _onReadyReadErrorOutput(self):
        self._lastError = self._report(self._process.readAllStandardError(), self._onProgressInfo)

    @staticmethod
    def _report(stream: "qt.QByteArray", outSignal: Callable[[str], None]) -> str:
        info = qt.QTextCodec.codecForUtfText(stream).toUnicode(stream)
        if info:
            outSignal(info)
        return info

    def getLastError(self) -> str:
        return self._lastError

    @classmethod
    def _slicerPath(cls) -> Path:
        return Path(slicer.app.applicationFilePath())

    @staticmethod
    def _ensureRequirements():
        import importlib.util

        if importlib.util.find_spec("trame_slicer") is None:
            slicer.util.delayDisplay("Installing trame-slicer")
            slicer.util.pip_install("trame-slicer")


class SlicerTrameServerWidget(ScriptedLoadableModuleWidget):
    def __init__(self, parent=None) -> None:
        ScriptedLoadableModuleWidget.__init__(self, parent)
        self.ui: Optional[qt.QWidget] = None

    def setup(self) -> None:
        ScriptedLoadableModuleWidget.setup(self)
        self.layout.addWidget(Widget())
        self.layout.addStretch()
