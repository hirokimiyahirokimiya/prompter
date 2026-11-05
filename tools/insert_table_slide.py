# Insert a new slide (eyebrow + title + table + small references + speaker notes) after a given slide,
# reusing that slide's background, accent bar and eyebrow style.
# usage: python3 tools/insert_table_slide.py in.pptx out.pptx spec.json
# spec: {"after": 21, "eyebrow": "考察 / DISCUSSION", "title": "...", "header": [...], "rows": [[...], ...],
#        "highlight_row": 3, "col_widths": [emu,...], "refs": "...", "notes": "..."}
import zipfile, sys, os, json, copy, re
from xml.sax.saxutils import escape
from lxml import etree
P='http://schemas.openxmlformats.org/presentationml/2006/main'
A='http://schemas.openxmlformats.org/drawingml/2006/main'
R='http://schemas.openxmlformats.org/officeDocument/2006/relationships'
PR='http://schemas.openxmlformats.org/package/2006/relationships'
CT='http://schemas.openxmlformats.org/package/2006/content-types'
NS={'p':P,'a':A}
src, dst, specf = sys.argv[1:4]
spec = json.load(open(specf))
z = zipfile.ZipFile(src); names = set(z.namelist())
files = {}
def get(n): return files[n] if n in files else z.read(n)
pres = etree.fromstring(get('ppt/presentation.xml'))
prels = etree.fromstring(get('ppt/_rels/presentation.xml.rels'))
rid2t = {r.get('Id'): r.get('Target') for r in prels}
lst = pres.find('p:sldIdLst', NS)
ids = list(lst)
base = ids[spec['after'] - 1]
base_path = 'ppt/' + rid2t[base.get('{%s}id' % R)]
base_rels = etree.fromstring(get(base_path.replace('slides/', 'slides/_rels/') + '.rels'))
layout = next(r.get('Target') for r in base_rels if r.get('Type').endswith('/slideLayout'))
notes_src = next(os.path.normpath(os.path.join('ppt/slides', r.get('Target'))) for r in base_rels if r.get('Type').endswith('/notesSlide'))
# new part names
sn = max(int(m.group(1)) for n in names for m in [re.match(r'ppt/slides/slide(\d+)\.xml$', n)] if m) + 1
nn = max(int(m.group(1)) for n in names for m in [re.match(r'ppt/notesSlides/notesSlide(\d+)\.xml$', n)] if m) + 1
slide_path, notes_path = f'ppt/slides/slide{sn}.xml', f'ppt/notesSlides/notesSlide{nn}.xml'
# ---- slide: copy base, keep bg / accent bar / eyebrow / corner number, drop the rest
s = etree.fromstring(get(base_path))
if 'show' in s.attrib: del s.attrib['show']
tree = s.find('.//p:cSld/p:spTree', NS)
keep_eyebrow = None
for el in list(tree):
    if el.tag in ('{%s}nvGrpSpPr' % P, '{%s}grpSpPr' % P): continue
    txt = ''.join(el.itertext()).strip()
    off = el.find('.//a:off', NS)
    y = int(off.get('y')) if off is not None else 0
    if el.tag == '{%s}sp' % P and not txt and y < 600000: continue            # accent bar
    if el.tag == '{%s}sp' % P and re.fullmatch(r'\d{1,3}(/\d{1,3})?', txt): continue  # corner number
    if el.tag == '{%s}sp' % P and txt and y < 800000 and keep_eyebrow is None:
        keep_eyebrow = el; el.findall('.//a:t', NS)[0].text = spec['eyebrow']; continue
    tree.remove(el)
for t in s.findall('p:timing', NS) + s.findall('p:transition', NS): s.remove(t)
nid = max(int(e.get('id')) for e in s.iter('{%s}cNvPr' % P)) + 1
def font(sz, color, b=True, i=False):
    return (f'<a:rPr lang="ja-JP" altLang="en-US" sz="{sz}"{" b=\"1\"" if b else ""}{" i=\"1\"" if i else ""} dirty="0">'
            f'<a:solidFill><a:srgbClr val="{color}"/></a:solidFill><a:latin typeface="Helvetica Neue"/><a:ea typeface="Hiragino Sans"/><a:cs typeface="Hiragino Sans"/></a:rPr>')
