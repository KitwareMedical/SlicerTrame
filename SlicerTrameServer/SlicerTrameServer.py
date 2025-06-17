from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional, Callable, Union

import ctk
import qt
import requests
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


def exampleDir() -> Path:
    return resourcesPath().joinpath("Examples")


def downloadExampleDir() -> Path:
    return resourcesPath().joinpath("downloaded_examples") / trame_slicer_version()


def medicalExamplePath() -> Path:
    return downloadExampleDir() / "medical_viewer_app.py"


def minimalExamplePath() -> Path:
    return exampleDir().joinpath("minimal_trame_slicer_app.py")


def trame_slicer_version() -> str:
    try:
        import trame_slicer

        return f"v{trame_slicer.__version__}"
    except ImportError:
        return ""


def srcZipFilePath() -> Path:
    return downloadExampleDir() / f"trame_slicer_{trame_slicer_version()}.zip"


def defaultExamplePath() -> Path:
    if medicalExamplePath().exists():
        return medicalExamplePath()
    return minimalExamplePath()


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
        self.downloadExampleFiles(srcZipFilePath(), downloadExampleDir())
        self._setServerPathToLastUsed()

    def _setServerPathToLastUsed(self):
        """
        Set the path edit to the last path used.
        If the last path is invalid, default example path will be used.
        """
        defaultPath = medicalExamplePath().resolve().as_posix()
        lastPath = self._setting(self._serverPathSettingsKey, defaultPath)
        if not Path(lastPath).is_file():
            lastPath = defaultPath

        self._serverPathLineEdit.currentPath = lastPath

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
            dialog = slicer.util.createProgressDialog(parent=None, maximum=0, labelText="Installing dependencies...")
            dialog.setCancelButton(None)
            dialog.show()
            slicer.app.processEvents()

            _error_msg = (
                "Failed to install the python dependencies. Please check the python console for more information."
            )
            with slicer.util.tryWithErrorDisplay(_error_msg):
                slicer.util.pip_install("trame-slicer")

            dialog.hide()
            dialog.deleteLater()

    @staticmethod
    def _downloadSrcZip(destPath: Path) -> bool:
        url = f"https://github.com/KitwareMedical/trame-slicer/archive/refs/tags/{trame_slicer_version()}.zip"

        response = requests.get(url, stream=True)
        if response.status_code != 200:
            _warn_msg = f"Failed to download zip file from {url}."
            logging.warning(_warn_msg)
            return False

        destPath.parent.mkdir(exist_ok=True, parents=True)
        with open(destPath, "wb") as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
        return True

    @classmethod
    def downloadExampleFiles(cls, zipPath: Path, destDir: Path) -> None:
        """
        Download the current trame-slicer examples present on the GitHub server to the Resources/downloaded_examples
        folder.
        """
        import zipfile

        # sources already downloaded and extracted
        if zipPath.exists():
            return

        if not cls._downloadSrcZip(zipPath):
            return

        examplesPath = "examples/"
        with zipfile.ZipFile(zipPath, "r") as zip_ref:
            for fileZipName in zip_ref.namelist():
                if fileZipName.endswith("/") or examplesPath not in fileZipName:
                    continue

                fileName = fileZipName.split(examplesPath)[-1]
                filePath = destDir / fileName
                filePath.parent.mkdir(parents=True, exist_ok=True)
                filePath.write_bytes(zip_ref.read(fileZipName))


class SlicerTrameServerWidget(ScriptedLoadableModuleWidget):
    def __init__(self, parent=None) -> None:
        ScriptedLoadableModuleWidget.__init__(self, parent)
        self.ui: Optional[qt.QWidget] = None

    def setup(self) -> None:
        ScriptedLoadableModuleWidget.setup(self)
        self.layout.addWidget(Widget())
        self.layout.addStretch()
