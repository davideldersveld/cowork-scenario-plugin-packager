"""Prepare a demo .docx for packaging: fix tracked-change/comment attribution,
normalise dates, remove duplicate comments, strip signed-in-user identity,
and apply literal text replacements.

Usage:
  python sanitize_docx.py FILE.docx|xlsx|pptx [--core-author "Kit name"]
  python sanitize_docx.py FILE.docx [--author "Name"] [--initials XX]
      [--date 2026-09-29T14:30:00Z] [--keep-comment-prefix "Name (Firm):"]
      [--replace "old=>new" ...] [--report]

Edits the file in place. Prints a JSON report (tracked insertions/deletions,
authors, comments kept) so the result can be verified.
"""
import argparse, json, re, zipfile

ap = argparse.ArgumentParser()
ap.add_argument("file")
ap.add_argument("--author")
ap.add_argument("--initials")
ap.add_argument("--date")
ap.add_argument("--keep-comment-prefix")
ap.add_argument("--replace", action="append", default=[])
ap.add_argument("--core-author", help="set document creator/last-modified-by (any Office file)")
ap.add_argument("--report", action="store_true", help="report only, no changes")
a = ap.parse_args()

zin = zipfile.ZipFile(a.file)
infos = zin.infolist()
data = {i.filename: zin.read(i.filename) for i in infos}
zin.close()

def txt(n):
    return data[n].decode("utf-8") if n in data else None

is_docx = "word/document.xml" in data
if a.core_author and not a.report and "docProps/core.xml" in data:
    cp = txt("docProps/core.xml")
    cp = re.sub(r"(<(?:dc:)?creator>)[^<]*(</(?:dc:)?creator>)", r"\g<1>%s\g<2>" % a.core_author, cp)
    cp = re.sub(r"(<(?:cp:)?lastModifiedBy>)[^<]*(</(?:cp:)?lastModifiedBy>)", r"\g<1>%s\g<2>" % a.core_author, cp)
    data["docProps/core.xml"] = cp.encode()
if not is_docx:
    if not a.report:
        z = zipfile.ZipFile(a.file, "w", zipfile.ZIP_DEFLATED)
        for i in infos:
            z.writestr(i.filename, data[i.filename])
        z.close()
    print(json.dumps({"file": a.file, "core_props_only": True}))
    raise SystemExit(0)
doc = txt("word/document.xml")
com = txt("word/comments.xml")

def comments(c):
    out = []
    if not c:
        return out
    for m in re.finditer(r"<w:comment [^>]*>.*?</w:comment>", c, re.S):
        cid = re.search(r'w:id="([^"]+)"', m.group(0)).group(1)
        para = re.findall(r'w14:paraId="([^"]+)"', m.group(0))
        text = "".join(re.findall(r"<w:t[^>]*>([^<]*)</w:t>", m.group(0)))
        out.append({"id": cid, "paras": para, "text": text})
    return out

if not a.report:
    # 1. drop duplicate / unwanted comments
    if com and a.keep_comment_prefix:
        cs = comments(com)
        keep = [c for c in cs if c["text"].startswith(a.keep_comment_prefix)]
        keep_ids = {keep[0]["id"]} if keep else set()
        for c in cs:
            if c["id"] in keep_ids:
                continue
            i = re.escape(c["id"])
            com = re.sub(r'<w:comment [^>]*w:id="%s"[^>]*>.*?</w:comment>' % i, "", com, flags=re.S)
            doc = re.sub(r'<w:comment(?:RangeStart|RangeEnd) w:id="%s"\s*/>' % i, "", doc)
            doc = re.sub(r'<w:r>(?:(?!</w:r>).)*?<w:commentReference w:id="%s"\s*/>(?:(?!<w:r>).)*?</w:r>' % i, "", doc, flags=re.S)
            doc = re.sub(r'<w:commentReference w:id="%s"\s*/>' % i, "", doc)
            for n in ("word/commentsIds.xml", "word/commentsExtended.xml"):
                s = txt(n)
                if s:
                    for p in c["paras"]:
                        s = re.sub(r'\s*<w1[56]\w*:comment(?:Id|Ex) [^>]*%s[^>]*/>' % re.escape(p), "", s)
                    data[n] = s.encode()
    # 2. attribution and dates
    if a.author:
        doc = re.sub(r'w:author="[^"]*"', 'w:author="%s"' % a.author, doc)
        if com:
            com = re.sub(r'w:author="[^"]*"', 'w:author="%s"' % a.author, com)
        p = txt("word/people.xml")
        if p:
            p = re.sub(r'w15:author="[^"]*"', 'w15:author="%s"' % a.author, p)
            p = re.sub(r"\s*<w15:presenceInfo[^>]*/>", "", p)
            data["word/people.xml"] = p.encode()
    if a.initials and com:
        com = re.sub(r'w:initials="[^"]*"', 'w:initials="%s"' % a.initials, com)
    if a.date:
        doc = re.sub(r'(<w:(?:ins|del|rPrChange|pPrChange) [^>]*?)w:date="[^"]+"', r'\1w:date="%s"' % a.date, doc)
        if com:
            com = re.sub(r'w:date="[^"]+"', 'w:date="%s"' % a.date, com)
    # 3. literal replacements in every XML part (text runs only)
    for r in a.replace:
        old, new = r.split("=>", 1)
        for n in list(data):
            if n.endswith(".xml"):
                s = data[n].decode("utf-8")
                if old in s:
                    data[n] = s.replace(old, new).encode()
        doc = doc.replace(old, new)
        if com:
            com = com.replace(old, new)
    data["word/document.xml"] = doc.encode()
    if com is not None:
        data["word/comments.xml"] = com.encode()
    z = zipfile.ZipFile(a.file, "w", zipfile.ZIP_DEFLATED)
    for i in infos:
        z.writestr(i.filename, data[i.filename])
    z.close()

z = zipfile.ZipFile(a.file)
d = z.read("word/document.xml").decode()
c = z.read("word/comments.xml").decode() if "word/comments.xml" in z.namelist() else ""
print(json.dumps({
    "file": a.file,
    "insertions": len(re.findall(r"<w:ins ", d)),
    "deletions": len(re.findall(r"<w:del ", d)),
    "authors": sorted(set(re.findall(r'w:author="([^"]+)"', d + c))),
    "comments": [x["text"][:90] for x in comments(c)],
}, indent=1))