X0, W = 658368, 7955279
title = f'''<p:sp xmlns:p="{P}" xmlns:a="{A}"><p:nvSpPr><p:cNvPr id="{nid}" name="Title"/><p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr>
<p:spPr><a:xfrm><a:off x="{X0}" y="880000"/><a:ext cx="{W}" cy="460000"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/></p:spPr>
<p:txBody><a:bodyPr wrap="square" lIns="0" tIns="0" rIns="0" bIns="0" anchor="t"><a:noAutofit/></a:bodyPr><a:lstStyle/>
<a:p><a:r>{font(spec.get("title_sz", 2800), "FFFFFF")}<a:t>{escape(spec["title"])}</a:t></a:r></a:p></p:txBody></p:sp>'''
tree.append(etree.fromstring(title)); nid += 1
# table
cw = spec['col_widths']; assert sum(cw) <= W + 10
rows = [spec['header']] + spec['rows']; hl = spec.get('highlight_row')
rh = spec.get('row_h', 520000); hh = spec.get('head_h', 340000)
def border(tag, color, w=9525):
    return f'<a:{tag} w="{w}"><a:solidFill><a:srgbClr val="{color}"/></a:solidFill></a:{tag}>'
NOLN = ''.join(f'<a:{t} w="0"><a:noFill/></a:{t}>' for t in ('lnL', 'lnR'))
trs = []
for ri, row in enumerate(rows):
    head = ri == 0; hi = (hl is not None and ri == hl + 1)
    tcs = []
    for ci, cell in enumerate(row):
        if head: color, sz, b = 'FFD60A', spec.get('head_sz', 1200), True
        elif hi: color, sz, b = 'FFD60A', spec.get('body_sz', 1400), True
        else: color, sz, b = ('FFFFFF' if ci == 0 else 'E6E6E6'), spec.get('body_sz', 1400), ci == 0
        paras = ''.join(f'<a:p><a:pPr algn="l"/><a:r>{font(sz, color, b)}<a:t>{escape(line)}</a:t></a:r></a:p>' for line in cell.split('\n'))
        fill = '<a:solidFill><a:srgbClr val="FFD60A"><a:alpha val="16000"/></a:srgbClr></a:solidFill>' if hi else '<a:noFill/>'
        bottom = border('lnB', 'FFD60A', 19050) if head else border('lnB', '3A3A3F')
        top = border('lnT', 'FFD60A', 19050) if hi else ('<a:lnT w="0"><a:noFill/></a:lnT>')
        tcs.append(f'<a:tc><a:txBody><a:bodyPr/><a:lstStyle/>{paras}</a:txBody>'
                   f'<a:tcPr marL="64008" marR="45720" marT="27432" marB="27432" anchor="ctr">{NOLN}{top}{bottom}{fill}</a:tcPr></a:tc>')
    trs.append(f'<a:tr h="{hh if head else rh}">{"".join(tcs)}</a:tr>')
grid = ''.join(f'<a:gridCol w="{w}"/>' for w in cw)
ty = spec.get('table_y', 1430000); th = hh + rh * len(spec['rows'])
frame = f'''<p:graphicFrame xmlns:p="{P}" xmlns:a="{A}"><p:nvGraphicFramePr><p:cNvPr id="{nid}" name="Comparison Table"/><p:cNvGraphicFramePr><a:graphicFrameLocks noGrp="1"/></p:cNvGraphicFramePr><p:nvPr/></p:nvGraphicFramePr>
<p:xfrm><a:off x="{X0}" y="{ty}"/><a:ext cx="{sum(cw)}" cy="{th}"/></p:xfrm>
<a:graphic><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/table"><a:tbl><a:tblPr firstRow="1"/><a:tblGrid>{grid}</a:tblGrid>{"".join(trs)}</a:tbl></a:graphicData></a:graphic></p:graphicFrame>'''
tree.append(etree.fromstring(frame)); nid += 1
if spec.get('refs'):
    refs = f'''<p:sp xmlns:p="{P}" xmlns:a="{A}"><p:nvSpPr><p:cNvPr id="{nid}" name="References"/><p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr>
<p:spPr><a:xfrm><a:off x="{X0}" y="{spec.get("refs_y", 4560000)}"/><a:ext cx="{W - 900000}" cy="230000"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/></p:spPr>
<p:txBody><a:bodyPr wrap="square" lIns="0" tIns="0" rIns="0" bIns="0" anchor="t"><a:noAutofit/></a:bodyPr><a:lstStyle/>
<a:p><a:r>{font(900, "8A8A8F", False, True)}<a:t>{escape(spec["refs"])}</a:t></a:r></a:p></p:txBody></p:sp>'''
    tree.append(etree.fromstring(refs)); nid += 1
