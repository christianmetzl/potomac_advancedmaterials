"""Render the committed Phase 3 docx to a submission PDF (single source = the docx, no drift).

LibreOffice cannot load the docx-js output in this environment, but Chromium is available. This parses
word/document.xml from EIGENNEXUS_Phase3_Content.docx (paragraphs, runs with bold/italic/color, tables,
embedded figures) into styled HTML (11pt Times New Roman, single-spaced, 1in margins), then prints it to
PDF headless via Chromium. Output: EIGENNEXUS_Phase3_Writeup.pdf (the write-up; the official cover page
is prepended separately by the team, per GIC rules).

Run: python paper/build_pdf.py
"""
import os, sys, zipfile, subprocess, html, xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
DOCX = os.path.join(HERE, "EIGENNEXUS_Phase3_Content.docx")
HTML = os.path.join(HERE, "_phase3_writeup.html")
PDF = os.path.join(HERE, "EIGENNEXUS_Phase3_Writeup.pdf")
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


def runs_html(p):
    out = []
    for r in p.findall(f"{W}r"):
        rpr = r.find(f"{W}rPr")
        b = rpr is not None and rpr.find(f"{W}b") is not None
        i = rpr is not None and rpr.find(f"{W}i") is not None
        col = None
        if rpr is not None:
            c = rpr.find(f"{W}color")
            if c is not None:
                col = c.get(f"{W}val")
        txt = "".join(t.text or "" for t in r.findall(f"{W}t"))
        if not txt:
            if r.find(f".//{W}drawing") is not None:
                out.append("\x00IMG\x00")
            continue
        s = html.escape(txt)
        if b:
            s = f"<b>{s}</b>"
        if i:
            s = f"<i>{s}</i>"
        if col and col.lower() not in ("000000", "auto"):
            s = f'<span style="color:#{col}">{s}</span>'
        out.append(s)
    return "".join(out)


def para_html(p, imgs):
    pPr = p.find(f"{W}pPr")
    jc = None
    brk = False
    if pPr is not None:
        j = pPr.find(f"{W}jc")
        if j is not None:
            jc = j.get(f"{W}val")
        brk = pPr.find(f"{W}pageBreakBefore") is not None
    txt = "".join(t.text or "" for t in p.findall(f".//{W}t"))
    inner = runs_html(p)
    # image placeholder substitution (in document order)
    while "\x00IMG\x00" in inner:
        src = imgs.pop(0) if imgs else ""
        inner = inner.replace("\x00IMG\x00", f'<img src="{src}" style="max-width:62%;display:block;margin:6px auto"/>', 1)
    if not inner.strip():
        return ""
    align = f"text-align:{ {'center':'center','right':'right'}.get(jc,'left') }"
    if brk or txt.strip() == "References":
        align += ";page-break-before:always"
    # crude heading detection: short, fully-bold, numbered section
    sz = None
    rpr0 = p.find(f"{W}r/{W}rPr/{W}sz")
    if rpr0 is not None:
        sz = int(rpr0.get(f"{W}val"))
    if sz and sz >= 24 and jc == "center":
        return f'<h1 style="{align}">{inner}</h1>'
    if txt[:3].rstrip().rstrip(".").isdigit() and len(txt) < 70 and "<b>" in inner and inner.count("<b>") == 1 and inner.strip().startswith("<b>"):
        return f'<h3 style="{align}">{inner}</h3>'
    return f'<p style="{align};margin:0 0 6px 0">{inner}</p>'


def table_html(tbl):
    rows = []
    for tr in tbl.findall(f"{W}tr"):
        cells = []
        for tc in tr.findall(f"{W}tc"):
            txt = "".join(runs_html(p) for p in tc.findall(f"{W}p"))
            shd = tc.find(f".//{W}shd")
            hdr = shd is not None and (shd.get(f"{W}fill", "FFFFFF").upper() not in ("FFFFFF", "AUTO"))
            tag = "th" if hdr else "td"
            cells.append(f'<{tag}>{txt}</{tag}>')
        rows.append("<tr>" + "".join(cells) + "</tr>")
    return '<table>' + "".join(rows) + "</table>"


def main():
    z = zipfile.ZipFile(DOCX)
    media = sorted([n for n in z.namelist() if n.startswith("word/media/")])
    imgs = []
    for m in media:
        ext = os.path.splitext(m)[1]
        outp = os.path.join(HERE, "_img" + str(len(imgs)) + ext)
        open(outp, "wb").write(z.read(m))
        imgs.append(os.path.basename(outp))
    root = ET.fromstring(z.read("word/document.xml"))
    body = root.find(f"{W}body")
    parts = []
    for el in body:
        if el.tag == f"{W}p":
            parts.append(para_html(el, imgs))
        elif el.tag == f"{W}tbl":
            parts.append(table_html(el))
    css = """
    @page { size: Letter; margin: 0.8in; }
    body { font-family: 'Times New Roman', Times, serif; font-size: 11pt; line-height: 1.0; color:#000; }
    h1 { font-size: 13pt; margin: 0 0 2px 0; }
    h3 { font-size: 11pt; margin: 4px 0 2px 0; }
    p { orphans: 2; widows: 2; margin: 0 0 3px 0; }
    table { border-collapse: collapse; width: 100%; font-size: 10pt; margin: 3px 0 6px 0; }
    th, td { border: 1px solid #888; padding: 1px 5px; text-align: center; }
    th { background: #D5E8F0; }
    img { page-break-inside: avoid; }
    """
    doc = f"<!doctype html><html><head><meta charset='utf-8'><style>{css}</style></head><body>{''.join(parts)}</body></html>"
    open(HTML, "w").write(doc)
    subprocess.run([CHROME, "--headless", "--no-sandbox", "--disable-gpu",
                    "--no-pdf-header-footer", f"--print-to-pdf={PDF}", "file://" + HTML],
                   capture_output=True, timeout=120)
    import fitz
    print(f"wrote {PDF}: {fitz.open(PDF).page_count} pages")


if __name__ == "__main__":
    main()
