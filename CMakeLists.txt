cmake_minimum_required(VERSION 3.16.3...3.19.7 FATAL_ERROR)

project(ONeSpineRx)

find_package(Slicer REQUIRED)
include(${Slicer_USE_FILE})

slicerMacroBuildScriptedModule(
  NAME LumbarRadiography
  SCRIPTS ONeSpineRx/LumbarRadiography/LumbarRadiography.py
  RESOURCES
    ONeSpineRx/LumbarRadiography/Resources/Definitions/landmarks.json
    ONeSpineRx/LumbarRadiography/Resources/Definitions/measurements.json
  WITH_GENERIC_TESTS
)