files[slide_path] = etree.tostring(s, xml_declaration=True, encoding='UTF-8', standalone=True)
files[slide_path.replace('slides/', 'slides/_rels/') + '.rels'] = (
    f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<Relationships xmlns="{PR}">'
    f'<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="{layout}"/>'
    f'<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/notesSlide" Target="../notesSlides/notesSlide{nn}.xml"/>'
    f'</Relationships>').encode()
# ---- notes: copy base notes, replace body text, point back to the new slide
nroot = etree.fromstring(get(notes_src))
for sp in nroot.iter('{%s}sp' % P):
    ph = sp.find('.//p:nvPr/p:ph', NS)
    if ph is not None and ph.get('type') == 'body':
        tx = sp.find('p:txBody', NS)
        ps = tx.findall('a:p', NS); r0 = sp.find('.//a:r/a:rPr', NS)
        for p in ps: tx.remove(p)
        p = etree.SubElement(tx, '{%s}p' % A); r = etree.SubElement(p, '{%s}r' % A)
        if r0 is not None: r.append(copy.deepcopy(r0))
        etree.SubElement(r, '{%s}t' % A).text = spec['notes']
    if ph is not None and ph.get('type') == 'sldNum':
        for t in sp.iter('{%s}t' % A): t.text = ''
files[notes_path] = etree.tostring(nroot, xml_declaration=True, encoding='UTF-8', standalone=True)
nrels = etree.fromstring(get(notes_src.replace('notesSlides/', 'notesSlides/_rels/') + '.rels'))
for r in nrels:
    if r.get('Type').endswith('/slide'): r.set('Target', f'../slides/slide{sn}.xml')
files[notes_path.replace('notesSlides/', 'notesSlides/_rels/') + '.rels'] = etree.tostring(nrels, xml_declaration=True, encoding='UTF-8', standalone=True)
# ---- content types, presentation rels, slide list, app.xml count
ct = etree.fromstring(get('[Content_Types].xml'))
for part, typ in ((slide_path, 'slide'), (notes_path, 'notesSlide')):
    o = etree.SubElement(ct, '{%s}Override' % CT); o.set('PartName', '/' + part)
    o.set('ContentType', f'application/vnd.openxmlformats-officedocument.presentationml.{typ}+xml')
files['[Content_Types].xml'] = etree.tostring(ct, xml_declaration=True, encoding='UTF-8', standalone=True)
rid = 'rId' + str(max(int(r.get('Id')[3:]) for r in prels if r.get('Id')[3:].isdigit()) + 1)
nr = etree.SubElement(prels, '{%s}Relationship' % PR); nr.set('Id', rid)
nr.set('Type', 'http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide'); nr.set('Target', f'slides/slide{sn}.xml')
files['ppt/_rels/presentation.xml.rels'] = etree.tostring(prels, xml_declaration=True, encoding='UTF-8', standalone=True)
new = etree.Element('{%s}sldId' % P); new.set('id', str(max(int(i.get('id')) for i in ids) + 1)); new.set('{%s}id' % R, rid)
base.addnext(new)
files['ppt/presentation.xml'] = etree.tostring(pres, xml_declaration=True, encoding='UTF-8', standalone=True)
if 'docProps/app.xml' in names:
    app = get('docProps/app.xml').decode()
    app = re.sub(r'<Slides>(\d+)</Slides>', lambda m: f'<Slides>{int(m.group(1)) + 1}</Slides>', app)
    app = re.sub(r'<Notes>(\d+)</Notes>', lambda m: f'<Notes>{int(m.group(1)) + 1}</Notes>', app)
    files['docProps/app.xml'] = app.encode()
with zipfile.ZipFile(dst, 'w') as out:
    for info in z.infolist():
        out.writestr(info, files.get(info.filename, z.read(info.filename)), compress_type=info.compress_type)
    for n, d in files.items():
        if n not in names: out.writestr(n, d, compress_type=zipfile.ZIP_DEFLATED)
print(f'inserted {slide_path} (+{notes_path}) after slide {spec["after"]}; now {len(ids) + 1} slides')
