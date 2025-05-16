## SlicerTrame

![SlicerTrame](https://github.com/KitwareMedical/SlicerTrame/raw/main/SlicerTrame.png)

![SlicerTrame Medical App Example](https://github.com/KitwareMedical/trame-slicer/raw/main/docs/trame-slicer-medical-app-example.png)

SlicerTrame is the 3D Slicer extension that regroups the different modules
allowing the usage of the trame-slicer library in the 3D Slicer ecosystem.

## Compiling

This extension, and trame-slicer, require VTK 9.4+ and vtkWebCore (packaged with
3D Slicer 5.9+). It relies on a SuperBuild and the VTKExternalModule library to
compile and install the required missing VTK modules for SlicerTrame.

## SlicerTrameServer

The `SlicerTrameServer` module is a scripted module designed to integrate 3D
Slicer with Trame, a modern web framework for building interactive web
applications.

This module allows users to start and manage a Trame server directly from within
3D Slicer.

### Key Features

1. **User Interface**: Provides a simple graphical interface for configuring and
   managing the Trame server.
2. **Server Configuration**:
   - Path to the Trame server entry point.
   - Port number on which the server will run.
3. **Server Management**:
   - Start/Stop functionality to manage the Trame server process.
   - Real-time logging of server output and errors.

### Usage

![Usage example](https://github.com/KitwareMedical/SlicerTrame/raw/main/Screenshots/1.png)

To use this module in 3D Slicer:

1. Load the module into the Slicer application.
2. Configure the server script path and port number.
   - A minimal example script can be found in
     [this extension resources files.](https://github.com/KitwareMedical/SlicerTrame/blob/main/SlicerTrameServer/Resources/Examples/minimal_trame_slicer_app.py)
   - A more complete medical example is available in
     [trame-slicer examples.](https://github.com/KitwareMedical/trame-slicer/blob/main/examples/medical_viewer_app.py)
3. Click the "Start Server" button to start the Trame server.
4. Use the graphical interface to manage the server's lifecycle.

For more advanced trame-slicer usages, refer to the documentation for
[trame_slicer](https://github.com/KitwareMedical/trame-slicer) and 3D Slicer's
Python API.

## Design driving use cases

**Launching a standalone trame-slicer process using 3D Slicer's Python
executable**

- Run a trame-slicer server without having to install the dependencies manually
- Use all the features wrapped in Python by Slicer and not just the ones
  available in the wheels
- Debug from 3D Slicer the compatibility of existing / new extensions with
  trame-slicer
- Compatible with 3D Slicer customization and early deployment solutions

**Launching a trame-slicer process connected to 3D Slicer's Scene**

- Allows collaborative views / interaction with the same Slicer scene on the web
- Could allow integrating Web rendered views in 3D Slicer's layout using
  QWebEngine components

**Launching a trame-slicer process connected to 3D Slicer rendering**

- Allows 3D Slicer view mirroring and interaction on light devices (for instance
  for IGT)

## License

This extension is distributed with a permissive license. Please look at the
[LICENSE](https://github.com/KitwareMedical/SlicerTrame/blob/main/LICENSE.txt)
file for more information.

## Acknowledgment

This module was funded by the following projects :

- [Cure Overgrowth Syndromes (COSY) RHU Project](https://rhu-cosy.com/en/accueil-english/).

## Contact

If you are interested in learning how you can use SlicerTrame for your use case
in the near future, or want to get an early start using the framework, don\'t
hesitate to [contact us](https://www.kitware.eu/contact/). Or reach out in the
[issue tracker](https://github.com/KitwareMedical/SlicerTrame/issues) and
[3DSlicer discourse community](https://discourse.slicer.org/).
