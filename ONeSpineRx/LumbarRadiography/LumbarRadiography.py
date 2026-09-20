import json
import slicer
import qt
from slicer.ScriptedLoadableModule import *
from slicer.util import VTKObservationMixin


class LumbarRadiography(ScriptedLoadableModule):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent.title = "ONeSpineRx Lumbar Radiography"
        self.parent.categories = ["ONeSpineRx"]
        self.parent.contributors = ["ONeSpineRx"]
        self.parent.helpText = (
            "Manual landmark-based lumbar radiographic measurements. "
            "The observer places anatomical landmarks; derived measurements are calculated by Python."
        )
        self.parent.acknowledgementText = "Research software. Measurements require clinical verification."


class LumbarRadiographyWidget(ScriptedLoadableModuleWidget, VTKObservationMixin):
    PROJECTIONS = ["Lateral neutral", "Flexion", "Extension", "AP"]
    LATERAL_LABELS = [
        f"{level}_{corner}"
        for level in ("L1", "L2", "L3", "L4", "L5")
        for corner in ("AS", "PS", "AI", "PI")
    ] + ["S1_AS", "S1_PS"]
    AP_LABELS = [
        f"{level}_{corner}"
        for level in ("L1", "L2", "L3", "L4", "L5")
        for corner in ("SL", "SR", "IL", "IR")
    ] + ["S1_L", "S1_R"]

    def __init__(self, parent=None):
        ScriptedLoadableModuleWidget.__init__(self, parent)
        VTKObservationMixin.__init__(self)
        self.logic = None
        self.markupNode = None
        self.nextLandmarkIndex = 0

    def setup(self):
        ScriptedLoadableModuleWidget.setup(self)
        self.logic = LumbarRadiographyLogic()

        studyBox = qt.QGroupBox("Study")
        studyLayout = qt.QFormLayout(studyBox)
        self.volumeSelector = slicer.qMRMLNodeComboBox()
        self.volumeSelector.nodeTypes = ["vtkMRMLScalarVolumeNode"]
        self.volumeSelector.noneEnabled = True
        self.volumeSelector.addEnabled = False
        self.volumeSelector.removeEnabled = False
        self.volumeSelector.setMRMLScene(slicer.mrmlScene)
        studyLayout.addRow("Radiograph:", self.volumeSelector)

        self.projectionCombo = qt.QComboBox()
        self.projectionCombo.addItems(self.PROJECTIONS)
        studyLayout.addRow("Projection:", self.projectionCombo)
        self.layout.addWidget(studyBox)

        landmarkBox = qt.QGroupBox("Manual landmarks")
        landmarkLayout = qt.QVBoxLayout(landmarkBox)
        self.statusLabel = qt.QLabel("Create a landmark set to begin.")
        self.statusLabel.wordWrap = True
        landmarkLayout.addWidget(self.statusLabel)

        self.createButton = qt.QPushButton("Create landmark set")
        self.placeButton = qt.QPushButton("Place next landmark")
        self.placeButton.enabled = False
        landmarkLayout.addWidget(self.createButton)
        landmarkLayout.addWidget(self.placeButton)
        self.layout.addWidget(landmarkBox)

        qcBox = qt.QGroupBox("Quality control")
        qcLayout = qt.QFormLayout(qcBox)
        self.countLabel = qt.QLabel("0 / 22")
        self.calibrationLabel = qt.QLabel(
            "Distances in mm require valid DICOM spacing or explicit calibration."
        )
        self.calibrationLabel.wordWrap = True
        qcLayout.addRow("Landmarks:", self.countLabel)
        qcLayout.addRow("Calibration:", self.calibrationLabel)
        self.layout.addWidget(qcBox)

        self.createButton.connect("clicked()", self.onCreateLandmarkSet)
        self.placeButton.connect("clicked()", self.onPlaceNextLandmark)
        self.projectionCombo.connect("currentIndexChanged(int)", self.onProjectionChanged)
        self.layout.addStretch(1)

    def cleanup(self):
        self.removeObservers()

    def labelsForCurrentProjection(self):
        return self.AP_LABELS if self.projectionCombo.currentText == "AP" else self.LATERAL_LABELS

    def onProjectionChanged(self, _index):
        if self.markupNode and self.markupNode.GetNumberOfControlPoints() > 0:
            self.statusLabel.text = (
                "Projection changed. Create a new landmark set; coordinates are never reused across projections."
            )

    def onCreateLandmarkSet(self):
        volume = self.volumeSelector.currentNode()
        if volume is None:
            slicer.util.errorDisplay("Select the radiograph first.")
            return
        projection = self.projectionCombo.currentText
        safeProjection = projection.replace(" ", "_").upper()
        self.markupNode = self.logic.createLandmarkNode(f"ONeSpineRx_{safeProjection}")
        self.markupNode.SetAttribute("ONeSpineRx.Projection", projection)
        self.markupNode.SetAttribute("ONeSpineRx.DefinitionVersion", self.logic.DEFINITION_VERSION)
        self.markupNode.SetAttribute("ONeSpineRx.SourceVolumeID", volume.GetID())
        self.nextLandmarkIndex = 0
        self.placeButton.enabled = True
        self.updateStatus()

    def onPlaceNextLandmark(self):
        if self.markupNode is None:
            return
        labels = self.labelsForCurrentProjection()
        if self.nextLandmarkIndex >= len(labels):
            self.statusLabel.text = "Landmark set complete. Adjust points manually if required."
            self.placeButton.enabled = False
            return
        label = labels[self.nextLandmarkIndex]
        self.markupNode.SetAttribute("ONeSpineRx.PendingLandmark", label)
        slicer.mrmlScene.SetActiveMRMLNodeID(self.markupNode.GetID())
        interactionNode = slicer.app.applicationLogic().GetInteractionNode()
        interactionNode.SetPlaceModePersistence(0)
        interactionNode.SetCurrentInteractionMode(interactionNode.Place)
        self.statusLabel.text = f"Place {label} on the radiograph, then press Place next landmark."
        self.nextLandmarkIndex += 1
        self.updateStatus()

    def updateStatus(self):
        labels = self.labelsForCurrentProjection()
        placed = self.markupNode.GetNumberOfControlPoints() if self.markupNode else 0
        self.countLabel.text = f"{placed} / {len(labels)}"
        if self.nextLandmarkIndex < len(labels):
            self.statusLabel.text = f"Next anatomical landmark: {labels[self.nextLandmarkIndex]}"
        else:
            self.statusLabel.text = "All required landmarks have been requested. Review and adjust them."


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
            raise RuntimeError("Unable to save markups: " + filePath)
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
