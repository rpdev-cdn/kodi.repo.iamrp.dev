#!/usr/bin/env python3
import os
import sys
import shutil
import hashlib
import datetime
import xml.etree.ElementTree as ET

def format_nginx_entry(name, is_dir, size_bytes=0, mtime=None):
    if mtime is None:
        dt_str = datetime.datetime.now().strftime("%d-%b-%Y %H:%M")
    else:
        dt_str = datetime.datetime.fromtimestamp(mtime).strftime("%d-%b-%Y %H:%M")

    display_name = name + ("/" if is_dir and not name.endswith("/") else "")
    link = display_name
    padding = max(1, 55 - len(display_name))
    size_str = "-" if is_dir else str(size_bytes)
    size_padding = max(1, 20 - len(size_str))
    return f'<a href="{link}">{display_name}</a>' + (" " * padding) + dt_str + (" " * size_padding) + size_str

def generate_subfolder_index(folder_path, rel_folder_name):
    entries = []
    # Parent directory link
    entries.append('<a href="../">../</a>')

    items = sorted(os.listdir(folder_path))
    for item in items:
        if item == "index.html" or item.startswith("."):
            continue
        item_path = os.path.join(folder_path, item)
        is_dir = os.path.isdir(item_path)
        stat = os.stat(item_path)
        entries.append(format_nginx_entry(item, is_dir, stat.st_size, stat.st_mtime))

    content = f"""<!DOCTYPE html>
<html>
<head>
    <title>Index of /{rel_folder_name}/</title>
</head>
<body>
<h1>Index of /{rel_folder_name}/</h1>
<hr>
<pre>
""" + "\n".join(entries) + """
</pre>
<hr>
</body>
</html>
"""
    out_file = os.path.join(folder_path, "index.html")
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Generated subfolder index: {rel_folder_name}/index.html")

