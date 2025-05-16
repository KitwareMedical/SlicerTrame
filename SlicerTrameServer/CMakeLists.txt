#-----------------------------------------------------------------------------
set(MODULE_NAME SlicerTrameServer)

#-----------------------------------------------------------------------------
set(MODULE_PYTHON_SCRIPTS
  ${MODULE_NAME}.py
  tests/__init__.py
  tests/test_slicer_trame_server.py
  )

set(MODULE_PYTHON_RESOURCES
  Resources/Icons/SlicerTrameServer.png
  Resources/Icons/start_icon.png
  Resources/Icons/stop_icon.png
  Resources/Examples/minimal_trame_slicer_app.py
  )

#-----------------------------------------------------------------------------
slicerMacroBuildScriptedModule(
  NAME ${MODULE_NAME}
  SCRIPTS ${MODULE_PYTHON_SCRIPTS}
  RESOURCES ${MODULE_PYTHON_RESOURCES}
  WITH_GENERIC_TESTS
  )

#-----------------------------------------------------------------------------
if(BUILD_TESTING)
  # Register the unittest subclass in the main script as a ctest.
  # Note that the test will also be available at runtime.
  slicer_add_python_unittest(SCRIPT ${MODULE_NAME}.py)
endif()
