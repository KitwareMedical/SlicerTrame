from __future__ import annotations

import base64
import json
import logging
import os
import pickle
import shutil
import sys
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
        self.parent.dependencies = []


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


def bootstrapTemplatePath() -> Path:
    return resourcesPath().joinpath("slicer_trame_bootstrap_template.py")


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
        self._trameSlicerVersionLabel = qt.QLabel(self)
        self._updateButton = qt.QPushButton()
        self._updateButton.setToolTip(_("Update trame-slicer version to latest."))
        self._updateButton.setIcon(icon("upgrade_icon.png"))
        self._updateButton.setIconSize(qt.QSize(16, 16))
        self._updateButton.clicked.connect(self._onInstallLatestTrameSlicerVersionClicked)

        buttonWidget = qt.QWidget()
        buttonLayout = qt.QHBoxLayout(buttonWidget)
        buttonLayout.setContentsMargins(0, 0, 0, 0)
        buttonLayout.addWidget(self._trameSlicerVersionLabel)
        buttonLayout.addWidget(self._updateButton, 0, qt.Qt.AlignRight)
        buttonLayout.addWidget(self._updateButton, 0, qt.Qt.AlignRight)
        layout.addRow(_("trame-slicer version:"), buttonWidget)

        self._createBootstrapButton = qt.QPushButton(_("Create bootstrap"))
        self._createBootstrapButton.setToolTip(
            _("Create a trame-slicer bootstrap python script to launch server without the Slicer main application.")
        )
        self._createBootstrapButton.clicked.connect(self._onCreateBootstrapClicked)
        layout.addRow(self._createBootstrapButton)

        self._serverPathLineEdit = ctk.ctkPathLineEdit(self)
        self._serverPathLineEdit.filters = ctk.ctkPathLineEdit.Files
        self._serverPathLineEdit.nameFilters = ["*.py"]
        self._serverPathLineEdit.toolTip = _("Path to the Slicer trame server entry point.")

        layout.addRow(_("Server script path:"), self._serverPathLineEdit)

        self._serverPort = qt.QSpinBox(self)
        self._serverPort.setRange(0, 65535)
        self._serverPort.toolTip = _("Port where the server will be bound")
        self._serverPort.value = self._setting(self._serverPortSettingsKey, defaultValue=0)
        layout.addRow(_("Server port:"), self._serverPort)

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
        self._ensureVtkWebModules()
        self._updateExamplesDir()
        self._setServerPathToLastUsed()
        self._updateDisplayedVersion()

        # Make sure to stop the running process if the application is stopped
        slicer.app.aboutToQuit.connect(self._stopProcess)

    def _updateExamplesDir(self):
        self._downloadExampleFiles(srcZipFilePath(), downloadExampleDir())

    def __del__(self):
        # Stop the process when stopping the widget
        self._stopProcess()

    def _updateDisplayedVersion(self):
        latest = self._getLatestTrameSlicerVersion()
        latestString = f" (latest: {latest})" if latest else ""

        self._trameSlicerVersionLabel.text = f"{trame_slicer_version()}{latestString}"

    def _onInstallLatestTrameSlicerVersionClicked(self, *_args):
        # Upgrade slicer version
        self._updateTrameSlicerInstall()

        # Update displayed version
        self._updateDisplayedVersion()

        # Update examples
        self._updateExamplesDir()

    def _setServerPathToLastUsed(self):
        """
        Set the path edit to the last path used.
        If the last path is invalid, default example path will be used.
        """
        defaultPath = medicalExamplePath().resolve().as_posix()
        lastPath = self._setting(self._serverPathSettingsKey, defaultPath)
        if not Path(lastPath).is_file():
            lastPath = defaultPath
        self.setServerPath(lastPath)

    def setServerPath(self, path: str | Path):
        self._serverPathLineEdit.currentPath = Path(path).as_posix()

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

    @classmethod
    def _ensureRequirements(cls):
        import importlib.util

        if importlib.util.find_spec("trame_slicer") is None:
            cls._updateTrameSlicerInstall()

    @staticmethod
    def _updateTrameSlicerInstall():
        dialog = slicer.util.createProgressDialog(parent=None, maximum=0, labelText="Installing dependencies...")
        dialog.setCancelButton(None)
        dialog.show()
        slicer.app.processEvents()

        _error_msg = "Failed to install the python dependencies. Please check the python console for more information."
        with slicer.util.tryWithErrorDisplay(_error_msg):
            slicer.util.pip_install("--upgrade trame-slicer")

        dialog.hide()
        dialog.deleteLater()

    @staticmethod
    def _ensureVtkWebModules():
        """
        VTK modules PYD files are not properly packaged in the python environment.
        To be discovered, the files need to be copied from the extensions vtk modules folder to the application folder.
        """

        # Early return if built modules are already in vtk modules package
        try:
            from vtkmodules import vtkWebCore, vtkWebGLExporter  # noqa

            return
        except ImportError:
            pass

        # Find location of vtkmodules in the Slicer environment
        import vtkmodules

        vtkModulesPath = Path(vtkmodules.__file__).parent

        # From the current folder, find the root of the extension files.
        # File structure is organized as :
        # Extensions-<...>/SlicerTrame/
        #  ├───bin
        #  │   └───Python
        #  │       └───vtkmodules
        #  ├───lib
        #  │   └───Slicer-5.9
        #  │       └───qt-scripted-modules
        #  │           └───<SCRIPTED_MODULE_NAME>.py
        currentFolder = Path(__file__).parent
        paths = currentFolder.as_posix().split("/")
        i_path = None
        for i in reversed(range(len(paths))):
            if "lib" in paths[i]:
                i_path = i
                break

        # Early return if module is not running in an extension folder.
        if i_path is None:
            _warn_msg = "VTK web core modules are not correctly installed."
            logging.warning(_warn_msg)
            return

        extensionModulePath = Path("/".join(paths[:i_path])) / "bin" / "Python" / "vtkmodules"
        extensionModules = extensionModulePath.rglob("*.*")

        try:
            for pydFile in extensionModules:
                shutil.copyfile(pydFile, vtkModulesPath / pydFile.name)
        except OSError as e:
            _warn_msg = f"Failed to copy vtk modules file to destination folder : {e}"
            logging.warning(_warn_msg)

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
    def _getLatestTrameSlicerVersion(cls) -> str | None:
        import requests

        url = "https://api.github.com/repos/KitwareMedical/trame-slicer/tags"
        response = requests.get(url)
        if response.status_code != 200:
            _warn_msg = "Failed to check for updates"
            logging.warning(_warn_msg)
            return None

        tags = response.json()
        return tags[0]["name"] if tags else None

    @classmethod
    def _downloadExampleFiles(cls, zipPath: Path, destDir: Path) -> None:
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

    def _onCreateBootstrapClicked(self, *_args):
        destPath = qt.QFileDialog.getSaveFileName(
            self,
            _("Select path to the Slicer trame bootstrap file"),
            _("slicer_trame_bootstrap.py"),
            _("Python Files (*.py)"),
        )
        if not destPath:
            return

        printableCommand = self._printableCommand(self._getCurrentBootstrappedCommand(destPath))
        self.createBootstrapFile(destPath, printableCommand)
        _infoMsg = f"Bootstrap was created. To use the bootstrap, execute the following command:\n\n{printableCommand}"
        slicer.util.infoDisplay(_infoMsg)

    @staticmethod
    def _printableCommand(cmdArgs: list[str]):
        return " ".join([f'"{cmd}"' if i_cmd < 3 else cmd for i_cmd, cmd in enumerate(cmdArgs)])

    def _getCurrentBootstrappedCommand(self, destPath: str | Path) -> list[str]:
        return [
            *self.createBootstrapCommandArgs(destPath),
            self._serverPathLineEdit.currentPath,
            "--port",
            str(self._serverPort.value),
        ]

    @classmethod
    def createBootstrapFile(cls, destFilePath: str | Path, printableCommand: str) -> None:
        destFilePath = Path(destFilePath)
        templateContent = bootstrapTemplatePath().read_text()
        templateContent = templateContent.replace("{{SLICER_SYS_PATH}}", json.dumps(sys.path))
        templateContent = templateContent.replace(
            "{{SLICER_OS_ENV}}", str(base64.encodebytes(pickle.dumps(dict(os.environ))))
        )
        templateContent = templateContent.replace("{{SLICER_BOOTSTRAP_COMMAND}}", printableCommand)
        templateContent = templateContent.replace("{{SLICER_APP_PATH}}", json.dumps(cls._slicerPath().as_posix()))
        destFilePath.write_text(templateContent)

    @classmethod
    def createBootstrapCommandArgs(cls, bootStrapFilePath: str | Path) -> list[str]:
        bootStrapFilePath = Path(bootStrapFilePath)
        return [Path(sys.executable).as_posix(), bootStrapFilePath.as_posix()]


class SlicerTrameServerWidget(ScriptedLoadableModuleWidget):
    def __init__(self, parent=None) -> None:
        ScriptedLoadableModuleWidget.__init__(self, parent)
        self.ui: Optional[qt.QWidget] = None

    def setup(self) -> None:
        ScriptedLoadableModuleWidget.setup(self)
        self.layout.addWidget(Widget())
        self.layout.addStretch()
