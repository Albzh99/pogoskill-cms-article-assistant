import argparse
import json
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET


NS = {
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "pr": "http://schemas.openxmlformats.org/package/2006/relationships",
}


def qname(prefix, name):
    return f"{{{NS[prefix]}}}{name}"


def node_text(node):
    return "".join(part.text or "" for part in node.findall(".//w:t", NS)).strip()


def paragraph_record(node, rels):
    style_node = node.find("./w:pPr/w:pStyle", NS)
    style = style_node.get(qname("w", "val")) if style_node is not None else ""
    image_targets = []
    for blip in node.findall(".//a:blip", NS):
        rel_id = blip.get(qname("r", "embed"))
        if rel_id and rel_id in rels:
            image_targets.append(rels[rel_id])
    return {
        "type": "paragraph",
        "style": style,
        "text": node_text(node),
        "images": image_targets,
    }


def table_record(node):
    rows = []
    for tr in node.findall("./w:tr", NS):
        cells = []
        for tc in tr.findall("./w:tc", NS):
            cells.append("\n".join(filter(None, (node_text(p) for p in tc.findall("./w:p", NS)))))
        rows.append(cells)
    return {"type": "table", "rows": rows}


def inspect(docx_path):
    with zipfile.ZipFile(docx_path) as archive:
        document = ET.fromstring(archive.read("word/document.xml"))
        rel_xml = ET.fromstring(archive.read("word/_rels/document.xml.rels"))
        rels = {
            rel.get("Id"): rel.get("Target")
            for rel in rel_xml.findall("./pr:Relationship", NS)
            if rel.get("Id") and rel.get("Target")
        }
        body = document.find("./w:body", NS)
        blocks = []
        for child in list(body):
            if child.tag == qname("w", "p"):
                record = paragraph_record(child, rels)
                if record["text"] or record["images"]:
                    blocks.append(record)
            elif child.tag == qname("w", "tbl"):
                blocks.append(table_record(child))
        return {"source": str(docx_path), "blocks": blocks}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("docx")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    payload = inspect(Path(args.docx).resolve())
    output = Path(args.out).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()
