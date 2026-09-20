import os
import json
import slicer
from slicer.ScriptedLoadableModule import *
from slicer.util import VTKObservationMixin

class LumbarRadiography(ScriptedLoadableModule):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent.title = "ONeSpineRx Lumbar Radiography"
        self.parent.categories = ["ONeSpineRx"]
        self.parent.contributors = ["ONeSpineRx"]
        self.parent.helpText = "Manual landmark-based, reproducible lumbar radiographic measurements."
        self.parent.acknowledgementText = "Research software. Measurements require clinical verification."

class LumbarRadiographyWidget(ScriptedLoadableModuleWidget, VTKObservationMixin):
    def __init__(self, parent=None):
        ScriptedLoadableModuleWidget.__init__(self, parent)
        VTKObservationMixin.__init__(self)

    def setup(self):
        ScriptedLoadableModuleWidget.setup(self)
        self.layout.addWidget(slicer.util.createProgressDialog(labelText="ONeSpineRx initialized", maximum=1))
        self.layout.addStretch(1)

class LumbarRadiographyLogic(ScriptedLoadableModuleLogic):
    DEFINITION_VERSION = "1.0.0"

    def createLandmarkNode(self, name):
        node = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLMarkupsFiducialNode", name)
        node.SetDescription("ONeSpineRx manual anatomical landmarks")
        return node

    def saveMarkups(self, node, filePath):
        if node is None:
            raise ValueError("Markup node is required")
        if not slicer.util.saveNode(node, filePath):
            raise RuntimeError(f"Unable to save markups: {filePath}")
        return filePath

    def exportManifest(self, filePath, study):
        payload = {
            "schema_version": "1.0.0",
            "measurement_definition_version": self.DEFINITION_VERSION,
            "study": study,
            "slicer_version": slicer.app.applicationVersion,
        }
        with open(filePath, "w", encoding="utf-8") as stream:
            json.dump(payload, stream, indent=2, ensure_ascii=False)
        return filePath
