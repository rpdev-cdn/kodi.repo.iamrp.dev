#!/usr/bin/env python3
import os
import hashlib
import xml.etree.ElementTree as ET

def main():
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    root = ET.Element("addons")
    for item in os.listdir(repo_root):
        item_path = os.path.join(repo_root, item)
        if os.path.isdir(item_path) and not item.startswith("."):
            xml_path = os.path.join(item_path, "addon.xml")
            if os.path.exists(xml_path):
                tree = ET.parse(xml_path)
                root.append(tree.getroot())
                
    tree = ET.ElementTree(root)
    ET.indent(tree, space="    ")
    xml_out = os.path.join(repo_root, "addons.xml")
    tree.write(xml_out, encoding="utf-8", xml_declaration=True)
    with open(xml_out, "rb") as f:
        md5_hash = hashlib.md5(f.read()).hexdigest()
    with open(os.path.join(repo_root, "addons.xml.md5"), "w", encoding="utf-8") as f:
        f.write(md5_hash + "\n")
    print(f"Refreshed addons.xml and addons.xml.md5: {md5_hash}")

if __name__ == "__main__":
    main()
