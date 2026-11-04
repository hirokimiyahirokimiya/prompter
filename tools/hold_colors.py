# Make font-color changes stay after they play (add fill="hold" to emphasis color effects).
# usage: python3 tools/hold_colors.py in.pptx out.pptx SLIDE
import zipfile, sys, os
from lxml import etree
P='http://schemas.openxmlformats.org/presentationml/2006/main'
R='http://schemas.openxmlformats.org/officeDocument/2006/relationships'
PR='http://schemas.openxmlformats.org/package/2006/relationships'
NS={'p':P}
src, dst, slide_no = sys.argv[1], sys.argv[2], int(sys.argv[3])
z = zipfile.ZipFile(src)
pres = etree.fromstring(z.read('ppt/presentation.xml'))
rels = {r.get('Id'): os.path.normpath(os.path.join('ppt', r.get('Target'))) for r in etree.fromstring(z.read('ppt/_rels/presentation.xml.rels')).iter('{%s}Relationship' % PR)}
path = [rels[s.get('{%s}id' % R)] for s in pres.find('p:sldIdLst', NS)][slide_no - 1]
root = etree.fromstring(z.read(path)); n = 0
for c in root.iter('{%s}cTn' % P):
    if c.get('presetClass') == 'emph' and c.find('.//p:animClr', NS) is not None:
        c.set('fill', 'hold'); n += 1
    for a in c.findall('p:childTnLst/p:animClr', NS):
        a.find('p:cBhvr/p:cTn', NS).set('fill', 'hold')
data = etree.tostring(root, xml_declaration=True, encoding='UTF-8', standalone=True)
with zipfile.ZipFile(dst, 'w') as out:
    for info in z.infolist():
        out.writestr(info, data if info.filename == path else z.read(info.filename), compress_type=info.compress_type)
print(f'slide {slide_no}: {n} color effects now hold')
