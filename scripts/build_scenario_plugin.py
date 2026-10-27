"""Build a Copilot Cowork scenario demo plugin from a spec, then validate it.

Usage:
  python build_scenario_plugin.py SPEC.json [--out OUTDIR]

SPEC.json (see references/spec-template.json) names:
  - the kit id, file prefix, titles, version, developer URLs and icon text
  - required skills (name, phases, purpose) and the plugin that provides them
  - folders -> files (paths relative to spec["assets_dir"])
  - phases (for the phase-order line) and seed-content / references locations

The scenario-specific references (scenario.md, phase-prompts.md, gates.md,
answer-key.md) are written by the author and copied from spec["references_dir"].
required-skills.md, asset-manifest.json, manifest.json, icons, the three
SKILL.md files and one or more <kit>-assets-N skills are generated. Each asset skill holds
flat references/asset-NNN.json files, one per sample file, with the file
base64-encoded plus its folder, original name and SHA-256. No binary
companion files and no archives are placed in the plugin (installed plugins
drop binary companions; nested archives are rejected). Output: OUTDIR/pkg (unzipped) and OUTDIR/<kit>.zip,
then validate_plugin.py runs on the zip. Exit code 1 if validation fails.
"""
import argparse, json, os, re, shutil, subprocess, sys, uuid, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
TPL = os.path.join(os.path.dirname(HERE), "templates")
ap = argparse.ArgumentParser(); ap.add_argument("spec"); ap.add_argument("--out", default=None)
a = ap.parse_args()
spec = json.load(open(a.spec, encoding="utf-8"))
base = os.path.dirname(os.path.abspath(a.spec))
def P(p): return p if os.path.isabs(p) else os.path.join(base, p)

kit = spec["kit_id"]
assert re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", kit) and len(kit) <= 52, "kit_id must be kebab-case, <=52 chars"
out = a.out or os.path.join(base, "build")
pkg = os.path.join(out, "pkg"); shutil.rmtree(pkg, ignore_errors=True)
sk = {r: os.path.join(pkg, "skills", f"{kit}-{r}") for r in ("demo", "setup", "reset")}
for r, d in sk.items(): os.makedirs(d, exist_ok=True)
os.makedirs(os.path.join(sk["demo"], "references")); os.makedirs(os.path.join(sk["setup"], "references"))
os.makedirs(os.path.join(sk["setup"], "scripts"))

# 1. assets as text payloads split across asset skills.
# Installed Cowork plugins keep text companion files (references/*.md, *.json)
# but binary companions (.docx, .xlsx, ...) were dropped on install, and nested
# archives are rejected. So every sample file is stored base64-encoded inside a
# flat references/asset-NNN.json file, and setup decodes it back to the original.
import base64, hashlib
SAFE = re.compile(r"[^A-Za-z0-9._ !-]")
folders = spec["folders"]; adir = P(spec["assets_dir"])
for k in folders:
    if SAFE.search(k): sys.exit(f"Folder name '{k}' has unsupported characters (use letters, digits, - _ . space !)")
listed = [f for fs in folders.values() for f in fs]
missing = [f for f in listed if not os.path.isfile(os.path.join(adir, f))]
if missing: sys.exit("Missing asset files: " + "; ".join(missing))
if any(f.lower().endswith((".zip", ".7z", ".rar", ".tar", ".gz")) for f in listed):
    sys.exit("Archives are not allowed inside the plugin; add the files themselves.")
prefixed = [f for f in listed if os.path.basename(f).startswith(spec["prefix"])]
per = int(spec.get("files_per_asset_skill", 18))
assert 1 <= per <= 19, "files_per_asset_skill must be 1-19 (20 companion files per skill, minus headroom)"
PER_FILE, PER_SKILL = 4_800_000, 9_500_000          # payload limits: 5 MB per file, 10 MB per skill
payloads = []
for n, (folder, f) in enumerate(((fo, f) for fo, fs in folders.items() for f in fs), 1):
    raw = open(os.path.join(adir, f), "rb").read()
    doc = {"kit": kit, "folder": folder, "name": os.path.basename(f), "size": len(raw),
           "sha256": hashlib.sha256(raw).hexdigest(), "encoding": "base64",
           "data": base64.b64encode(raw).decode("ascii")}
    txt = json.dumps(doc, ensure_ascii=False)
    if len(txt.encode()) > PER_FILE:
        sys.exit(f"{f} is too large to embed ({len(raw)} bytes; limit about 3.5 MB). Host it on SharePoint instead.")
    payloads.append((f"asset-{n:03d}.json", doc, txt))
