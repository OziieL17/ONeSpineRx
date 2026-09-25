import json
import slicer
import qt
import vtk
import ctk
from slicer.ScriptedLoadableModule import *
from slicer.util import VTKObservationMixin

TRANSLATIONS = {
    "es": {
        "study":"Estudio radiográfico", "language":"Idioma", "ap":"AP", "lat":"Lateral neutra",
        "flex":"Flexión", "ext":"Extensión", "select":"Seleccionar volumen",
        "landmarks":"Registro manual de landmarks", "start":"Iniciar registro",
        "importDicom":"Importar DICOM", "categorize":"Categorizar", "validate":"Validar estudio",
        "validation":"Importación, categorización y validación", "assigned":"Asignada", "missing":"Faltante",
        "place":"Marcar punto", "skip":"Saltar", "finish":"Finalizar", "previous":"Anterior", "next":"Siguiente", "edit":"Modificar", "save":"Guardar cambios",
        "current":"Punto actual", "progress":"Progreso", "instructions":"Instrucciones",
        "noVolume":"Seleccione un volumen para esta proyección.",
        "ready":"Seleccione las cuatro proyecciones y pulse Iniciar registro en la proyección que desea medir.",
        "complete":"Registro finalizado. Revise los puntos antes de calcular o exportar.", "results":"Resultados", "calculate":"Calcular medidas", "copy":"Copiar valores", "figure":"Generar imagen",
        "skipped":"Omitido", "calibration":"Calibración milimétrica por proyección", "calibrate":"Calibrar", "knownLength":"Longitud conocida (mm)", "orientation":"Orientación sagital", "anteriorLeft":"Anterior a la izquierda", "anteriorRight":"Anterior a la derecha", "debug":"Depuración traslación", "debugRun":"Depurar segmento",
    },
    "en": {
        "study":"Radiographic study", "language":"Language", "ap":"AP", "lat":"Neutral lateral",
        "flex":"Flexion", "ext":"Extension", "select":"Select volume",
        "landmarks":"Manual landmark registration", "start":"Start registration",
        "importDicom":"Import DICOM", "categorize":"Categorize", "validate":"Validate study",
        "validation":"Import, categorization and validation", "assigned":"Assigned", "missing":"Missing",
        "place":"Place point", "skip":"Skip", "finish":"Finish", "previous":"Previous", "next":"Next", "edit":"Edit", "save":"Save changes",
        "current":"Current landmark", "progress":"Progress", "instructions":"Instructions",
        "noVolume":"Select a volume for this projection.",
        "ready":"Select all four projections and press Start registration on the projection you want to measure.",
        "complete":"Registration finished. Review landmarks before calculation or export.", "results":"Results", "calculate":"Calculate measurements", "copy":"Copy values", "figure":"Generate image",
        "skipped":"Skipped", "calibration":"Millimetric calibration by projection", "calibrate":"Calibrate", "knownLength":"Known length (mm)", "orientation":"Sagittal orientation", "anteriorLeft":"Anterior on left", "anteriorRight":"Anterior on right", "debug":"Translation debug", "debugRun":"Debug segment",
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


class VisualizationSettings:
    LEVELS=("L1_L2","L2_L3","L3_L4","L4_L5","L5_S1")
    def __init__(self):
        self.preset="custom"
        self.show_LL=False; self.show_L4_S1=False; self.show_SS=False; self.show_PI=False; self.show_PT=False
        self.show_IVA={level:False for level in self.LEVELS}
        self.show_translation={level:False for level in self.LEVELS}
        self.show_disc_height_anterior=False; self.show_disc_height_posterior=False; self.show_disc_height_mean=False; self.show_IHI=False
        self.disc_levels={level:False for level in self.LEVELS}
        self.show_auxiliary_geometry=False
    def toDict(self):
        return {"preset":self.preset,"show_LL":self.show_LL,"show_L4_S1":self.show_L4_S1,"show_SS":self.show_SS,"show_PI":self.show_PI,"show_PT":self.show_PT,"show_IVA":dict(self.show_IVA),"show_translation":dict(self.show_translation),"show_disc_height_anterior":self.show_disc_height_anterior,"show_disc_height_posterior":self.show_disc_height_posterior,"show_disc_height_mean":self.show_disc_height_mean,"show_IHI":self.show_IHI,"disc_levels":dict(self.disc_levels),"show_auxiliary_geometry":self.show_auxiliary_geometry}


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
    SAGITTAL_POINTS = [f"{v} {p}" for v in ("L1","L2","L3","L4","L5") for p in ("SA","SP","IA","IP")] + ["S1 SA","S1 SP"]
    LAT_POINTS = SAGITTAL_POINTS + ["FH_R_CENTER","FH_L_CENTER"]
    AP_POINTS = [f"{v} {p}" for v in ("L1","L2","L3","L4","L5") for p in ("SL","SR","IL","IR")] + ["S1 L","S1 R"]
    PREFIX = {"ap":"AP","lat":"LAT","flex":"FLEX","ext":"EXT"}
    COLORS = {"ap":(0.20,0.85,0.35),"lat":(0.95,0.35,0.70),"flex":(0.20,0.70,0.85),"ext":(1.00,0.70,0.10)}

    def __init__(self, parent=None):
        ScriptedLoadableModuleWidget.__init__(self,parent)
        VTKObservationMixin.__init__(self)
        self.logic=None; self.lang="es"; self.activeProjection=None
        self.markupNodes={}; self.indices={k:0 for k in self.PROJECTION_KEYS}; self.skipped={k:[] for k in self.PROJECTION_KEYS}; self.markupObserverTags={}

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
        orientationRow=qt.QHBoxLayout(); self.orientationLabel=qt.QLabel(); self.orientationCombo=qt.QComboBox()
        self.orientationCombo.addItem("Anterior ←", "left"); self.orientationCombo.addItem("Anterior →", "right")
        orientationRow.addWidget(self.orientationLabel); orientationRow.addWidget(self.orientationCombo); validationLayout.addLayout(orientationRow)
        self.layout.addWidget(self.validationBox)
        self.importButton.connect("clicked()",self.importDicom)
        self.categorizeButton.connect("clicked()",self.categorizeLoadedVolumes)
        self.validateButton.connect("clicked()",self.validateStudy)

        self.landmarkBox=qt.QGroupBox(); v=qt.QVBoxLayout(self.landmarkBox)
        self.currentLabel=qt.QLabel(); self.currentLabel.setStyleSheet("font-weight: bold; font-size: 16px;")
        self.helpLabel=qt.QLabel(); self.helpLabel.wordWrap=True
        self.progressLabel=qt.QLabel(); v.addWidget(self.currentLabel); v.addWidget(self.helpLabel); v.addWidget(self.progressLabel)
        buttons=qt.QHBoxLayout()
        self.previousButton=qt.QPushButton(); self.nextButton=qt.QPushButton(); self.skipButton=qt.QPushButton()
        self.editButton=qt.QPushButton(); self.saveButton=qt.QPushButton(); self.finishButton=qt.QPushButton()
        for b in (self.previousButton,self.nextButton,self.skipButton,self.editButton,self.saveButton,self.finishButton):
            buttons.addWidget(b); b.enabled=False
        v.addLayout(buttons); self.layout.addWidget(self.landmarkBox)
        self.calibrationBox=qt.QGroupBox(); cal=qt.QGridLayout(self.calibrationBox)
        self.calibrationProjection=qt.QComboBox()
        for key in self.PROJECTION_KEYS: self.calibrationProjection.addItem(self.tr(key),key)
        self.knownLengthSpin=qt.QDoubleSpinBox(); self.knownLengthSpin.minimum=0.1; self.knownLengthSpin.maximum=1000.0; self.knownLengthSpin.value=25.0; self.knownLengthSpin.suffix=" mm"
        self.calibrateButton=qt.QPushButton(); self.calibrationStatus=qt.QLabel(); self.calibrationStatus.wordWrap=True
        cal.addWidget(self.calibrationProjection,0,0); cal.addWidget(self.knownLengthSpin,0,1); cal.addWidget(self.calibrateButton,0,2); cal.addWidget(self.calibrationStatus,1,0,1,3)
        self.layout.addWidget(self.calibrationBox); self.calibrations={}; self.pendingCalibration=None; self.calibrationObserverTag=None
        self.calibrateButton.connect("clicked()",self.startCalibration)

        self.visualizationBox=ctk.ctkCollapsibleButton()
        self.visualizationBox.text="Mediciones a mostrar en imagen"
        self.visualizationBox.collapsed=True
        vis=qt.QVBoxLayout(self.visualizationBox)
        presetRow=qt.QHBoxLayout(); self.presetButtons={}
        for preset,label in (("clean","Limpia"),("global","Global"),("segmental","Segmentaria"),("dynamic","Dinámica"),("complete","Completa"),("custom","Personalizada")):
            b=qt.QPushButton(label); self.presetButtons[preset]=b; presetRow.addWidget(b); b.connect("clicked()",lambda p=preset:self.applyVisualizationPreset(p))
        vis.addLayout(presetRow)
        self.sameVisualizationCheck=qt.QCheckBox("Usar misma configuración para Neutral/Flexión/Extensión"); self.sameVisualizationCheck.checked=True; vis.addWidget(self.sameVisualizationCheck)
        self.visualizationProjection=qt.QComboBox(); self.visualizationProjection.addItem("NEUTRAL","lat"); self.visualizationProjection.addItem("FLEXION","flex"); self.visualizationProjection.addItem("EXTENSION","ext"); self.visualizationProjection.enabled=False; vis.addWidget(self.visualizationProjection)
        self.sameVisualizationCheck.connect("toggled(bool)",lambda checked:setattr(self.visualizationProjection,"enabled",not checked))
        self.visualizationProjection.connect("currentIndexChanged(int)",self.loadVisualizationSettingsToUI)
        vis.addWidget(qt.QLabel("Alineación global"))
        self.globalChecks={}
        for name,label in (("LL","Lordosis lumbar L1–S1 (LL)"),("L4_S1","Lordosis distal L4–S1"),("SS","Sacral slope (SS)"),("PI","Pelvic incidence (PI)"),("PT","Pelvic tilt (PT)")):
            cb=qt.QCheckBox(label); self.globalChecks[name]=cb; vis.addWidget(cb)
        self.pelvicReliableCheck=qt.QCheckBox("Parámetros pélvicos fiables"); self.pelvicReliableCheck.checked=True; vis.addWidget(self.pelvicReliableCheck)
        vis.addWidget(qt.QLabel("Ángulos segmentarios"))
        self.ivaChecks={}; self.allIvaCheck=qt.QCheckBox("Mostrar todos los IVA"); vis.addWidget(self.allIvaCheck)
        for level in VisualizationSettings.LEVELS:
            cb=qt.QCheckBox("IVA "+level.replace("_","–")); self.ivaChecks[level]=cb; vis.addWidget(cb)
        self.allIvaCheck.connect("toggled(bool)",lambda checked:self.setCheckGroup(self.ivaChecks,checked))
        vis.addWidget(qt.QLabel("Traslación"))
        self.translationChecks={}; self.allTranslationCheck=qt.QCheckBox("Mostrar todas las traslaciones"); vis.addWidget(self.allTranslationCheck)
        for level in VisualizationSettings.LEVELS:
            cb=qt.QCheckBox("Traslación "+level.replace("_","–")); self.translationChecks[level]=cb; vis.addWidget(cb)
        self.allTranslationCheck.connect("toggled(bool)",lambda checked:self.setCheckGroup(self.translationChecks,checked))
        vis.addWidget(qt.QLabel("Altura discal"))
        self.discMetricChecks={}
        for name,label in (("anterior","Altura anterior"),("posterior","Altura posterior"),("mean","Altura media"),("IHI","IHI")):
            cb=qt.QCheckBox(label); self.discMetricChecks[name]=cb; vis.addWidget(cb)
        discRow=qt.QHBoxLayout(); discRow.addWidget(qt.QLabel("Niveles:")); self.discLevelChecks={}
        for level in VisualizationSettings.LEVELS:
            cb=qt.QCheckBox(level.replace("_","–")); self.discLevelChecks[level]=cb; discRow.addWidget(cb)
        vis.addLayout(discRow)
        self.auxGeometryCheck=qt.QCheckBox("Mostrar geometría auxiliar"); self.auxGeometryCheck.checked=False; vis.addWidget(self.auxGeometryCheck)
        self.dynamicComparisonCheck=qt.QCheckBox("Generar Dynamic comparison"); self.dynamicComparisonCheck.checked=False; vis.addWidget(self.dynamicComparisonCheck)
        self.layout.addWidget(self.visualizationBox)
        self.visualizationSettings={key:VisualizationSettings() for key in ("lat","flex","ext")}

        self.resultsBox=qt.QGroupBox(); resultsLayout=qt.QVBoxLayout(self.resultsBox)
        resultButtons=qt.QHBoxLayout(); self.calculateButton=qt.QPushButton(); self.copyButton=qt.QPushButton(); self.figureButton=qt.QPushButton()
        resultButtons.addWidget(self.calculateButton); resultButtons.addWidget(self.copyButton); resultButtons.addWidget(self.figureButton); resultsLayout.addLayout(resultButtons)
        self.resultsText=qt.QTextEdit(); self.resultsText.readOnly=True; self.resultsText.minimumHeight=180; resultsLayout.addWidget(self.resultsText)
        self.layout.addWidget(self.resultsBox); self.lastResults={}
        self.debugBox=qt.QGroupBox(); dbg=qt.QVBoxLayout(self.debugBox); dbgRow=qt.QHBoxLayout()
        self.debugProjection=qt.QComboBox(); self.debugProjection.addItem("LAT","lat"); self.debugProjection.addItem("FLEX","flex"); self.debugProjection.addItem("EXT","ext")
        self.debugSegment=qt.QComboBox()
        for segment in ("L1-L2","L2-L3","L3-L4","L4-L5","L5-S1"): self.debugSegment.addItem(segment,segment)
        self.debugButton=qt.QPushButton(); dbgRow.addWidget(self.debugProjection); dbgRow.addWidget(self.debugSegment); dbgRow.addWidget(self.debugButton); dbg.addLayout(dbgRow)
        self.debugText=qt.QTextEdit(); self.debugText.readOnly=True; self.debugText.minimumHeight=160; dbg.addWidget(self.debugText); self.layout.addWidget(self.debugBox)
        self.debugButton.connect("clicked()",self.debugTranslation)
        self.calculateButton.connect("clicked()",self.calculateMeasurements); self.copyButton.connect("clicked()",self.copyResults); self.figureButton.connect("clicked()",self.generateFigure)
        self.previousButton.connect("clicked()",self.previousLandmark); self.nextButton.connect("clicked()",self.nextLandmark); self.skipButton.connect("clicked()",self.skipCurrent); self.editButton.connect("clicked()",self.editCurrent); self.saveButton.connect("clicked()",self.saveChanges); self.finishButton.connect("clicked()",self.finishRegistration)
        self.languageCombo.connect("currentIndexChanged(int)",self.changeLanguage)
        self.applyLanguage(); self.layout.addStretch(1)

    def cleanup(self): self.removeObservers()

    def tr(self,key): return TRANSLATIONS[self.lang].get(key,key)
    def changeLanguage(self,_index):
        self.lang=self.languageCombo.itemData(self.languageCombo.currentIndex); self.applyLanguage(); self.updateGuide()

    def applyLanguage(self):
        self.studyBox.title=self.tr("study"); self.landmarkBox.title=self.tr("landmarks"); self.validationBox.title=self.tr("validation"); self.resultsBox.title=self.tr("results"); self.calibrationBox.title=self.tr("calibration"); self.debugBox.title=self.tr("debug")
        self.importButton.text=self.tr("importDicom"); self.categorizeButton.text=self.tr("categorize"); self.validateButton.text=self.tr("validate"); self.orientationLabel.text=self.tr("orientation"); self.debugButton.text=self.tr("debugRun")
        for key in self.PROJECTION_KEYS:
            getattr(self,key+"Label").text=self.tr(key)
            getattr(self,key+"StartButton").text=self.tr("start")
        self.previousButton.text=self.tr("previous"); self.nextButton.text=self.tr("next"); self.skipButton.text=self.tr("skip"); self.editButton.text=self.tr("edit"); self.saveButton.text=self.tr("save"); self.finishButton.text=self.tr("finish")
        self.calibrateButton.text=self.tr("calibrate"); self.calculateButton.text=self.tr("calculate"); self.copyButton.text=self.tr("copy"); self.figureButton.text=self.tr("figure")
        if self.activeProjection is None: self.currentLabel.text=self.tr("ready"); self.helpLabel.text=""; self.progressLabel.text=""

    def labels(self,key):
        points=self.AP_POINTS if key=="ap" else (self.LAT_POINTS if key=="lat" else self.SAGITTAL_POINTS)
        prefix=self.PREFIX[key]
        return [prefix+" "+p for p in points]

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

    def startCalibration(self):
        key=self.calibrationProjection.itemData(self.calibrationProjection.currentIndex)
        volume=self.selectors[key].currentNode()
        if volume is None: slicer.util.errorDisplay(self.tr("noVolume")); return
        slicer.util.setSliceViewerLayers(background=volume,fit=True)
        node=slicer.mrmlScene.AddNewNodeByClass("vtkMRMLMarkupsLineNode","ONeSpineRx_CAL_"+self.PREFIX[key])
        node.SetAttribute("ONeSpineRx.CalibrationProjection",key); self.pendingCalibration=node
        self.calibrationObserverTag=node.AddObserver(slicer.vtkMRMLMarkupsNode.PointPositionDefinedEvent,self.onCalibrationPoint)
        slicer.mrmlScene.SetActiveMRMLNodeID(node.GetID()); interaction=slicer.app.applicationLogic().GetInteractionNode(); interaction.SetPlaceModePersistence(1); interaction.SetCurrentInteractionMode(interaction.Place)
        self.calibrationStatus.text=("Marque los dos extremos de una referencia de %.1f mm en %s." if self.lang=="es" else "Mark both ends of a %.1f mm reference on %s.") % (self.knownLengthSpin.value,self.PREFIX[key])

    def onCalibrationPoint(self,caller,event):
        if caller is not self.pendingCalibration or caller.GetNumberOfControlPoints()<2: return
        key=caller.GetAttribute("ONeSpineRx.CalibrationProjection"); a=[0.0,0.0,0.0]; b=[0.0,0.0,0.0]
        caller.GetNthControlPointPositionWorld(0,a); caller.GetNthControlPointPositionWorld(1,b)
        import math
        measured=math.hypot(b[0]-a[0],b[1]-a[1]); known=float(self.knownLengthSpin.value)
        if measured<=0: return
        factor=known/measured; self.calibrations[key]={"method":"manual_two_point","known_mm":known,"measured_scene_units":measured,"factor_mm_per_scene_unit":factor,"verified":True}
        caller.SetAttribute("ONeSpineRx.KnownLengthMM",str(known)); caller.SetAttribute("ONeSpineRx.CalibrationFactor",str(factor))
        caller.RemoveObserver(self.calibrationObserverTag); self.calibrationObserverTag=None
        interaction=slicer.app.applicationLogic().GetInteractionNode(); interaction.SetCurrentInteractionMode(interaction.ViewTransform)
        self.calibrationStatus.text=("✓ %s calibrada: %.6f mm/unidad." if self.lang=="es" else "✓ %s calibrated: %.6f mm/unit.") % (self.PREFIX[key],factor)
        self.pendingCalibration=None

    def calibrationFactor(self,key):
        item=self.calibrations.get(key)
        return item["factor_mm_per_scene_unit"] if item and item.get("verified") else None
    def startRegistration(self,key):
        volume=self.selectors[key].currentNode()
        if volume is None:
            slicer.util.errorDisplay(self.tr("noVolume")); return
        self.activeProjection=key
        for projection,node in self.markupNodes.items():
            if node.GetDisplayNode():
                node.GetDisplayNode().SetVisibility(projection==key)
        if key not in self.markupNodes:
            node=self.logic.createLandmarkNode("ONeSpineRx_"+self.PREFIX[key])
            node.SetAttribute("ONeSpineRx.Projection",key)
            node.SetAttribute("ONeSpineRx.SourceVolumeID",volume.GetID())
            node.SetAttribute("ONeSpineRx.DefinitionVersion",self.logic.DEFINITION_VERSION)
            color=self.COLORS[key]
            node.GetDisplayNode().SetSelectedColor(*color)
            node.GetDisplayNode().SetColor(*color)
            node.GetDisplayNode().SetTextScale(1.05)
            self.markupNodes[key]=node
            tag=node.AddObserver(slicer.vtkMRMLMarkupsNode.PointPositionDefinedEvent,self.onPointDefined)
            self.markupObserverTags[key]=tag
        self.indices[key]=min(self.indices[key],len(self.labels(key))-1)
        for b in (self.previousButton,self.nextButton,self.skipButton,self.editButton,self.saveButton,self.finishButton):
            b.enabled=True
        slicer.util.setSliceViewerLayers(background=volume,fit=True)
        self.updateGuide()
        self.activatePlacement()

    def activatePlacement(self):
        if self.activeProjection is None: return
        node=self.markupNodes[self.activeProjection]
        slicer.mrmlScene.SetActiveMRMLNodeID(node.GetID())
        interaction=slicer.app.applicationLogic().GetInteractionNode()
        interaction.SetPlaceModePersistence(1)
        interaction.SetCurrentInteractionMode(interaction.Place)

    def onPointDefined(self,caller,event):
        key=self.activeProjection
        if key is None or caller is not self.markupNodes.get(key): return
        i=self.indices[key]; labels=self.labels(key)
        if i>=len(labels): return
        pointIndex=caller.GetNumberOfControlPoints()-1
        if pointIndex>=0:
            caller.SetNthControlPointLabel(pointIndex,labels[i])
            caller.SetNthControlPointDescription(pointIndex,self.helpFor(labels[i]))
        self.indices[key]=i+1
        if self.indices[key]>=len(labels):
            self.finishRegistration()
        else:
            self.updateGuide()
            self.activatePlacement()

    def helpFor(self,label):
        if label.endswith("FH_R_CENTER"):
            return "Centro de la cabeza femoral derecha." if self.lang=="es" else "Center of the right femoral head."
        if label.endswith("FH_L_CENTER"):
            return "Centro de la cabeza femoral izquierda." if self.lang=="es" else "Center of the left femoral head."
        token=label.split()[-1]
        mapping={"SA":"AS","SP":"PS","IA":"AI","IP":"PI","SL":"SL","SR":"SR","IL":"IL","IR":"IR"}
        return LANDMARK_HELP.get(mapping.get(token,token),{}).get(self.lang,"")

    def updateGuide(self):
        if self.activeProjection is None: return
        labels=self.labels(self.activeProjection); i=self.indices[self.activeProjection]
        if i>=len(labels): self.finishRegistration(); return
        label=labels[i]; self.currentLabel.text=f"{self.tr('current')}: {label}"
        self.helpLabel.text=self.helpFor(label); self.progressLabel.text=f"{self.tr('progress')}: {i+1} / {len(labels)}"

    def previousLandmark(self):
        if self.activeProjection is None: return
        self.indices[self.activeProjection]=max(0,self.indices[self.activeProjection]-1)
        self.updateGuide()

    def nextLandmark(self):
        if self.activeProjection is None: return
        labels=self.labels(self.activeProjection)
        self.indices[self.activeProjection]=min(len(labels)-1,self.indices[self.activeProjection]+1)
        self.updateGuide()

    def editCurrent(self):
        if self.activeProjection is None: return
        label=self.labels(self.activeProjection)[self.indices[self.activeProjection]]
        node=self.markupNodes[self.activeProjection]
        for i in range(node.GetNumberOfControlPoints()):
            if node.GetNthControlPointLabel(i)==label:
                node.SetNthControlPointSelected(i,True)
                self.currentLabel.text=self.tr("current")+": "+label
                self.helpLabel.text=("Arrastre el marcador seleccionado y pulse Guardar cambios." if self.lang=="es" else "Drag the selected marker, then press Save changes.")
                return

    def saveChanges(self):
        if self.activeProjection is None: return
        node=self.markupNodes[self.activeProjection]
        for i in range(node.GetNumberOfControlPoints()):
            node.SetNthControlPointSelected(i,False)
        node.Modified()
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
        for b in (self.previousButton,self.nextButton,self.skipButton,self.editButton,self.saveButton,self.finishButton):
            b.enabled=False
        self.activeProjection=None
    def setCheckGroup(self,group,checked):
        for cb in group.values(): cb.checked=checked

    def visualizationKey(self):
        return self.visualizationProjection.itemData(self.visualizationProjection.currentIndex)

    def readVisualizationSettings(self,key=None):
        key=key or self.visualizationKey(); s=self.visualizationSettings[key]
        s.show_LL=self.globalChecks["LL"].checked; s.show_L4_S1=self.globalChecks["L4_S1"].checked; s.show_SS=self.globalChecks["SS"].checked
        s.show_PI=self.globalChecks["PI"].checked; s.show_PT=self.globalChecks["PT"].checked
        s.show_IVA={level:cb.checked for level,cb in self.ivaChecks.items()}; s.show_translation={level:cb.checked for level,cb in self.translationChecks.items()}
        s.show_disc_height_anterior=self.discMetricChecks["anterior"].checked; s.show_disc_height_posterior=self.discMetricChecks["posterior"].checked; s.show_disc_height_mean=self.discMetricChecks["mean"].checked; s.show_IHI=self.discMetricChecks["IHI"].checked
        s.disc_levels={level:cb.checked for level,cb in self.discLevelChecks.items()}; s.show_auxiliary_geometry=self.auxGeometryCheck.checked
        if self.sameVisualizationCheck.checked:
            payload=s.toDict()
            for other in ("lat","flex","ext"):
                if other==key: continue
                o=self.visualizationSettings[other]; o.__dict__.update({k:(dict(v) if isinstance(v,dict) else v) for k,v in s.__dict__.items()})
        return s

    def loadVisualizationSettingsToUI(self,_index=None):
        key=self.visualizationKey(); s=self.visualizationSettings.get(key)
        if not s: return
        self.globalChecks["LL"].checked=s.show_LL; self.globalChecks["L4_S1"].checked=s.show_L4_S1; self.globalChecks["SS"].checked=s.show_SS; self.globalChecks["PI"].checked=s.show_PI; self.globalChecks["PT"].checked=s.show_PT
        for level,cb in self.ivaChecks.items(): cb.checked=s.show_IVA.get(level,False)
        for level,cb in self.translationChecks.items(): cb.checked=s.show_translation.get(level,False)
        self.discMetricChecks["anterior"].checked=s.show_disc_height_anterior; self.discMetricChecks["posterior"].checked=s.show_disc_height_posterior; self.discMetricChecks["mean"].checked=s.show_disc_height_mean; self.discMetricChecks["IHI"].checked=s.show_IHI
        for level,cb in self.discLevelChecks.items(): cb.checked=s.disc_levels.get(level,False)
        self.auxGeometryCheck.checked=s.show_auxiliary_geometry
        self.updateMeasurementAvailabilityUI()
    def applyVisualizationPreset(self,preset):
        for cb in list(self.globalChecks.values())+list(self.ivaChecks.values())+list(self.translationChecks.values())+list(self.discMetricChecks.values()): cb.checked=False
        if preset=="global":
            for name in ("LL","L4_S1","SS"): self.globalChecks[name].checked=True
        elif preset=="segmental": self.setCheckGroup(self.ivaChecks,True)
        elif preset=="dynamic":
            self.setCheckGroup(self.ivaChecks,True); self.setCheckGroup(self.translationChecks,True)
        elif preset=="complete":
            for cb in self.globalChecks.values(): cb.checked=True
            self.setCheckGroup(self.ivaChecks,True); self.setCheckGroup(self.translationChecks,True)
            for cb in self.discMetricChecks.values(): cb.checked=True
            for cb in self.discLevelChecks.values(): cb.checked=True
        self.readVisualizationSettings().preset=preset
    def pointMap(self,key):
        node=self.markupNodes.get(key); points={}
        if not node: return points
        for i in range(node.GetNumberOfControlPoints()):
            p=[0.0,0.0,0.0]; node.GetNthControlPointPositionWorld(i,p); points[node.GetNthControlPointLabel(i)]=p
        return points

    def angleBetween(self,a,b,c,d):
        import math
        ux,uy=b[0]-a[0],b[1]-a[1]; vx,vy=d[0]-c[0],d[1]-c[1]
        angle=abs(math.degrees(math.atan2(ux*vy-uy*vx,ux*vx+uy*vy)))%180.0
        return min(angle,180.0-angle)

    def translationMeasurement(self,key,upper,lower):
        import math
        p=self.pointMap(key); prefix=self.PREFIX[key]; q=lambda name: p.get(prefix+" "+name)
        names=(upper+" IP",lower+" SP",lower+" SA"); missing=[n for n in names if q(n) is None]
        base={"measurement_valid":False,"invalid_reason":None,"calibration_valid":self.calibrationFactor(key) is not None,"translation_mm":None,"translation_pct":None}
        if missing: base["invalid_reason"]="missing_landmarks:"+",".join(missing); return base
        pa,pb,pant=q(upper+" IP"),q(lower+" SP"),q(lower+" SA")
        values=pa+pb+pant
        if not all(math.isfinite(x) for x in values): base["invalid_reason"]="non_finite_coordinates"; return base
        dx,dy=pant[0]-pb[0],pant[1]-pb[1]; ap=math.hypot(dx,dy)
        if ap<=1e-9: base["invalid_reason"]="invalid_AP_reference"; return base
        ux,uy=dx/ap,dy/ap; vx,vy=-uy,ux; rx,ry=pa[0]-pb[0],pa[1]-pb[1]; t=rx*ux+ry*uy
        if not math.isfinite(t): base["invalid_reason"]="non_finite_projection"; return base
        pct=100.0*t/ap; factor=self.calibrationFactor(key)
        expected=self.orientationCombo.itemData(self.orientationCombo.currentIndex); observed="right" if dx>0 else "left"
        orientationOK=(expected==observed)
        base.update({"measurement_valid":orientationOK,"invalid_reason":None if orientationOK else "anterior_posterior_orientation_mismatch","P_A":list(pa),"P_B":list(pb),"P_anterior":list(pant),"u":[ux,uy],"v":[vx,vy],"AP_reference_scene":ap,"translation_scene":t,"translation_pct":pct,"orientation_expected":expected,"orientation_observed":observed,"orientation_qc":orientationOK})
        if factor is not None: base["translation_mm"]=t*factor; base["AP_reference_mm"]=ap*factor
        return base

    def calculateTranslations(self):
        segments=(("L1","L2"),("L2","L3"),("L3","L4"),("L4","L5"),("L5","S1")); out={}
        for upper,lower in segments:
            name=upper+"_"+lower; n=self.translationMeasurement("lat",upper,lower); f=self.translationMeasurement("flex",upper,lower); e=self.translationMeasurement("ext",upper,lower)
            item={"neutral_mm":n.get("translation_mm"),"neutral_pct":n.get("translation_pct"),"flex_mm":f.get("translation_mm"),"flex_pct":f.get("translation_pct"),"ext_mm":e.get("translation_mm"),"ext_pct":e.get("translation_pct"),"neutral":n,"flex":f,"ext":e}
            if f.get("measurement_valid") and e.get("measurement_valid"):
                ds=e["translation_pct"]-f["translation_pct"]; item["delta_signed_pct"]=ds; item["delta_flex_ext_pct"]=abs(ds)
                if f.get("translation_mm") is not None and e.get("translation_mm") is not None:
                    dmm=e["translation_mm"]-f["translation_mm"]; item["delta_signed_mm"]=dmm; item["delta_flex_ext_mm"]=abs(dmm)
                else: item["delta_signed_mm"]=None; item["delta_flex_ext_mm"]=None
            else:
                item.update({"delta_signed_pct":None,"delta_flex_ext_pct":None,"delta_signed_mm":None,"delta_flex_ext_mm":None})
            out[name]=item
        return out

    def debugTranslation(self):
        key=self.debugProjection.itemData(self.debugProjection.currentIndex); segment=self.debugSegment.itemData(self.debugSegment.currentIndex); upper,lower=segment.split("-")
        m=self.translationMeasurement(key,upper,lower); lines=["%s %s" % (self.PREFIX[key],segment)]
        for name in ("P_A","P_B","P_anterior","u","v","AP_reference_scene","translation_scene","translation_mm","translation_pct","calibration_valid","orientation_expected","orientation_observed","orientation_qc","measurement_valid","invalid_reason"): lines.append("%s = %s" % (name,m.get(name)))
        self.debugText.plainText="\n".join(lines)
        if m.get("measurement_valid"): self.buildTranslationOverlay(key,upper,lower,m)

    def buildTranslationOverlay(self,key,upper,lower,m):
        self.clearMeasurementOverlays(); pa=m["P_A"]; pb=m["P_B"]; pant=m["P_anterior"]; ap=m["AP_reference_scene"]; u=m["u"]; v=m["v"]
        self.addMeasurementLine("T_"+upper+"_"+lower+"_AP",pb,pant,(0.10,0.85,0.35))
        scale=0.35*ap; vend=[pb[0]+v[0]*scale,pb[1]+v[1]*scale,pb[2]]; self.addMeasurementLine("T_"+upper+"_"+lower+"_V",pb,vend,(0.90,0.75,0.10))
        proj=[pb[0]+u[0]*m["translation_scene"],pb[1]+u[1]*m["translation_scene"],pb[2]]; self.addMeasurementLine("T_"+upper+"_"+lower+"_PROJ",pb,proj,(0.15,0.75,0.95)); self.addMeasurementLine("T_"+upper+"_"+lower+"_DROP",pa,proj,(0.85,0.35,0.70))
        volume=self.selectors[key].currentNode()
        if volume: slicer.util.setSliceViewerLayers(background=volume,fit=True)
        for projection,node in self.markupNodes.items():
            if node.GetDisplayNode(): node.GetDisplayNode().SetVisibility(projection==key)
    def measurementValidity(self,results):
        validity={}
        for key in ("lat","flex","ext"):
            r=results.get(key,{}); v={}
            mapping={"LL":"LL_deg","L4_S1":"LL_L4_S1_deg","SS":"SS_deg","PI":"PI_deg","PT":"PT_deg"}
            for name,resultKey in mapping.items():
                ok=resultKey in r and r.get(resultKey) is not None
                reason=None if ok else ("femoral_heads_not_visible" if name in ("PI","PT") else "required_landmarks_unavailable")
                v[name]={"measurement_valid":ok,"invalid_reason":reason}
            for level in VisualizationSettings.LEVELS:
                k="IVA_"+level+"_deg"; ok=k in r and r.get(k) is not None; v["IVA_"+level]={"measurement_valid":ok,"invalid_reason":None if ok else "required_landmarks_unavailable"}
                for metric,suffix in (("DH_anterior","anterior_mm"),("DH_posterior","posterior_mm"),("DH_mean","mean_mm"),("IHI","IHI")):
                    rk=("IHI_"+level+"_pct") if metric=="IHI" else ("DH_"+level+"_"+suffix)
                    ok=rk in r and r.get(rk) is not None
                    reason=None if ok else ("calibration_unavailable" if metric.startswith("DH") else "required_landmarks_unavailable")
                    v[metric+"_"+level]={"measurement_valid":ok,"invalid_reason":reason}
            validity[key]=v
        return validity

    def pelvicValidity(self):
        p=self.pointMap("lat"); prefix=self.PREFIX["lat"]; q=lambda name:p.get(prefix+" "+name)
        if not self.pelvicReliableCheck.checked: return {"pelvic_parameters_valid":False,"pelvic_invalid_reason":"manual_exclusion"}
        if q("FH_R_CENTER") is None or q("FH_L_CENTER") is None: return {"pelvic_parameters_valid":False,"pelvic_invalid_reason":"femoral_heads_not_visible"}
        if q("S1 SA") is None or q("S1 SP") is None: return {"pelvic_parameters_valid":False,"pelvic_invalid_reason":"bicoxofemoral_axis_unavailable"}
        return {"pelvic_parameters_valid":True,"pelvic_invalid_reason":None}

    def updateMeasurementAvailabilityUI(self):
        if not self.lastResults: return
        validity=self.lastResults.get("validity",{}).get(self.visualizationKey(),{}); pelvic=self.lastResults.get("pelvic_validity",{})
        pairs=[(self.globalChecks["LL"],"LL"),(self.globalChecks["L4_S1"],"L4_S1"),(self.globalChecks["SS"],"SS"),(self.globalChecks["PI"],"PI"),(self.globalChecks["PT"],"PT")]
        for level,cb in self.ivaChecks.items(): pairs.append((cb,"IVA_"+level))
        for cb,name in pairs:
            item=validity.get(name,{"measurement_valid":False,"invalid_reason":"not_calculated"}); ok=item.get("measurement_valid",False)
            if name in ("PI","PT") and not pelvic.get("pelvic_parameters_valid",False): ok=False; item={"invalid_reason":pelvic.get("pelvic_invalid_reason")}
            cb.enabled=ok; cb.toolTip="" if ok else str(item.get("invalid_reason") or "No disponible")
    def calculateMeasurements(self):
        results={}
        for key in ("lat","flex","ext"):
            p=self.pointMap(key); prefix=self.PREFIX[key]; r={}; q=lambda name: p.get(prefix+" "+name)
            if all(q(x) for x in ("L1 SA","L1 SP","S1 SA","S1 SP")): r["LL_deg"]=self.angleBetween(q("L1 SA"),q("L1 SP"),q("S1 SA"),q("S1 SP"))
            if all(q(x) for x in ("L4 SA","L4 SP","S1 SA","S1 SP")): r["LL_L4_S1_deg"]=self.angleBetween(q("L4 SA"),q("L4 SP"),q("S1 SA"),q("S1 SP"))
            if all(q(x) for x in ("S1 SA","S1 SP")):
                import math
                sa,sp=q("S1 SA"),q("S1 SP"); r["SS_deg"]=abs(math.degrees(math.atan2(sp[1]-sa[1],sp[0]-sa[0])))
            for upper,lower in zip(("L1","L2","L3","L4","L5"),("L2","L3","L4","L5","S1")):
                needed=(upper+" IA",upper+" IP",lower+" SA",lower+" SP")
                if all(q(x) for x in needed):
                    ua,up,la,lp=[q(x) for x in needed]
                    r["IVA_"+upper+"_"+lower+"_deg"]=self.angleBetween(ua,up,la,lp)
                    import math
                    dist=lambda a,b: math.hypot(b[0]-a[0],b[1]-a[1])
                    # Lan et al. 2019: IHI=(anterior height + posterior height)/(superior width + inferior width)*100.
                    den=dist(ua,up)+dist(la,lp)
                    if den>0: r["IHI_"+upper+"_"+lower+"_pct"]=100.0*(dist(ua,la)+dist(up,lp))/den
                    factor=self.calibrationFactor(key)
                    if factor:
                        r["DH_"+upper+"_"+lower+"_anterior_mm"]=dist(ua,la)*factor
                        r["DH_"+upper+"_"+lower+"_posterior_mm"]=dist(up,lp)*factor
                        r["DH_"+upper+"_"+lower+"_mean_mm"]=0.5*(dist(ua,la)+dist(up,lp))*factor
            if key=="lat" and all(q(x) for x in ("S1 SA","S1 SP","FH_R_CENTER","FH_L_CENTER")):
                import math
                sa,sp=q("S1 SA"),q("S1 SP"); sm=((sa[0]+sp[0])/2.0,(sa[1]+sp[1])/2.0)
                fr,fl=q("FH_R_CENTER"),q("FH_L_CENTER"); fh=((fr[0]+fl[0])/2.0,(fr[1]+fl[1])/2.0)
                dx,dy=sp[0]-sa[0],sp[1]-sa[1]; vx,vy=sm[0]-fh[0],sm[1]-fh[1]
                r["PT_deg"]=abs(math.degrees(math.atan2(vx,vy)))
                nx,ny=-dy,dx; hx,hy=fh[0]-sm[0],fh[1]-sm[1]; r["PI_deg"]=abs(math.degrees(math.atan2(nx*hy-ny*hx,nx*hx+ny*hy)))
            results[key]=r
        dyn={}
        for name in set(results.get("flex",{})).intersection(results.get("ext",{})):
            if name.endswith("_deg"): dyn["delta_"+name]=abs(results["flex"][name]-results["ext"][name])
        results["dynamic"]=dyn
        results["translation"]=self.calculateTranslations()
        results["validity"]=self.measurementValidity(results)
        results["pelvic_validity"]=self.pelvicValidity()
        settings=self.readVisualizationSettings()
        results["visualization"]=settings.toDict() if self.sameVisualizationCheck.checked else {key:self.visualizationSettings[key].toDict() for key in ("lat","flex","ext")}
        self.lastResults=results
        self.updateMeasurementAvailabilityUI()
        lines=[]
        for section,data in results.items():
            lines.append("["+section.upper()+"]")
            if section in ("lat","flex","ext","dynamic"): lines.extend("%s = %.2f" % (name,value) for name,value in data.items())
            elif section in ("validity","pelvic_validity","visualization"): lines.append(json.dumps(data,ensure_ascii=False))
            else:
                for level,item in data.items(): lines.append("%s: neutral=%s%% flex=%s%% ext=%s%% delta=%s%%" % (level, self.fmt(item.get("neutral_pct")), self.fmt(item.get("flex_pct")), self.fmt(item.get("ext_pct")), self.fmt(item.get("delta_flex_ext_pct"))))
            lines.append("")
        lines.append("ECA: pendiente de landmark de concavidad; no puede inferirse de las cuatro esquinas vertebrales.")
        self.resultsText.plainText="\n".join(lines)
    def fmt(self,value):
        return "NA" if value is None else ("%.2f" % value)

    def copyResults(self):
        if not self.lastResults: self.calculateMeasurements()
        qt.QApplication.clipboard().setText(json.dumps(self.lastResults,indent=2,ensure_ascii=False))

    def clearMeasurementOverlays(self):
        for node in list(slicer.util.getNodesByClass("vtkMRMLMarkupsNode")):
            if node.GetAttribute("ONeSpineRx.MeasurementOverlay")=="1": slicer.mrmlScene.RemoveNode(node)

    def addMeasurementLine(self,name,a,b,color=(0.95,0.25,0.15)):
        node=slicer.mrmlScene.AddNewNodeByClass("vtkMRMLMarkupsLineNode","ONeSpineRx_"+name)
        node.SetAttribute("ONeSpineRx.MeasurementOverlay","1")
        node.AddControlPointWorld(vtk.vtkVector3d(a[0],a[1],a[2])); node.AddControlPointWorld(vtk.vtkVector3d(b[0],b[1],b[2]))
        d=node.GetDisplayNode(); d.SetSelectedColor(*color); d.SetColor(*color); d.SetLineThickness(0.35); d.SetTextScale(1.15); d.SetPointLabelsVisibility(False)
        return node

    def addMeasurementLabel(self,name,point,text,color=(1.0,1.0,1.0)):
        node=slicer.mrmlScene.AddNewNodeByClass("vtkMRMLMarkupsFiducialNode","ONeSpineRx_LABEL_"+name); node.SetAttribute("ONeSpineRx.MeasurementOverlay","1")
        node.AddControlPointWorld(vtk.vtkVector3d(point[0],point[1],point[2])); node.SetNthControlPointLabel(0,text)
        d=node.GetDisplayNode(); d.SetSelectedColor(*color); d.SetColor(*color); d.SetTextScale(1.25); d.SetGlyphScale(0.0)
        return node

    def labelPoint(self,anchor,occupied):
        offsets=((0,8),(8,8),(-8,8),(10,0),(-10,0),(0,-8),(10,-8),(-10,-8),(0,16))
        for ox,oy in offsets:
            p=[anchor[0]+ox,anchor[1]+oy,anchor[2]]
            if all((p[0]-q[0])**2+(p[1]-q[1])**2>100.0 for q in occupied): occupied.append(p); return p
        p=[anchor[0],anchor[1]+24,anchor[2]]; occupied.append(p); return p

    def addAngleArc(self,name,a,b,c,d,value,occupied):
        import math
        m1=[(a[i]+b[i])/2.0 for i in range(3)]; m2=[(c[i]+d[i])/2.0 for i in range(3)]; center=[(m1[i]+m2[i])/2.0 for i in range(3)]
        u=[b[0]-a[0],b[1]-a[1]]; v=[d[0]-c[0],d[1]-c[1]]; au=math.atan2(u[1],u[0]); av=math.atan2(v[1],v[0])
        diff=(av-au+math.pi)%(2*math.pi)-math.pi
        if abs(diff)>math.pi/2: diff=diff-math.copysign(math.pi,diff)
        radius=max(6.0,min(16.0,0.18*(math.hypot(u[0],u[1])+math.hypot(v[0],v[1]))))
        curve=slicer.mrmlScene.AddNewNodeByClass("vtkMRMLMarkupsCurveNode","ONeSpineRx_ARC_"+name); curve.SetAttribute("ONeSpineRx.MeasurementOverlay","1")
        for i in range(13):
            t=au+diff*i/12.0; curve.AddControlPointWorld(vtk.vtkVector3d(center[0]+radius*math.cos(t),center[1]+radius*math.sin(t),center[2]))
        dd=curve.GetDisplayNode(); dd.SetSelectedColor(0.95,0.25,0.15); dd.SetColor(0.95,0.25,0.15); dd.SetPointLabelsVisibility(False); dd.SetGlyphScale(0.0)
        lp=self.labelPoint([center[0]+radius,center[1]+radius,center[2]],occupied); self.addMeasurementLabel(name,lp,"%s\n%.1f°" % (name.replace("_","–"),value))

    def buildMeasurementOverlays(self,key):
        self.clearMeasurementOverlays()
        if key not in ("lat","flex","ext"): return False
        if not self.lastResults: self.calculateMeasurements()
        s=self.readVisualizationSettings(key); r=self.lastResults.get(key,{}); validity=self.lastResults.get("validity",{}).get(key,{})
        p=self.pointMap(key); prefix=self.PREFIX[key]; q=lambda name:p.get(prefix+" "+name); occupied=[]
        def valid(name): return validity.get(name,{}).get("measurement_valid",False)
        def line(name,a,b,color=(0.95,0.25,0.15)):
            if a is not None and b is not None: self.addMeasurementLine(name,a,b,color)
        if s.show_LL and valid("LL"):
            line("LL_L1",q("L1 SA"),q("L1 SP")); line("LL_S1",q("S1 SA"),q("S1 SP")); self.addAngleArc("LL",q("L1 SA"),q("L1 SP"),q("S1 SA"),q("S1 SP"),r["LL_deg"],occupied)
        if s.show_L4_S1 and valid("L4_S1"):
            line("L4S1_L4",q("L4 SA"),q("L4 SP")); line("L4S1_S1",q("S1 SA"),q("S1 SP")); self.addAngleArc("L4_S1",q("L4 SA"),q("L4 SP"),q("S1 SA"),q("S1 SP"),r["LL_L4_S1_deg"],occupied)
        if s.show_SS and valid("SS"):
            line("SS_S1",q("S1 SA"),q("S1 SP")); anchor=self.labelPoint(q("S1 SA"),occupied); self.addMeasurementLabel("SS",anchor,"SS %.1f°" % r["SS_deg"])
        pelvic=self.lastResults.get("pelvic_validity",{}).get("pelvic_parameters_valid",False)
        if key=="lat" and pelvic:
            if s.show_PI and valid("PI"): self.addMeasurementLabel("PI",self.labelPoint(q("S1 SP"),occupied),"PI %.1f°" % r["PI_deg"])
            if s.show_PT and valid("PT"): self.addMeasurementLabel("PT",self.labelPoint(q("S1 SA"),occupied),"PT %.1f°" % r["PT_deg"])
        for level in VisualizationSettings.LEVELS:
            upper,lower=level.split("_")
            if s.show_IVA.get(level) and valid("IVA_"+level):
                a,b,c0,d=q(upper+" IA"),q(upper+" IP"),q(lower+" SA"),q(lower+" SP"); line("IVA_"+level+"_U",a,b); line("IVA_"+level+"_L",c0,d); self.addAngleArc("IVA_"+level,a,b,c0,d,r["IVA_"+level+"_deg"],occupied)
            if s.show_translation.get(level):
                tm=self.lastResults.get("translation",{}).get(level,{}).get({"lat":"neutral","flex":"flex","ext":"ext"}[key],{})
                if tm.get("measurement_valid"):
                    pa,pb,pant=tm["P_A"],tm["P_B"],tm["P_anterior"]; u,v=tm["u"],tm["v"]; line("T_"+level+"_AP",pb,pant,(0.10,0.85,0.35)); proj=[pb[0]+u[0]*tm["translation_scene"],pb[1]+u[1]*tm["translation_scene"],pb[2]]; line("T_"+level,pb,proj,(0.15,0.75,0.95))
                    text=level.replace("_","→")+"\n"+(("%.1f mm\n" % tm["translation_mm"]) if tm.get("translation_mm") is not None else "")+("%.1f%%" % tm["translation_pct"]); self.addMeasurementLabel("T_"+level,self.labelPoint(proj,occupied),text)
                    if s.show_auxiliary_geometry:
                        scale=0.35*tm["AP_reference_scene"]; vend=[pb[0]+v[0]*scale,pb[1]+v[1]*scale,pb[2]]; line("T_"+level+"_V",pb,vend,(0.90,0.75,0.10)); line("T_"+level+"_DROP",pa,proj,(0.85,0.35,0.70))
        for level in VisualizationSettings.LEVELS:
            if not s.disc_levels.get(level): continue
            upper,lower=level.split("_"); ua,up,la,lp=q(upper+" IA"),q(upper+" IP"),q(lower+" SA"),q(lower+" SP")
            labels=[]
            if s.show_disc_height_anterior and valid("DH_anterior_"+level): line("DH_A_"+level,ua,la,(0.15,0.75,0.95)); labels.append("A %.1f mm" % r["DH_"+level+"_anterior_mm"])
            if s.show_disc_height_posterior and valid("DH_posterior_"+level): line("DH_P_"+level,up,lp,(0.15,0.75,0.95)); labels.append("P %.1f mm" % r["DH_"+level+"_posterior_mm"])
            if s.show_disc_height_mean and valid("DH_mean_"+level): labels.append("M %.1f mm" % r["DH_"+level+"_mean_mm"])
            if s.show_IHI and valid("IHI_"+level): labels.append("IHI %.1f%%" % r["IHI_"+level+"_pct"])
            if labels and ua: self.addMeasurementLabel("DISC_"+level,self.labelPoint(ua,occupied),level.replace("_","–")+"\n"+" | ".join(labels))
        if s.show_auxiliary_geometry:
            node=self.markupNodes.get(key)
            if node and node.GetDisplayNode(): node.GetDisplayNode().SetVisibility(True); node.GetDisplayNode().SetPointLabelsVisibility(True)
        return True
    def captureAnnotatedProjection(self,key,path):
        volume=self.selectors[key].currentNode()
        if volume is None or key not in self.markupNodes: return False
        slicer.util.setSliceViewerLayers(background=volume,fit=True)
        for projection,node in self.markupNodes.items():
            if node.GetDisplayNode(): node.GetDisplayNode().SetVisibility(False)
        self.buildMeasurementOverlays(key)
        widget=slicer.app.layoutManager().sliceWidget("Red")
        if not widget: return False
        pix=widget.grab(); image=pix.toImage(); painter=qt.QPainter(image); painter.setPen(qt.QColor("white")); font=painter.font(); font.setPointSize(14); font.setBold(True); painter.setFont(font)
        title={"lat":"NEUTRAL","flex":"FLEXION","ext":"EXTENSION"}[key]; painter.drawText(18,28,title); painter.end(); return image.save(path,"PNG")

    def generateDynamicComparison(self,directory):
        import os
        flex=os.path.join(directory,"Flexion_Annotated.png"); ext=os.path.join(directory,"Extension_Annotated.png")
        if not (os.path.exists(flex) and os.path.exists(ext)): return None
        a=qt.QImage(flex); b=qt.QImage(ext); boxHeight=150; out=qt.QImage(a.width()+b.width(),max(a.height(),b.height())+boxHeight,qt.QImage.Format_ARGB32); out.fill(qt.QColor("black"))
        painter=qt.QPainter(out); painter.drawImage(0,0,a); painter.drawImage(a.width(),0,b); painter.setPen(qt.QColor("white")); font=painter.font(); font.setPointSize(12); painter.setFont(font)
        lines=[]; settings=self.readVisualizationSettings("flex")
        for level in VisualizationSettings.LEVELS:
            if not (settings.show_IVA.get(level) or settings.show_translation.get(level)): continue
            parts=[level.replace("_","–")]
            dk="delta_IVA_"+level+"_deg"; dv=self.lastResults.get("dynamic",{}).get(dk)
            if settings.show_IVA.get(level) and dv is not None: parts.append("ΔIVA F–E: %.1f°" % dv)
            t=self.lastResults.get("translation",{}).get(level,{})
            if settings.show_translation.get(level) and t.get("delta_flex_ext_pct") is not None:
                if t.get("delta_flex_ext_mm") is not None: parts.append("ΔTranslation F–E: %.1f mm" % t["delta_flex_ext_mm"])
                parts.append("ΔTranslation F–E: %.1f%%" % t["delta_flex_ext_pct"])
            lines.append("   ".join(parts))
        painter.drawText(qt.QRect(20,max(a.height(),b.height())+10,out.width()-40,boxHeight-20),qt.Qt.AlignLeft|qt.Qt.AlignTop,"\n".join(lines)); painter.end()
        path=os.path.join(directory,"Dynamic_Comparison.png"); out.save(path,"PNG"); return path

    def generateFigure(self):
        import os
        self.calculateMeasurements()
        directory=qt.QFileDialog.getExistingDirectory(slicer.util.mainWindow(),"Guardar imágenes anotadas / Save annotated images")
        if not directory: return
        names={"lat":"Neutral_Annotated.png","flex":"Flexion_Annotated.png","ext":"Extension_Annotated.png"}
        for key,name in names.items():
            if self.selectors[key].currentNode() is not None and key in self.markupNodes: self.captureAnnotatedProjection(key,os.path.join(directory,name))
        if self.dynamicComparisonCheck.checked: self.generateDynamicComparison(directory)
        self.lastResults["visualization"]=self.readVisualizationSettings().toDict() if self.sameVisualizationCheck.checked else {key:self.visualizationSettings[key].toDict() for key in ("lat","flex","ext")}

class LumbarRadiographyLogic(ScriptedLoadableModuleLogic):
    DEFINITION_VERSION="1.5.2"
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
