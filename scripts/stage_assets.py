"""Stage a scenario demo kit's files into the session workspace.

Each sample file is stored in one of the plugin's asset skills as a flat text
file references/asset-NNN.json: {"folder", "name", "size", "sha256",
"encoding": "base64", "data"}. This script decodes every file listed in the
setup skill's references/asset-manifest.json into <dest>/<folder>/<name>,
checks size and SHA-256, and prints a JSON report.

Usage:
  python stage_assets.py <setup_skill_dir> <dest_dir> [<asset_skill_dir> ...]

Asset skill directories can be passed in any order (matched by folder name).
Any not passed are looked for as sibling folders of the setup skill, then by
searching under the setup skill's grandparent folder.
"""
import base64, hashlib, json, os, sys

if len(sys.argv) < 3:
    sys.exit(__doc__)
setup_dir, dest = sys.argv[1], sys.argv[2]
man = json.load(open(os.path.join(setup_dir, "references", "asset-manifest.json"), encoding="utf-8"))
dirs = {os.path.basename(os.path.normpath(d)): d for d in sys.argv[3:]}
parent = os.path.dirname(os.path.normpath(setup_dir))
for name in man["asset_skills"]:
    if name not in dirs and os.path.isdir(os.path.join(parent, name)):
        dirs[name] = os.path.join(parent, name)
if any(n not in dirs for n in man["asset_skills"]):
    root = os.path.dirname(parent)
    for r, ds, _ in os.walk(root):
        for d in ds:
            if d in man["asset_skills"] and d not in dirs:
                dirs[d] = os.path.join(r, d)

staged, missing, bad = [], [], []
for e in man["files"]:
    src_dir = dirs.get(e["asset_skill"])
    src = os.path.join(src_dir, e["stored_name"]) if src_dir else None
    label = f'{e["folder"]}/{e["name"]}'
    if not src or not os.path.isfile(src):
        missing.append(f'{label} (expected {e["asset_skill"]}/{e["stored_name"]})')
        continue
    doc = json.load(open(src, encoding="utf-8"))
    raw = base64.b64decode(doc["data"])
    if len(raw) != e["size"] or hashlib.sha256(raw).hexdigest() != e["sha256"]:
        bad.append(label)
        continue
    out_dir = os.path.join(dest, e["folder"])
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, e["name"]), "wb") as fh:
        fh.write(raw)
    staged.append(label)

print(json.dumps({
    "dest": dest,
    "expected": man["file_count"],
    "staged": len(staged),
    "missing": missing,
    "failed_checksum": bad,
    "asset_skills_found": {k: dirs[k] for k in sorted(dirs)},
    "folders": man["folder_order"],
}, indent=1))
sys.exit(1 if (missing or bad) else 0)
