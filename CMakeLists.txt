cmake_minimum_required(VERSION 3.16.3...3.19.7 FATAL_ERROR)

project(SlicerTrame)

#-----------------------------------------------------------------------------
# Extension meta-information
set(EXTENSION_HOMEPAGE "https://www.slicer.org/wiki/Documentation/Nightly/Extensions/SlicerTrame")
set(EXTENSION_CATEGORY "Servers")
set(EXTENSION_CONTRIBUTORS "Thibault Pelletier (Kitware SAS)")
set(EXTENSION_DESCRIPTION "SlicerTrame is the 3D Slicer extension that regroups the different modules allowing the usage of the trame-slicer library in the 3D Slicer ecosystem")
set(EXTENSION_ICONURL "https://github.com/KitwareMedical/SlicerTrame/raw/main/SlicerTrame.png")
set(EXTENSION_SCREENSHOTURLS "https://github.com/KitwareMedical/trame-slicer/raw/main/docs/trame-slicer-medical-app-example.png")
set(EXTENSION_DEPENDS "NA") # Specified as a list or "NA" if no dependencies

#-----------------------------------------------------------------------------
set(EXTENSION_BUILD_SUBDIRECTORY inner-build)
set(SUPERBUILD_TOPLEVEL_PROJECT inner)

#-----------------------------------------------------------------------------
# Extension dependencies
find_package(Slicer REQUIRED)
include(${Slicer_USE_FILE})
mark_as_superbuild(Slicer_DIR)

find_package(Git REQUIRED)
mark_as_superbuild(GIT_EXECUTABLE)

#-----------------------------------------------------------------------------
# SuperBuild setup
option(${EXTENSION_NAME}_SUPERBUILD "Build ${EXTENSION_NAME} and the projects it depends on." ON)
mark_as_advanced(${EXTENSION_NAME}_SUPERBUILD)
if(${EXTENSION_NAME}_SUPERBUILD)
  include("${CMAKE_CURRENT_SOURCE_DIR}/SuperBuildPrerequisites.cmake")
  include("${CMAKE_CURRENT_SOURCE_DIR}/SuperBuild.cmake")
  return()
endif()

#-----------------------------------------------------------------------------
# Extension modules
add_subdirectory(SlicerTrameServer)
## NEXT_MODULE

#-----------------------------------------------------------------------------
set(SlicerTrame_CUSTOM_CONFIG "####### Expanded from \@SlicerTrame_CUSTOM_CONFIG\@ #######

set(vtkWebCore_DIR \"${vtkWebCore_DIR}\")
find_package(vtkWebCore REQUIRED)

set(vtkWebGLExporter_DIR \"${vtkWebGLExporter_DIR}\")
find_package(vtkWebGLExporter REQUIRED)

##################################################
")
include(${Slicer_EXTENSION_GENERATE_CONFIG})

#-----------------------------------------------------------------------------
set(EXTENSION_CPACK_INSTALL_CMAKE_PROJECTS)

# vtkWebCore
list(APPEND EXTENSION_CPACK_INSTALL_CMAKE_PROJECTS "${vtkWebCore_DIR};vtkWebCore;;runtime;/")
if(Slicer_USE_PYTHONQT)
  list(APPEND EXTENSION_CPACK_INSTALL_CMAKE_PROJECTS "${vtkWebCore_DIR};vtkWebCore;python;/")
endif()

# vtkWebGLExporter
list(APPEND EXTENSION_CPACK_INSTALL_CMAKE_PROJECTS "${vtkWebGLExporter_DIR};vtkWebGLExporter;;runtime;/")
if(Slicer_USE_PYTHONQT)
  list(APPEND EXTENSION_CPACK_INSTALL_CMAKE_PROJECTS "${vtkWebGLExporter_DIR};vtkWebGLExporter;python;/")
endif()


set(${EXTENSION_NAME}_CPACK_INSTALL_CMAKE_PROJECTS "${EXTENSION_CPACK_INSTALL_CMAKE_PROJECTS}" CACHE STRING "List of external projects to install" FORCE)

#-----------------------------------------------------------------------------
list(APPEND CPACK_INSTALL_CMAKE_PROJECTS "${CMAKE_BINARY_DIR};${EXTENSION_NAME};ALL;/")
list(APPEND CPACK_INSTALL_CMAKE_PROJECTS "${${EXTENSION_NAME}_CPACK_INSTALL_CMAKE_PROJECTS}")
include(${Slicer_EXTENSION_CPACK})
