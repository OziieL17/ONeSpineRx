import json
import slicer
import qt
from slicer.ScriptedLoadableModule import *
from slicer.util import VTKObservationMixin

TRANSLATIONS = {
    "es": {
        "study":"Estudio radiográfico", "language":"Idioma", "ap":"AP", "lat":"Lateral neutra",
        "flex":"Flexión", "ext":"Extensión", "select":"Seleccionar volumen",
        "landmarks":"Registro manual de landmarks", "start":"Iniciar registro",
        "importDicom":"Importar DICOM", "categorize":"Categorizar", "validate":"Validar estudio",
        "validation":"Importación, categorización y validación", "assigned":"Asignada", "missing":"Faltante",
        "place":"Marcar punto", "skip":"Saltar", "finish":"Finalizar",
        "current":"Punto actual", "progress":"Progreso", "instructions":"Instrucciones",
        "noVolume":"Seleccione un volumen para esta proyección.",
        "ready":"Seleccione las cuatro proyecciones y pulse Iniciar registro en la proyección que desea medir.",
        "complete":"Registro finalizado. Revise los puntos antes de calcular o exportar.",
        "skipped":"Omitido", "calibration":"Las distancias en mm requieren calibración espacial válida.",
    },
    "en": {
        "study":"Radiographic study", "language":"Language", "ap":"AP", "lat":"Neutral lateral",
        "flex":"Flexion", "ext":"Extension", "select":"Select volume",
        "landmarks":"Manual landmark registration", "start":"Start registration",
        "importDicom":"Import DICOM", "categorize":"Categorize", "validate":"Validate study",
        "validation":"Import, categorization and validation", "assigned":"Assigned", "missing":"Missing",
        "place":"Place point", "skip":"Skip", "finish":"Finish",
        "current":"Current landmark", "progress":"Progress", "instructions":"Instructions",
        "noVolume":"Select a volume for this projection.",
        "ready":"Select all four projections and press Start registration on the projection you want to measure.",
        "complete":"Registration finished. Review landmarks before calculation or export.",
        "skipped":"Skipped", "calibration":"Distances in mm require valid spatial calibration.",
    },
}

LANDMARK_HELP = {
    "AS": {"es":"Esquina anterosuperior del cuerpo vertebral. Marque el punto donde el borde anterior se continúa con el platillo superior; use zoom si el contorno es dudoso.", "en":"Anterosuperior vertebral-body corner. Mark the junction of the anterior cortex and superior endplate; zoom when the contour is uncertain."},
    "PS": {"es":"Esquina posterosuperior. Marque la unión del borde posterior con el platillo superior.", "en":"Posterosuperior corner. Mark the junction of the posterior cortex and superior endplate."},
    "AI": {"es":"Esquina anteroinferior. Marque la unión del borde anterior con el platillo inferior.", "en":"Anteroinferior corner. Mark the junction of the anterior cortex and inferior endplate."},
    "PI": {"es":"Esquina posteroinferior. Marque la unión del borde posterior con el platillo inferior.", "en":"Posteroinferior corner. Mark the junction of the posterior cortex and inferior endplate."},
    "SL": {"es":"Extremo izquierdo del platillo superior en AP. Use el margen óseo proyectado más reproducible.", "en":"Left end of the superior endplate on AP. Use the most reproducible projected osseous margin."},
    "SR": {"es":"Extremo derecho del platillo superior en AP. Use el margen óseo proyectado más reproducible.", "en":"Right end of the superior endplate on AP. Use the most reproducible projected osseous margin."},
    "IL": {"es":"Extremo izquierdo del platillo inferior en AP.", "en":"Left end of the inferior endplate on AP."},
    "IR": {"es":"Extremo derecho del platillo inferior en AP.", "en":"Right end of the inferior endplate on AP."},
    "S1_AS": {"es":"Extremo anterior del platillo superior de S1.", "en":"Anterior end of the S1 superior endplate."},
    "S1_PS": {"es":"Extremo posterior del platillo superior de S1.", "en":"Posterior end of the S1 superior endplate."},
    "S1_L": {"es":"Extremo izquierdo del platillo superior de S1 en AP.", "en":"Left end of the S1 superior endplate on AP."},
    "S1_R": {"es":"Extremo derecho del platillo superior de S1 en AP.", "en":"Right end of the S1 superior endplate on AP."},
}


