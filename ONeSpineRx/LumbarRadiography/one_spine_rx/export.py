from __future__ import annotations
import csv, json
import xml.etree.ElementTree as ET
from pathlib import Path

def export_json(path, payload):
    Path(path).write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

def export_text(path, text):
    Path(path).write_text(text, encoding="utf-8")

def export_csv(path, rows):
    rows=list(rows)
    if not rows:
        Path(path).write_text("", encoding="utf-8"); return
    with open(path,"w",newline="",encoding="utf-8") as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0].keys()))
        writer.writeheader(); writer.writerows(rows)

def _xml(parent,key,value):
    e=ET.SubElement(parent,str(key))
    if isinstance(value,dict):
        for k,v in value.items(): _xml(e,k,v)
    elif isinstance(value,(list,tuple)):
        for item in value: _xml(e,"item",item)
    elif value is not None: e.text=str(value)

def export_xml(path,payload):
    root=ET.Element("ONeSpineRx")
    for k,v in payload.items(): _xml(root,k,v)
    ET.ElementTree(root).write(path,encoding="utf-8",xml_declaration=True)
