# Replace the text of one paragraph in a text box (keeps its formatting); optionally set the font size of all its paragraphs.
# usage: python3 tools/set_para_text.py in.pptx out.pptx SLIDE SHAPE_ID PARA_INDEX "new text" [SIZE_100PT]
import zipfile, sys, os
from lxml import etree
P='http://schemas.openxmlformats.org/presentationml/2006/main'
A='http://schemas.openxmlformats.org/drawingml/2006/main'
R='http://schemas.openxmlformats.org/officeDocument/2006/relationships'
PR='http://schemas.openxmlformats.org/package/2006/relationships'
NS={'p':P,'a':A}
src, dst, slide_no, spid, pi, new = sys.argv[1:7]
size = sys.argv[7] if len(sys.argv) > 7 else None
z = zipfile.ZipFile(src)
pres = etree.fromstring(z.read('ppt/presentation.xml'))
rels = {r.get('Id'): os.path.normpath(os.path.join('ppt', r.get('Target'))) for r in etree.fromstring(z.read('ppt/_rels/presentation.xml.rels')).iter('{%s}Relationship' % PR)}
path = [rels[s.get('{%s}id' % R)] for s in pres.find('p:sldIdLst', NS)][int(slide_no) - 1]
root = etree.fromstring(z.read(path))
sp = next(s for s in root.iter('{%s}sp' % P) if s.find('p:nvSpPr/p:cNvPr', NS).get('id') == spid)
paras = sp.findall('p:txBody/a:p', NS)
runs = paras[int(pi)].findall('a:r', NS)
print('before:', ''.join(t.text or '' for r in runs for t in r.findall('a:t', NS)))
runs[0].find('a:t', NS).text = new
for r in runs[1:]: paras[int(pi)].remove(r)
if size:
    for p in paras:
        for rp in p.iter('{%s}rPr' % A, '{%s}endParaRPr' % A): rp.set('sz', size)
data = etree.tostring(root, xml_declaration=True, encoding='UTF-8', standalone=True)
with zipfile.ZipFile(dst, 'w') as out:
    for info in z.infolist():
        out.writestr(info, data if info.filename == path else z.read(info.filename), compress_type=info.compress_type)
print('after:', new)