def build_root_index(repo_root, addons_meta, root_autoindex_entries, repo_zip_name):
    # Construct rows for human browser table
    table_rows = []
    for meta in sorted(addons_meta, key=lambda x: x["name"]):
        table_rows.append(f"""                    <tr>
                        <td><strong>{meta['name']}</strong><br><small style="color:#8b949e;">{meta['id']}</small></td>
                        <td>{meta['provider']}</td>
                        <td><span class="badge">v{meta['version']}</span></td>
                        <td>{meta['summary']}</td>
                        <td><a href="{meta['id']}/" class="btn btn-sm">Browse Folder</a></td>
                    </tr>""")

    tbody = "\n".join(table_rows)
    autoindex_block = "\n".join(root_autoindex_entries)

    content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RPDevs Kodi Add-on Repository</title>
    <link rel="icon" type="image/png" href="logo.png">
    <style>
        :root {{
            --bg: #0d1117;
            --surface: #161b22;
            --border: #30363d;
            --text: #c9d1d9;
            --heading: #f0f6fc;
            --accent: #58a6ff;
            --accent-hover: #1f6feb;
            --badge: #238636;
            --code-bg: #090d13;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background-color: var(--bg);
            color: var(--text);
            margin: 0;
            padding: 2rem 1rem;
            display: flex;
            justify-content: center;
        }}
        .container {{
            max-width: 900px;
            width: 100%;
        }}
        header {{
            border-bottom: 1px solid var(--border);
            padding-bottom: 1.5rem;
            margin-bottom: 2rem;
        }}
        h1 {{
            color: var(--heading);
            font-size: 2rem;
            margin: 0 0 0.5rem 0;
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }}
        p.subtitle {{
            margin: 0;
            color: #8b949e;
            font-size: 1.05rem;
        }}
        .card {{
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
        }}
        .card h2 {{
            margin-top: 0;
            color: var(--heading);
            font-size: 1.3rem;
        }}
        .install-box {{
            background: var(--code-bg);
            border: 1px solid var(--border);
            border-radius: 6px;
            padding: 1rem;
            font-family: "JetBrains Mono", ui-monospace, monospace;
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin: 1rem 0;
            color: #79c0ff;
            word-break: break-all;
        }}
        .btn {{
            background: var(--accent);
            color: #ffffff;
            padding: 0.6rem 1.2rem;
            border-radius: 6px;
            text-decoration: none;
            font-weight: 600;
            display: inline-block;
            transition: background 0.15s ease;
        }}
        .btn:hover {{
            background: var(--accent-hover);
        }}
        .btn-sm {{
            padding: 0.35rem 0.75rem;
            font-size: 0.85rem;
        }}
        pre.autoindex {{
            background: var(--code-bg);
            border: 1px solid var(--border);
            border-radius: 6px;
            padding: 1.2rem;
            font-family: "JetBrains Mono", ui-monospace, monospace;
            font-size: 0.9rem;
            overflow-x: auto;
            color: var(--text);
            line-height: 1.5;
        }}
        pre.autoindex a {{
            color: var(--accent);
            text-decoration: none;
        }}
        pre.autoindex a:hover {{
            text-decoration: underline;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 1rem;
        }}
        th, td {{
            text-align: left;
            padding: 0.75rem;
            border-bottom: 1px solid var(--border);
        }}
        th {{
            color: var(--heading);
            font-weight: 600;
        }}
        .badge {{
            background: var(--badge);
            color: #fff;
            padding: 0.2rem 0.5rem;
            border-radius: 12px;
            font-size: 0.75rem;
            font-weight: 600;
        }}
        footer {{
            margin-top: 3rem;
            text-align: center;
            font-size: 0.85rem;
            color: #8b949e;
            border-top: 1px solid var(--border);
            padding-top: 1.5rem;
        }}
        footer a {{
            color: var(--accent);
            text-decoration: none;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div style="display: flex; align-items: center; gap: 1.25rem;">
                <img src="logo.png" alt="RPDevs Logo" style="width: 72px; height: 72px; border-radius: 12px; object-fit: contain;">
                <div>
                    <h1 style="margin: 0; font-size: 2rem;">RPDevs Kodi Add-on Repository</h1>
                    <p class="subtitle" style="margin-top: 0.25rem;">Official distribution point for first-party streaming resolvers, anime scrapers, and entertainment utilities.</p>
                </div>
            </div>
        </header>

        <div class="card">
            <h2>🎯 How to Install in Kodi</h2>
            <p><strong>Step-by-step Kodi File Manager installation:</strong></p>
            <ol>
                <li>In Kodi, open <strong>Settings</strong> (gear icon) &rarr; <strong>File Manager</strong>.</li>
                <li>Select <strong>Add source</strong>, click <code>&lt;None&gt;</code>, and enter this exact URL:</li>
            </ol>
            <div class="install-box">
                <span>https://kodi.repo.iamrp.dev/</span>
            </div>
            <ol start="3">
                <li>Name the media source <strong>RPDevs</strong> and click <strong>OK</strong>.</li>
                <li>Go back to Kodi home &rarr; <strong>Add-ons</strong> &rarr; <strong>Install from zip file</strong> (enable Unknown Sources if prompted).</li>
                <li>Select <strong>RPDevs</strong> &rarr; <strong>{repo_zip_name}</strong>.</li>
            </ol>
            
            <p style="margin-top: 1.5rem;"><strong>Direct Browser Download:</strong></p>
            <p>Download the installer zip directly to install via USB drive or network share:</p>
            <a href="{repo_zip_name}" class="btn">⬇️ Download Installer ({repo_zip_name})</a>
        </div>

        <div class="card">
            <h2>📂 Kodi Repository File Index</h2>
            <p style="font-size: 0.9rem; color: #8b949e; margin-top: -0.5rem;">
                Standard HTTP autoindex recognized by Kodi's built-in file browser engine (<code>CHTTPDirectory</code>).
            </p>
            <pre class="autoindex">
{autoindex_block}
            </pre>
        </div>

        <div class="card">
            <h2>📦 First-Party Add-ons Included in Manifest</h2>
            <table>
                <thead>
                    <tr>
                        <th>Add-on</th>
                        <th>Provider</th>
                        <th>Version</th>
                        <th>Summary</th>
                        <th>Folder</th>
                    </tr>
                </thead>
                <tbody>
{tbody}
                </tbody>
            </table>
        </div>

        <footer>
            <p>Part of the <a href="https://iamrp.dev">RPDev Sovereign Ecosystem</a> &bull; Documentation at <a href="https://wiki.iamrp.dev">wiki.iamrp.dev</a> &bull; Source on <a href="https://github.com/rpdev-cdn/kodi.repo.iamrp.dev">GitHub</a></p>
        </footer>
    </div>
</body>
</html>
"""
    out_file = os.path.join(repo_root, "index.html")
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(content)
    print("Generated root index: index.html")

def main():
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    root_element = ET.Element("addons")
    addons_meta = []
    repo_dirs = []
    repo_zip_name = "repository.rpdevs-1.0.0.zip"

    # 1. Scan addon directories and build addons.xml
    for item in sorted(os.listdir(repo_root)):
        item_path = os.path.join(repo_root, item)
        if os.path.isdir(item_path) and not item.startswith(".") and item != "tools":
            xml_path = os.path.join(item_path, "addon.xml")
            if os.path.exists(xml_path):
                repo_dirs.append(item)
                try:
                    tree = ET.parse(xml_path)
                    addon_elem = tree.getroot()
                    root_element.append(addon_elem)

                    addon_id = addon_elem.get("id", item)
                    addon_name = addon_elem.get("name", item)
                    addon_version = addon_elem.get("version", "1.0.0")
                    addon_provider = addon_elem.get("provider-name", "RPDev")
                    
                    summary = ""
                    meta_elem = addon_elem.find("extension[@point='xbmc.addon.metadata']")
                    if meta_elem is not None:
                        summary_elem = meta_elem.find("summary")
                        if summary_elem is not None and summary_elem.text:
                            summary = summary_elem.text.strip()
                        elif meta_elem.find("description") is not None:
                            summary = meta_elem.find("description").text.strip()
                    
                    addons_meta.append({
                        "id": addon_id,
                        "name": addon_name,
                        "version": addon_version,
                        "provider": addon_provider,
                        "summary": summary
                    })

                    # If this is repository.rpdevs, sync its zip to repo root
                    if item == "repository.rpdevs":
                        zip_candidate = f"{addon_id}-{addon_version}.zip"
                        sub_zip = os.path.join(item_path, zip_candidate)
                        root_zip = os.path.join(repo_root, zip_candidate)
                        repo_zip_name = zip_candidate
                        if os.path.exists(sub_zip) and not os.path.exists(root_zip):
                            shutil.copy2(sub_zip, root_zip)
                            print(f"Synced {zip_candidate} to repo root.")

                    # Generate subfolder index.html
                    generate_subfolder_index(item_path, item)

                except Exception as e:
                    print(f"Error processing {xml_path}: {e}", file=sys.stderr)

    # 2. Write addons.xml and addons.xml.md5
    tree = ET.ElementTree(root_element)
    ET.indent(tree, space="    ")
    xml_out = os.path.join(repo_root, "addons.xml")
    tree.write(xml_out, encoding="utf-8", xml_declaration=True)

    with open(xml_out, "rb") as f:
        md5_hash = hashlib.md5(f.read()).hexdigest()
    with open(os.path.join(repo_root, "addons.xml.md5"), "w", encoding="utf-8") as f:
        f.write(md5_hash + "\n")
    print(f"Refreshed addons.xml and addons.xml.md5: {md5_hash}")

    # 3. Construct root autoindex listing for Kodi
    autoindex_entries = []

    # First list root zip files (e.g. repository.rpdevs-1.0.0.zip) so it appears at the very top for users!
    for f in sorted(os.listdir(repo_root)):
        if f.endswith(".zip"):
            f_path = os.path.join(repo_root, f)
            stat = os.stat(f_path)
            autoindex_entries.append(format_nginx_entry(f, False, stat.st_size, stat.st_mtime))

    # Next list manifest files
    for m in ["addons.xml", "addons.xml.md5"]:
        m_path = os.path.join(repo_root, m)
        if os.path.exists(m_path):
            stat = os.stat(m_path)
            autoindex_entries.append(format_nginx_entry(m, False, stat.st_size, stat.st_mtime))

    # Then list addon folders
    for d in repo_dirs:
        d_path = os.path.join(repo_root, d)
        stat = os.stat(d_path)
        autoindex_entries.append(format_nginx_entry(d, True, stat.st_size, stat.st_mtime))

    # 4. Write root index.html
    build_root_index(repo_root, addons_meta, autoindex_entries, repo_zip_name)
    print("Done! Repository structure and indices fully regenerated.")

if __name__ == "__main__":
    main()
