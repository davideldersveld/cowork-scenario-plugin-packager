"""Validate a Copilot Cowork plugin .zip offline against the documented rules
(manifest v1.28 fields, icons, ASKILL-M/P codes, companion-file limits,
safe file names, no nested archives, text-only companion files).
Usage: python validate_plugin.py PLUGIN.zip   (exit 1 on errors)
"""
import json, os, re, sys, zipfile, io
from PIL import Image
pkg = sys.argv[1]
TEXT_EXT = (".md", ".txt", ".json", ".py", ".csv", ".yaml", ".yml", ".ps1", ".sh", ".js", ".ts", ".xml")
z = zipfile.ZipFile(pkg); names = z.namelist(); errs = []; warns = []
def E(c, m): errs.append(f"{c}: {m}")
if "manifest.json" not in names: E("PKG", "manifest.json missing at root")
for n in names:
    if n.lower().endswith((".zip", ".7z", ".rar", ".tar", ".gz", ".tgz")): E("NESTED-ARCHIVE", f"{n}: no archives inside the plugin zip")
m = json.loads(z.read("manifest.json"))
allowed = {"$schema","manifestVersion","version","id","developer","name","description","icons","accentColor","agentSkills","agentConnectors","localizationInfo"}
for k in m:
    if k not in allowed: E("SCHEMA", f"root field '{k}' not in the documented skills-plugin manifest")
for k in ["$schema","manifestVersion","version","id","developer","name","description","icons","accentColor"]:
    if k not in m: E("SCHEMA", f"missing {k}")
if m.get("manifestVersion") != "1.28": E("SCHEMA", "manifestVersion should be 1.28")
if not re.fullmatch(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", m.get("id","")): E("SCHEMA","id not a GUID")
if not re.fullmatch(r"\d+\.\d+\.\d+", m.get("version","")): E("SCHEMA","version not semver")
for k in ["name","websiteUrl","privacyUrl","termsOfUseUrl"]:
    v = m["developer"].get(k)
    if not v: E("SCHEMA", f"developer.{k} missing")
    elif k != "name" and not v.startswith("https://"): E("SCHEMA", f"developer.{k} must be https")
if len(m["name"]["short"]) > 30: E("SCHEMA","name.short > 30")
if len(m["name"].get("full","")) > 100: E("SCHEMA","name.full > 100")
if len(m["description"]["short"]) > 80: E("SCHEMA","description.short > 80")
if len(m["description"]["full"]) > 4000: E("SCHEMA","description.full > 4000")
if not re.fullmatch(r"#[0-9A-Fa-f]{6}", m["accentColor"]): E("SCHEMA","accentColor")
for key, size in [("color",(192,192)),("outline",(32,32))]:
    f = m["icons"][key]
    if f not in names: E("PKG", f"icon {f} missing")
    else:
        im = Image.open(io.BytesIO(z.read(f)))
        if im.size != size: E("PKG", f"{f} is {im.size}, expected {size}")
        if key == "outline":
            rgba = im.convert("RGBA"); px = [rgba.getpixel((x, y)) for x in range(rgba.width) for y in range(rgba.height)]; px = [p for p in px if p[3] > 0]
            if any(p[:3] != (255,255,255) for p in px): warns.append("outline.png has non-white pixels")
skills = m.get("agentSkills", [])
if len(skills) > 20: E("ASKILL-M002","more than 20 skills")
folders = []
for s in skills:
    f = s.get("folder")
    if not f: E("ASKILL-M001","folder missing"); continue
    if len(f) > 256: E("ASKILL-M003", f)
    if f in folders: E("ASKILL-P008", f"duplicate {f}")
    folders.append(f)
    base = f[2:] if f.startswith("./") else f
    if not any(n.startswith(base + "/") for n in names): E("ASKILL-P001", f"{f} not in zip"); continue
    sk = base + "/SKILL.md"
    if sk not in names: E("ASKILL-P002", f"{sk} missing"); continue
    txt = z.read(sk).decode("utf-8")
    fm = re.match(r"^---\r?\n(.*?)\r?\n---\r?\n", txt, re.S)
    if not fm: E("ASKILL-P003", f"{sk} frontmatter"); continue
    nm = re.search(r"^name:\s*(\S+)\s*$", fm.group(1), re.M)
    if not nm: E("ASKILL-P004", sk); continue
    dm = re.search(r"^description:\s*(\|?)\s*\n?(.*?)(?=^\w[\w-]*:|\Z)", fm.group(1), re.M | re.S)
    if not dm: E("ASKILL-P005", sk)
    else:
        desc = " ".join(l.strip() for l in dm.group(2).splitlines()).strip()
        if not 1 <= len(desc) <= 1024: E("ASKILL-P005", f"{sk} description length {len(desc)}")
    name = nm.group(1)
    if name != base.split("/")[-1]: E("ASKILL-P006", f"{name} != folder")
    if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", name) or len(name) > 64: E("ASKILL-P007", name)
    body = txt[fm.end():]; words = len(body.split())
    if words > 3000: warns.append(f"{sk} body {words} words (>3000)")
    comps = [n for n in names if n.startswith(base + "/") and not n.endswith("/") and n != sk]
    if len(comps) > 20: E("COMPANION", f"{base}: {len(comps)} companion files > 20")
    tot = 0
    for c in comps:
        sz = z.getinfo(c).file_size; tot += sz
        rel = c[len(base)+1:]
        if sz > 5*1024*1024: E("COMPANION", f"{c} > 5 MB")
        if c.lower().endswith((".zip", ".7z", ".rar", ".tar", ".gz", ".tgz")): E("NESTED-ARCHIVE", f"{c}: archives inside the plugin are not allowed")
        if not c.lower().endswith(TEXT_EXT): E("BINARY-COMPANION", f"{c}: binary companion files are dropped when the plugin is installed; store as base64 JSON in references/")
        if ".." in rel.split("/") or "\\" in rel or rel.startswith("/"): E("COMPANION", f"bad path {c}")
        for part in rel.split("/"):
            if part.startswith("."): E("COMPANION", f"hidden {c}")
            if re.fullmatch(r"(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(\..*)?", part, re.I): E("COMPANION", f"reserved {c}")
            if not re.fullmatch(r"[A-Za-z0-9._ !-]+", part): E("COMPANION", f"unsafe chars {c}")
        if rel.startswith("references/") and not rel.split("/")[-1].startswith("asset-") and rel.split("/")[-1] not in body: warns.append(f"{c} not referenced in SKILL.md")
    if tot > 10*1024*1024: E("COMPANION", f"{base}: total {tot} > 10 MB")
    print(f"skill {name}: {len(comps)} companions, {tot/1024:.0f} KB, body {words} words")
print(json.dumps({"errors": errs, "warnings": warns, "files": len(names)}, indent=1))
sys.exit(1 if errs else 0)
