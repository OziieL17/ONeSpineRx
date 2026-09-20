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
        "place":"Marcar punto", "skip":"Saltar", "finish":"Finalizar", "previous":"Anterior", "next":"Siguiente", "edit":"Modificar", "save":"Guardar cambios",
        "current":"Punto actual", "progress":"Progreso", "instructions":"Instrucciones",
        "noVolume":"Seleccione un volumen para esta proyección.",
        "ready":"Seleccione las cuatro proyecciones y pulse Iniciar registro en la proyección que desea medir.",
        "complete":"Registro finalizado. Revise los puntos antes de calcular o exportar.", "results":"Resultados", "calculate":"Calcular medidas", "copy":"Copiar valores", "figure":"Generar imagen",
        "skipped":"Omitido", "calibration":"Las distancias en mm requieren calibración espacial válida.",
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
        self.calibrationLabel=qt.QLabel(); self.calibrationLabel.wordWrap=True; self.layout.addWidget(self.calibrationLabel)
        self.resultsBox=qt.QGroupBox(); resultsLayout=qt.QVBoxLayout(self.resultsBox)
        resultButtons=qt.QHBoxLayout(); self.calculateButton=qt.QPushButton(); self.copyButton=qt.QPushButton(); self.figureButton=qt.QPushButton()
        resultButtons.addWidget(self.calculateButton); resultButtons.addWidget(self.copyButton); resultButtons.addWidget(self.figureButton); resultsLayout.addLayout(resultButtons)
        self.resultsText=qt.QTextEdit(); self.resultsText.readOnly=True; self.resultsText.minimumHeight=180; resultsLayout.addWidget(self.resultsText)
        self.layout.addWidget(self.resultsBox); self.lastResults={}
        self.calculateButton.connect("clicked()",self.calculateMeasurements); self.copyButton.connect("clicked()",self.copyResults); self.figureButton.connect("clicked()",self.generateFigure)
        self.previousButton.connect("clicked()",self.previousLandmark); self.nextButton.connect("clicked()",self.nextLandmark); self.skipButton.connect("clicked()",self.skipCurrent); self.editButton.connect("clicked()",self.editCurrent); self.saveButton.connect("clicked()",self.saveChanges); self.finishButton.connect("clicked()",self.finishRegistration)
        self.languageCombo.connect("currentIndexChanged(int)",self.changeLanguage)
        self.applyLanguage(); self.layout.addStretch(1)

    def cleanup(self): self.removeObservers()

    def tr(self,key): return TRANSLATIONS[self.lang].get(key,key)
    def changeLanguage(self,_index):
        self.lang=self.languageCombo.itemData(self.languageCombo.currentIndex); self.applyLanguage(); self.updateGuide()

    def applyLanguage(self):
        self.studyBox.title=self.tr("study"); self.landmarkBox.title=self.tr("landmarks"); self.validationBox.title=self.tr("validation"); self.resultsBox.title=self.tr("results")
        self.importButton.text=self.tr("importDicom"); self.categorizeButton.text=self.tr("categorize"); self.validateButton.text=self.tr("validate")
        for key in self.PROJECTION_KEYS:
            getattr(self,key+"Label").text=self.tr(key)
            getattr(self,key+"StartButton").text=self.tr("start")
        self.previousButton.text=self.tr("previous"); self.nextButton.text=self.tr("next"); self.skipButton.text=self.tr("skip"); self.editButton.text=self.tr("edit"); self.saveButton.text=self.tr("save"); self.finishButton.text=self.tr("finish")
        self.calibrationLabel.text=self.tr("calibration"); self.calculateButton.text=self.tr("calculate"); self.copyButton.text=self.tr("copy"); self.figureButton.text=self.tr("figure")
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
            node.GetDisplayNode().SetTextScale(0.7)
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

    def calculateMeasurements(self):
        results={}
        for key in ("lat","flex","ext"):
            p=self.pointMap(key); prefix=self.PREFIX[key]; r={}
            q=lambda name: p.get(prefix+" "+name)
            if all(q(x) for x in ("L1 SA","L1 SP","S1 SA","S1 SP")): r["LL_L1_S1_deg"]=self.angleBetween(q("L1 SA"),q("L1 SP"),q("S1 SA"),q("S1 SP"))
            if all(q(x) for x in ("L4 SA","L4 SP","S1 SA","S1 SP")): r["LL_L4_S1_deg"]=self.angleBetween(q("L4 SA"),q("L4 SP"),q("S1 SA"),q("S1 SP"))
            for upper,lower in zip(("L1","L2","L3","L4","L5"),("L2","L3","L4","L5","S1")):
                needed=(upper+" IA",upper+" IP",lower+" SA",lower+" SP")
                if all(q(x) for x in needed): r[upper+"-"+lower+"_disc_angle_deg"]=self.angleBetween(q(upper+" IA"),q(upper+" IP"),q(lower+" SA"),q(lower+" SP"))
            if key=="lat" and all(q(x) for x in ("S1 SA","S1 SP","FH_R_CENTER","FH_L_CENTER")):
                import math
                sa,sp=q("S1 SA"),q("S1 SP"); s=((sa[0]+sp[0])/2.0,(sa[1]+sp[1])/2.0)
                fr,fl=q("FH_R_CENTER"),q("FH_L_CENTER"); fh=((fr[0]+fl[0])/2.0,(fr[1]+fl[1])/2.0)
                dx,dy=sp[0]-sa[0],sp[1]-sa[1]; r["SS_deg"]=abs(math.degrees(math.atan2(dy,dx)))
                vx,vy=s[0]-fh[0],s[1]-fh[1]; r["PT_deg"]=abs(math.degrees(math.atan2(vx,vy)))
                nx,ny=-dy,dx; hx,hy=fh[0]-s[0],fh[1]-s[1]; r["PI_deg"]=abs(math.degrees(math.atan2(nx*hy-ny*hx,nx*hx+ny*hy)))
            results[key]=r
        dyn={}
        for name in set(results.get("flex",{})).intersection(results.get("ext",{})):
            if name.endswith("_deg"): dyn["delta_"+name]=abs(results["flex"][name]-results["ext"][name])
        results["dynamic"]=dyn; self.lastResults=results
        lines=[]
        for section,data in results.items():
            lines.append("["+section.upper()+"]"); lines.extend("%s = %.2f" % (name,value) for name,value in data.items()); lines.append("")
        self.resultsText.plainText="\\n".join(lines) if lines else ("No hay landmarks suficientes." if self.lang=="es" else "Insufficient landmarks.")

    def copyResults(self):
        if not self.lastResults: self.calculateMeasurements()
        qt.QApplication.clipboard().setText(json.dumps(self.lastResults,indent=2,ensure_ascii=False))

    def generateFigure(self):
        if not self.lastResults: self.calculateMeasurements()
        key="lat" if "lat" in self.markupNodes else self.activeProjection
        if not key or key not in self.markupNodes: slicer.util.errorDisplay("No hay una proyección registrada."); return
        volume=self.selectors[key].currentNode()
        if volume: slicer.util.setSliceViewerLayers(background=volume,fit=True)
        for projection,node in self.markupNodes.items():
            if node.GetDisplayNode(): node.GetDisplayNode().SetVisibility(projection==key)
        path=qt.QFileDialog.getSaveFileName(slicer.util.mainWindow(),"Guardar imagen / Save image","","PNG (*.png)")
        if not path: return
        if not path.lower().endswith(".png"): path+=".png"
        widget=slicer.app.layoutManager().sliceWidget("Red")
        if widget: widget.grab().save(path,"PNG")

class LumbarRadiographyLogic(ScriptedLoadableModuleLogic):
    DEFINITION_VERSION="1.2.0"
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
