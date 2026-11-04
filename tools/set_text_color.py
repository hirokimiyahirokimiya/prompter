# Set the text color of every run in one text box.
# usage: python3 tools/set_text_color.py in.pptx out.pptx SLIDE SHAPE_ID RRGGBB
import zipfile, sys, os, copy
from lxml import etree
P='http://schemas.openxmlformats.org/presentationml/2006/main'
A='http://schemas.openxmlformats.org/drawingml/2006/main'
R='http://schemas.openxmlformats.org/officeDocument/2006/relationships'
PR='http://schemas.openxmlformats.org/package/2006/relationships'
NS={'p':P,'a':A}
src, dst, slide_no, spid, color = sys.argv[1:6]
z = zipfile.ZipFile(src)
pres = etree.fromstring(z.read('ppt/presentation.xml'))
rels = {r.get('Id'): os.path.normpath(os.path.join('ppt', r.get('Target'))) for r in etree.fromstring(z.read('ppt/_rels/presentation.xml.rels')).iter('{%s}Relationship' % PR)}
path = [rels[s.get('{%s}id' % R)] for s in pres.find('p:sldIdLst', NS)][int(slide_no) - 1]
root = etree.fromstring(z.read(path))
sp = next(s for s in root.iter('{%s}sp' % P) if s.find('p:nvSpPr/p:cNvPr', NS).get('id') == spid)
n = 0
for r in sp.iter('{%s}r' % A):
    rpr = r.find('a:rPr', NS)
    if rpr is None: rpr = etree.Element('{%s}rPr' % A); r.insert(0, rpr)
    for f in rpr.findall('a:solidFill', NS) + rpr.findall('a:gradFill', NS) + rpr.findall('a:noFill', NS): rpr.remove(f)
    fill = etree.Element('{%s}solidFill' % A); etree.SubElement(fill, '{%s}srgbClr' % A).set('val', color)
    pos = 0                                   # solidFill must come before latin/ea/cs etc.
    for i, ch in enumerate(rpr):
        if etree.QName(ch).localname in ('ln',): pos = i + 1
    rpr.insert(pos, fill); n += 1
data = etree.tostring(root, xml_declaration=True, encoding='UTF-8', standalone=True)
with zipfile.ZipFile(dst, 'w') as out:
    for info in z.infolist():
        out.writestr(info, data if info.filename == path else z.read(info.filename), compress_type=info.compress_type)
print(f'slide {slide_no} shape {spid}: {n} runs set to #{color}:', ' / '.join(''.join(t.text or '' for t in p.iter('{%s}t' % A)) for p in sp.findall('p:txBody/a:p', NS)))