parts, cur, cur_size = [], [], 0
for p in payloads:
    sz = len(p[2].encode())
    if cur and (len(cur) >= per or cur_size + sz > PER_SKILL):
        parts.append(cur); cur, cur_size = [], 0
    cur.append(p); cur_size += sz
if cur: parts.append(cur)
asset_skills = [f"{kit}-assets-{i}" for i in range(1, len(parts) + 1)]
man_files = []
for i, part in enumerate(parts):
    name = asset_skills[i]; rdir_a = os.path.join(pkg, "skills", name, "references")
    os.makedirs(rdir_a, exist_ok=True)
    for stored, doc, txt in part:
        open(os.path.join(rdir_a, stored), "w", encoding="utf-8").write(txt)
        man_files.append({"folder": doc["folder"], "name": doc["name"], "stored_name": "references/" + stored,
                          "asset_skill": name, "size": doc["size"], "sha256": doc["sha256"]})
man = {"kit": spec["title"], "version": spec["version"], "file_count": len(listed),
       "prefixed_file_count": len(prefixed), "storage": "base64-json", "asset_skills": asset_skills,
       "folder_order": list(folders), "files": man_files}
json.dump(man, open(os.path.join(sk["setup"], "references", "asset-manifest.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
seed = json.load(open(P(spec["seed_content"]), encoding="utf-8")) if spec.get("seed_content") else {"emails": [], "teams_messages": [], "calendar_events": []}
json.dump(seed, open(os.path.join(sk["setup"], "references", "seed-content.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
shutil.copy(os.path.join(HERE, "stage_assets.py"), os.path.join(sk["setup"], "scripts", "stage_assets.py"))

# 2. demo references
rdir = P(spec["references_dir"])
for f in ("scenario.md", "phase-prompts.md", "gates.md", "answer-key.md"):
    src = os.path.join(rdir, f)
    if not os.path.isfile(src): sys.exit(f"Missing reference {src}")
    shutil.copy(src, os.path.join(sk["demo"], "references", f))
req = spec["required_skills"]
lines = [f"# Required skills ({spec['required_plugin']} plugin)", "",
         f"All {len(req)} must be available before the demo runs. Names must match exactly (a plugin prefix is acceptable).", "",
         "| # | Skill name | Used in phase | Purpose in this scenario |", "|---|---|---|---|"]
lines += [f"| {i} | {r['name']} | {r['phases']} | {r['purpose']} |" for i, r in enumerate(req, 1)]
open(os.path.join(sk["demo"], "references", "required-skills.md"), "w", encoding="utf-8").write("\n".join(lines) + "\n")

# 3. SKILL.md files from templates
trig = "".join(f'"{t}", ' for t in spec.get("trigger_phrases", []))
V = {"KIT": kit, "TITLE": spec["title"], "SHORT_TITLE": spec.get("short_title", spec["title"]), "SUMMARY": spec["summary"], "REQUIRED_PLUGIN": spec["required_plugin"],
     "N_SKILLS": str(len(req)), "N_PHASES": str(len(spec["phases"])), "N_FILES": str(len(prefixed)),
     "PREFIX": spec["prefix"], "ROOT_FOLDER": spec["root_folder"], "AS_OF": spec["as_of"],
     "START_PHRASE": spec["start_phrase"], "TRIGGERS": trig, "KIT_AUTHOR": spec["kit_author"],
     "VERSION": spec["version"], "OUTPUT_MARKING": spec["output_marking"],
     "PHASE_ORDER": spec["phase_order"],
     "N_EMAILS": str(len(seed.get("emails", []))), "N_TEAMS": str(len(seed.get("teams_messages", []))),
     "N_EVENTS": str(len(seed.get("calendar_events", []))),
     "N_PARTS": str(len(asset_skills)), "ASSET_SKILL_LIST": ", ".join(f"`{n}`" for n in asset_skills)}
for r in ("demo", "setup", "reset"):
    t = open(os.path.join(TPL, f"{r}-SKILL.md"), encoding="utf-8").read()
    for k, v in V.items(): t = t.replace("{{" + k + "}}", v)
    left = re.findall(r"\{\{[A-Z_]+\}\}", t)
    if left: sys.exit(f"Unfilled placeholders in {r}: {left}")
    open(os.path.join(sk[r], "SKILL.md"), "w", encoding="utf-8").write(t)
at = open(os.path.join(TPL, "assets-SKILL.md"), encoding="utf-8").read()
for i, name in enumerate(asset_skills, 1):
    rows = [e for e in man_files if e["asset_skill"] == name]
    table = "| Folder | Original file name | Stored as |\n|---|---|---|\n" + "\n".join(f'| {e["folder"]} | {e["name"]} | {e["stored_name"]} |' for e in rows)
    t = at
    for k, v in dict(V, ASSET_SKILL=name, PART=str(i), N_PART_FILES=str(len(rows)), PART_FILE_TABLE=table).items():
        t = t.replace("{{" + k + "}}", v)
    left = re.findall(r"\{\{[A-Z_]+\}\}", t)
    if left: sys.exit(f"Unfilled placeholders in {name}: {left}")
    open(os.path.join(pkg, "skills", name, "SKILL.md"), "w", encoding="utf-8").write(t)

# 4. manifest + icons
pl = spec["plugin"]
m = {"$schema": "https://developer.microsoft.com/json-schemas/teams/v1.28/MicrosoftTeams.schema.json",
     "manifestVersion": "1.28", "version": spec["version"],
     "id": spec.get("app_id") or str(uuid.uuid5(uuid.NAMESPACE_URL, "cowork-scenario-plugin/" + kit)),
     "developer": pl["developer"], "name": {"short": pl["name_short"], "full": pl["name_full"]},
     "description": {"short": pl["desc_short"], "full": pl["desc_full"]},
     "icons": {"color": "color.png", "outline": "outline.png"}, "accentColor": pl.get("accent", "#14233C"),
     "agentSkills": [{"folder": f"./skills/{kit}-{r}"} for r in ("demo", "setup", "reset")] + [{"folder": f"./skills/{n}"} for n in asset_skills]}
if len(m["agentSkills"]) > 20: sys.exit("More than 20 skills; raise files_per_asset_skill or split the scenario")
json.dump(m, open(os.path.join(pkg, "manifest.json"), "w", encoding="utf-8"), indent=2, ensure_ascii=False)
from PIL import Image, ImageDraw, ImageFont
def font(sz):
    for p in ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf", "C:/Windows/Fonts/arialbd.ttf", "/Library/Fonts/Arial Bold.ttf"):
        try: return ImageFont.truetype(p, sz)
        except Exception: pass
    return ImageFont.load_default()
def hexrgb(h): h = h.lstrip("#"); return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
if pl.get("color_icon") and os.path.isfile(P(pl["color_icon"])):
    shutil.copy(P(pl["color_icon"]), os.path.join(pkg, "color.png"))
else:
    img = Image.new("RGB", (192, 192), hexrgb(pl.get("accent", "#14233C"))); d = ImageDraw.Draw(img)
    d.rectangle([0, 150, 192, 192], fill=hexrgb(pl.get("band", "#0F7C80")))
    for txt, sz, top, h in ((pl.get("icon_letter", "C"), 96, 0, 150), (pl.get("icon_label", "DEMO"), 26, 150, 42)):
        f = font(sz); b = d.textbbox((0, 0), txt, font=f)
        d.text(((192 - (b[2]-b[0])) / 2 - b[0], top + (h - (b[3]-b[1])) / 2 - b[1]), txt, font=f, fill="white")
    img.save(os.path.join(pkg, "color.png"))
if pl.get("outline_icon") and os.path.isfile(P(pl["outline_icon"])):
    shutil.copy(P(pl["outline_icon"]), os.path.join(pkg, "outline.png"))
else:
    o = Image.new("RGBA", (32, 32), (0, 0, 0, 0)); d = ImageDraw.Draw(o)
    d.rounded_rectangle([1, 1, 30, 30], radius=5, outline=(255, 255, 255, 255), width=2)
    f = font(18); txt = pl.get("icon_letter", "C"); b = d.textbbox((0, 0), txt, font=f)
    d.text(((32 - (b[2]-b[0])) / 2 - b[0], (32 - (b[3]-b[1])) / 2 - b[1]), txt, font=f, fill=(255, 255, 255, 255))
    o.save(os.path.join(pkg, "outline.png"))

# 5. zip (files at root) + validate
zpath = os.path.join(out, f"{kit}-plugin.zip")
if os.path.exists(zpath): os.remove(zpath)
with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
    for root, _, files in os.walk(pkg):
        for f in sorted(files):
            full = os.path.join(root, f); z.write(full, os.path.relpath(full, pkg).replace(os.sep, "/"))
print(f"Built {zpath}")
rc = subprocess.call([sys.executable, os.path.join(HERE, "validate_plugin.py"), zpath])
sys.exit(rc)
