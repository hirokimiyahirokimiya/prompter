# Turn each slide's small corner page number into "n/N" (e.g. 3/24), keeping its look.
# Slides without a corner number get one copied from another slide's style.
# Safe to re-run: it recognises both "3" and "3/24".
# usage: python3 tools/add_slide_numbers.py in.pptx out.pptx
import zipfile, sys, os, re, copy
from lxml import etree
P='http://schemas.openxmlformats.org/presentationml/2006/main'
A='http://schemas.openxmlformats.org/drawingml/2006/main'
R='http://schemas.openxmlformats.org/officeDocument/2006/relationships'
PR='http://schemas.openxmlformats.org/package/2006/relationships'
NS={'p':P,'a':A}
src, dst = sys.argv[1], sys.argv[2]
z = zipfile.ZipFile(src)
pres = etree.fromstring(z.read('ppt/presentation.xml'))
sz = pres.find('p:sldSz', NS); cx, cy = int(sz.get('cx')), int(sz.get('cy'))
rels = {r.get('Id'): os.path.normpath(os.path.join('ppt', r.get('Target'))) for r in etree.fromstring(z.read('ppt/_rels/presentation.xml.rels')).iter('{%s}Relationship' % PR)}
order = [rels[s.get('{%s}id' % R)] for s in pres.find('p:sldIdLst', NS)]
roots = {p: etree.fromstring(z.read(p)) for p in order}
shown = [p for p in order if roots[p].get('show') != '0']
total = len(shown)
def corner_box(root):
    for sp in root.iter('{%s}sp' % P):
        t = ''.join(sp.itertext()).strip(); off = sp.find('p:spPr/a:xfrm/a:off', NS)
        if off is None or not re.fullmatch(r'\d{1,3}(/\d{1,3})?', t): continue
        if int(off.get('x')) > cx * 0.75 and int(off.get('y')) > cy * 0.8: return sp
template = next((copy.deepcopy(b) for b in (corner_box(roots[p]) for p in shown) if b is not None), None)
done = added = 0
for i, path in enumerate(shown, 1):
    root = roots[path]; sp = corner_box(root)
    if sp is None:
        if template is None: continue
        sp = copy.deepcopy(template)
        ids = [int(e.get('id')) for e in root.iter('{%s}cNvPr' % P) if (e.get('id') or '').isdigit()]
        sp.find('p:nvSpPr/p:cNvPr', NS).set('id', str(max(ids + [1]) + 1))
        root.find('.//p:cSld/p:spTree', NS).append(sp); added += 1
    ts = sp.findall('.//a:t', NS)
    ts[0].text = f'{i}/{total}'
    for t in ts[1:]: t.text = ''
    off, ext = sp.find('p:spPr/a:xfrm/a:off', NS), sp.find('p:spPr/a:xfrm/a:ext', NS)
    need = int(914400 * 0.75)                       # room for "24/24", right edge stays put
    if int(ext.get('cx')) < need:
        right = int(off.get('x')) + int(ext.get('cx'))
        ext.set('cx', str(need)); off.set('x', str(right - need))
    done += 1
with zipfile.ZipFile(dst, 'w') as out:
    for info in z.infolist():
        data = etree.tostring(roots[info.filename], xml_declaration=True, encoding='UTF-8', standalone=True) if info.filename in roots else z.read(info.filename)
        out.writestr(info, data, compress_type=info.compress_type)
print(f'numbered {done} slides as n/{total} (added {added})')
