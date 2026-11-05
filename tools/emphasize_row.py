# Emphasize one row of the table on a slide (light yellow fill, bold, yellow line above).
# usage: python3 tools/emphasize_row.py in.pptx out.pptx SLIDE ROW_INDEX(0=header) [ALPHA_1000ths=9000] [TEXT_COLOR=FFFFFF]
import zipfile, sys, os
from lxml import etree
P='http://schemas.openxmlformats.org/presentationml/2006/main'
A='http://schemas.openxmlformats.org/drawingml/2006/main'
R='http://schemas.openxmlformats.org/officeDocument/2006/relationships'
PR='http://schemas.openxmlformats.org/package/2006/relationships'
NS={'p':P,'a':A}
src, dst, slide_no, ri = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
alpha = sys.argv[5] if len(sys.argv) > 5 else '9000'; color = sys.argv[6] if len(sys.argv) > 6 else 'FFFFFF'
z = zipfile.ZipFile(src)
pres = etree.fromstring(z.read('ppt/presentation.xml'))
rels = {r.get('Id'): os.path.normpath(os.path.join('ppt', r.get('Target'))) for r in etree.fromstring(z.read('ppt/_rels/presentation.xml.rels')).iter('{%s}Relationship' % PR)}
path = [rels[s.get('{%s}id' % R)] for s in pres.find('p:sldIdLst', NS)][slide_no - 1]
root = etree.fromstring(z.read(path))
tr = root.findall('.//a:tbl/a:tr', NS)[ri]
def ln(tag, col, w):
    e = etree.Element('{%s}%s' % (A, tag)); e.set('w', str(w))
    f = etree.SubElement(e, '{%s}solidFill' % A); etree.SubElement(f, '{%s}srgbClr' % A).set('val', col); return e
for tc in tr.findall('a:tc', NS):
    for rpr in tc.iter('{%s}rPr' % A):
        rpr.set('b', '1')
        sf = rpr.find('a:solidFill/a:srgbClr', NS)
        if sf is not None: sf.set('val', color)
    pr = tc.find('a:tcPr', NS)
    for t in ('lnT', 'solidFill', 'noFill'):
        for e in pr.findall('a:' + t, NS): pr.remove(e)
    # order inside tcPr: lnL lnR lnT lnB ... fill
    lnb = pr.find('a:lnB', NS)
    lnb.addprevious(ln('lnT', 'FFD60A', 12700))
    f = etree.SubElement(pr, '{%s}solidFill' % A); c = etree.SubElement(f, '{%s}srgbClr' % A); c.set('val', 'FFD60A')
    etree.SubElement(c, '{%s}alpha' % A).set('val', alpha)
data = etree.tostring(root, xml_declaration=True, encoding='UTF-8', standalone=True)
with zipfile.ZipFile(dst, 'w') as out:
    for info in z.infolist():
        out.writestr(info, data if info.filename == path else z.read(info.filename), compress_type=info.compress_type)
print(f'slide {slide_no}: row {ri} emphasized:', ' | '.join(''.join(t.text or '' for t in tc.iter('{%s}t' % A)) for tc in tr.findall('a:tc', NS)))
