============
SlicerTrame
============

.. image:: https://raw.githubusercontent.com/KitwareMedical/trame-slicer/main/docs/trame-slicer-medical-app-example.png
  :alt: Welcome to SlicerTrame

SlicerTrame is the 3D Slicer extension which regroups the different modules allowing the usage of the trame-slicer 
library in the 3D Slicer ecosystem.


Warning
-------

This repository is at a proof of concept level of readiness.
All its APIs will be changed, the maintainers will force push to the main branch as they see fit without any
forewarning.

The first user versions will be available through the extension manager and 3D Slicer's preview release mechanism.


Compiling
----------

This extension, and trame-slicer, require VTK 9.4+ and vtkWebCore (not packaged with 3D Slicer).
It relies on a SuperBuild and the VTKExternalModule library to compile and install the required missing VTK modules
for SlicerTrame.

SlicerTrameServer
-----------------

Design driving use cases
------------------------

**Launching a standalone trame-slicer process using 3D Slicer's Python executable**

* Run a trame-slicer server without having to install the dependencies manually
* Use all the features wrapped in Python by Slicer and not just the ones available in the wheels
* Debug from 3D Slicer the compatibility of existing / new extensions with trame-slicer
* Compatible with 3D Slicer customization and early deployment solutions

**Launching a trame-slicer process connected to 3D Slicer's Scene**

* Allows collaborative views / interaction with the same Slicer scene on the web
* Could allow to integrate Web rendered views in 3D Slicer's layout using QWebEngine components

**Launching a trame-slicer process connected to 3D Slicer rendering**

* Allows 3D Slicer view mirroring and interaction on light devices (for instance for IGT)