class LumbarRadiography(ScriptedLoadableModule):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent.title = "ONeSpineRx Lumbar Radiography"
        self.parent.categories = ["ONeSpineRx"]
        self.parent.contributors = ["ONeSpineRx"]
        self.parent.helpText = "Medición radiográfica lumbar reproducible mediante landmarks anatómicos manuales."
        self.parent.acknowledgementText = "Software de investigación. Verifique clínicamente las mediciones."

class LumbarRadiographyWidget(ScriptedLoadableModuleWidget, VTKObservationMixin):
    PROJECTION_KEYS = ["ap","lat","flex","ext"]
    LATERAL_LABELS = [f"{v}_{c}" for v in ("L1","L2","L3","L4","L5") for c in ("AS","PS","AI","PI")] + ["S1_AS","S1_PS"]
    AP_LABELS = [f"{v}_{c}" for v in ("L1","L2","L3","L4","L5") for c in ("SL","SR","IL","IR")] + ["S1_L","S1_R"]

    def __init__(self, parent=None):
        ScriptedLoadableModuleWidget.__init__(self,parent)
        VTKObservationMixin.__init__(self)
        self.logic=None; self.lang="es"; self.activeProjection=None
        self.markupNodes={}; self.indices={k:0 for k in self.PROJECTION_KEYS}; self.skipped={k:[] for k in self.PROJECTION_KEYS}

    def setup(self):
        ScriptedLoadableModuleWidget.setup(self); self.logic=LumbarRadiographyLogic()
        top=qt.QHBoxLayout(); self.languageCombo=qt.QComboBox(); self.languageCombo.addItem("Español","es"); self.languageCombo.addItem("English","en")
        top.addWidget(qt.QLabel("Idioma / Language:")); top.addWidget(self.languageCombo); self.layout.addLayout(top)

        self.studyBox=qt.QGroupBox(); grid=qt.QGridLayout(self.studyBox); self.selectors={}
        for row,key in enumerate(self.PROJECTION_KEYS):
            label=qt.QLabel(); selector=slicer.qMRMLNodeComboBox(); selector.nodeTypes=["vtkMRMLScalarVolumeNode"]; selector.noneEnabled=True; selector.addEnabled=False; selector.removeEnabled=False; selector.setMRMLScene(slicer.mrmlScene)
            self.selectors[key]=selector; setattr(self,key+"Label",label); grid.addWidget(label,row,0); grid.addWidget(selector,row,1)
            b=qt.QPushButton(); b.minimumWidth=110; setattr(self,key+"StartButton",b); b.connect("clicked()",lambda k=key:self.startRegistration(k)); grid.addWidget(b,row,2)
        self.layout.addWidget(self.studyBox)

        self.validationBox=qt.QGroupBox()
        validationLayout=qt.QVBoxLayout(self.validationBox)
        validationButtons=qt.QHBoxLayout()
        self.importButton=qt.QPushButton()
        self.categorizeButton=qt.QPushButton()
        self.validateButton=qt.QPushButton()
        validationButtons.addWidget(self.importButton)
        validationButtons.addWidget(self.categorizeButton)
        validationButtons.addWidget(self.validateButton)
        validationLayout.addLayout(validationButtons)
        self.validationText=qt.QLabel()
        self.validationText.wordWrap=True
        validationLayout.addWidget(self.validationText)
        self.layout.addWidget(self.validationBox)
        self.importButton.connect("clicked()",self.importDicom)
        self.categorizeButton.connect("clicked()",self.categorizeLoadedVolumes)
        self.validateButton.connect("clicked()",self.validateStudy)

        self.landmarkBox=qt.QGroupBox(); v=qt.QVBoxLayout(self.landmarkBox)
        self.currentLabel=qt.QLabel(); self.currentLabel.setStyleSheet("font-weight: bold; font-size: 16px;")
        self.helpLabel=qt.QLabel(); self.helpLabel.wordWrap=True
        self.progressLabel=qt.QLabel(); v.addWidget(self.currentLabel); v.addWidget(self.helpLabel); v.addWidget(self.progressLabel)
        buttons=qt.QHBoxLayout(); self.placeButton=qt.QPushButton(); self.skipButton=qt.QPushButton(); self.finishButton=qt.QPushButton()
        for b in (self.skipButton,self.finishButton): buttons.addWidget(b); b.enabled=False\n        self.placeButton.visible=False
        v.addLayout(buttons); self.layout.addWidget(self.landmarkBox)
        self.calibrationLabel=qt.QLabel(); self.calibrationLabel.wordWrap=True; self.layout.addWidget(self.calibrationLabel)
        self.placeButton.connect("clicked()",self.placeCurrent); self.skipButton.connect("clicked()",self.skipCurrent); self.finishButton.connect("clicked()",self.finishRegistration)
        self.languageCombo.connect("currentIndexChanged(int)",self.changeLanguage)
        self.applyLanguage(); self.layout.addStretch(1)

    def cleanup(self): self.removeObservers()

    def tr(self,key): return TRANSLATIONS[self.lang].get(key,key)
    def changeLanguage(self,_index):
        self.lang=self.languageCombo.itemData(self.languageCombo.currentIndex); self.applyLanguage(); self.updateGuide()

    def applyLanguage(self):
        self.studyBox.title=self.tr("study"); self.landmarkBox.title=self.tr("landmarks"); self.validationBox.title=self.tr("validation")
        self.importButton.text=self.tr("importDicom"); self.categorizeButton.text=self.tr("categorize"); self.validateButton.text=self.tr("validate")
        for key in self.PROJECTION_KEYS:
            getattr(self,key+"Label").text=self.tr(key)
            getattr(self,key+"StartButton").text=self.tr("start")
        self.skipButton.text=self.tr("skip"); self.finishButton.text=self.tr("finish")
        self.calibrationLabel.text=self.tr("calibration")
        if self.activeProjection is None: self.currentLabel.text=self.tr("ready"); self.helpLabel.text=""; self.progressLabel.text=""

    def labels(self,key): return self.AP_LABELS if key=="ap" else self.LATERAL_LABELS

    def importDicom(self):
        slicer.util.selectModule("DICOM")
        self.validationText.text=("Importe/cargue el estudio con el navegador DICOM de Slicer y regrese a ONeSpineRx para categorizarlo." if self.lang=="es" else "Import/load the study with Slicer's DICOM browser, then return to ONeSpineRx to categorize it.")

    def categorizeLoadedVolumes(self):
        volumes=list(slicer.util.getNodesByClass("vtkMRMLScalarVolumeNode"))
        available=[v for v in volumes if v is not None]
        rules={
            "flex":("flex","flexion","flexión"),
            "ext":("ext","extension","extensión"),
            "ap":(" ap","ap ","anteroposterior"),
            "lat":("lat","lateral"),
        }
        for key in ("flex","ext","ap","lat"):
            if self.selectors[key].currentNode() is not None:
                continue
            for volume in list(available):
                name=(" "+volume.GetName()+" ").lower()
                if any(token in name for token in rules[key]):
                    self.selectors[key].setCurrentNode(volume)
                    available.remove(volume)
                    break
        self.validateStudy()

    def validateStudy(self):
        lines=[]
        complete=True
        for key in self.PROJECTION_KEYS:
            volume=self.selectors[key].currentNode()
            if volume is None:
                lines.append("✗ "+self.tr(key)+": "+self.tr("missing"))
                complete=False
                continue
            imageData=volume.GetImageData()
            dims=imageData.GetDimensions() if imageData else (0,0,0)
            spacing=volume.GetSpacing()
            spacingValid=bool(spacing and spacing[0]>0 and spacing[1]>0)
            detail=self.tr("assigned")+" — "+str(dims[0])+"×"+str(dims[1])
            if spacingValid:
                detail+=" — spacing %.4f × %.4f mm" % (spacing[0],spacing[1])
            else:
                detail+=" — "+("sin spacing espacial válido" if self.lang=="es" else "no valid spatial spacing")
                complete=False
            lines.append(("✓ " if spacingValid else "⚠ ")+self.tr(key)+": "+detail)
        lines.append("")
        if self.lang=="es":
            lines.append("Estado: "+("cuatro proyecciones asignadas; falta validar el origen de la calibración en mm." if complete else "estudio incompleto o requiere revisión/calibración."))
        else:
            lines.append("Status: "+("four projections assigned; millimetric calibration provenance still requires validation." if complete else "incomplete study or calibration/review required."))
        self.validationText.text="\n".join(lines)

    def startRegistration(self,key):
        volume=self.selectors[key].currentNode()
        if volume is None: slicer.util.errorDisplay(self.tr("noVolume")); return
        self.activeProjection=key
        if key not in self.markupNodes:
            node=self.logic.createLandmarkNode("ONeSpineRx_"+key.upper()); node.SetAttribute("ONeSpineRx.Projection",key); node.SetAttribute("ONeSpineRx.SourceVolumeID",volume.GetID()); node.SetAttribute("ONeSpineRx.DefinitionVersion",self.logic.DEFINITION_VERSION); self.markupNodes[key]=node
        self.placeButton.enabled=True; self.skipButton.enabled=True; self.finishButton.enabled=True
        slicer.util.setSliceViewerLayers(background=volume,fit=True); self.updateGuide()

    def helpFor(self,label):
        if label in LANDMARK_HELP: return LANDMARK_HELP[label][self.lang]
        suffix=label.split("_",1)[1] if "_" in label else label
        return LANDMARK_HELP.get(suffix,{}).get(self.lang,"")

    def updateGuide(self):
        if self.activeProjection is None: return
        labels=self.labels(self.activeProjection); i=self.indices[self.activeProjection]
        if i>=len(labels): self.finishRegistration(); return
        label=labels[i]; self.currentLabel.text=f"{self.tr('current')}: {label}"
        self.helpLabel.text=self.helpFor(label); self.progressLabel.text=f"{self.tr('progress')}: {i+1} / {len(labels)}"

    def placeCurrent(self):
        key=self.activeProjection
        if key is None: return
        labels=self.labels(key); i=self.indices[key]
        if i>=len(labels): return
        label=labels[i]; node=self.markupNodes[key]
        before=node.GetNumberOfControlPoints()
        slicer.mrmlScene.SetActiveMRMLNodeID(node.GetID())
        interaction=slicer.app.applicationLogic().GetInteractionNode(); interaction.SetPlaceModePersistence(0); interaction.SetCurrentInteractionMode(interaction.Place)
        node.SetAttribute("ONeSpineRx.PendingLandmark",label)
        self.currentLabel.text=f"{self.tr('current')}: {label}"
        self.helpLabel.text=self.helpFor(label)+"\\n\\n"+("Haga clic sobre la radiografía. Después continúe con el siguiente punto." if self.lang=="es" else "Click on the radiograph, then continue with the next point.")
        # Advancement is explicit to keep Slicer 5.2 behavior predictable.
        self.indices[key]=i+1
        self.updateGuide()

    def skipCurrent(self):
        key=self.activeProjection
        if key is None:return
        labels=self.labels(key); i=self.indices[key]
        if i<len(labels): self.skipped[key].append(labels[i]); self.indices[key]=i+1
        self.updateGuide()

    def finishRegistration(self):
        if self.activeProjection is not None:
            node=self.markupNodes.get(self.activeProjection)
            if node: node.SetAttribute("ONeSpineRx.Skipped",json.dumps(self.skipped[self.activeProjection]))
        self.currentLabel.text=self.tr("complete"); self.helpLabel.text=""; self.progressLabel.text=""
        self.placeButton.enabled=False; self.skipButton.enabled=False; self.finishButton.enabled=False; self.activeProjection=None

class LumbarRadiographyLogic(ScriptedLoadableModuleLogic):
    DEFINITION_VERSION="1.1.0"
    def createLandmarkNode(self,name):
        node=slicer.mrmlScene.AddNewNodeByClass("vtkMRMLMarkupsFiducialNode",name); node.SetDescription("ONeSpineRx manual anatomical landmarks"); return node
    def saveMarkups(self,node,filePath):
        if node is None: raise ValueError("Markup node is required")
        if not slicer.util.saveNode(node,filePath): raise RuntimeError("Unable to save markups: "+filePath)
        return filePath
    def exportManifest(self,filePath,study):
        payload={"schema_version":"1.0.0","measurement_definition_version":self.DEFINITION_VERSION,"study":study,"slicer_version":slicer.app.applicationVersion}
        with open(filePath,"w",encoding="utf-8") as stream: json.dump(payload,stream,indent=2,ensure_ascii=False)
        return filePath
