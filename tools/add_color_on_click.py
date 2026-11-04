# Add "change font color" to paragraphs of one text box, played together with an existing click.
# usage: python3 tools/add_color_on_click.py in.pptx out.pptx SLIDE SHAPE_ID COLOR CLICK:PARAS [CLICK:PARAS ...]
#   e.g. ... 9 5 FFD60A 1:0,1 2:2   -> on click 1, paragraphs 0 and 1 turn yellow; on click 2, paragraph 2.
# CLICK counts the slide's existing click steps (1 = first click). Paragraph numbers start at 0.
import zipfile, sys, os
from lxml import etree
P='http://schemas.openxmlformats.org/presentationml/2006/main'
A='http://schemas.openxmlformats.org/drawingml/2006/main'
R='http://schemas.openxmlformats.org/officeDocument/2006/relationships'
PR='http://schemas.openxmlformats.org/package/2006/relationships'
NS={'p':P,'a':A}
src, dst, slide_no, spid, color = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4], sys.argv[5]
plan = {int(k): [int(x) for x in v.split(',')] for k, v in (a.split(':') for a in sys.argv[6:])}
z = zipfile.ZipFile(src)
pres = etree.fromstring(z.read('ppt/presentation.xml'))
rels = {r.get('Id'): os.path.normpath(os.path.join('ppt', r.get('Target'))) for r in etree.fromstring(z.read('ppt/_rels/presentation.xml.rels')).iter('{%s}Relationship' % PR)}
path = [rels[s.get('{%s}id' % R)] for s in pres.find('p:sldIdLst', NS)][slide_no - 1]
root = etree.fromstring(z.read(path))
seq = root.find('.//p:timing//p:cTn[@nodeType="mainSeq"]/p:childTnLst', NS)
clicks = seq.findall('p:par', NS)
next_id = max(int(c.get('id')) for c in root.iter('{%s}cTn' % P)) + 1
grp = max([int(c.get('grpId')) for c in root.iter('{%s}cTn' % P) if c.get('grpId')] + [-1]) + 1
for k, paras in plan.items():
    inner = clicks[k - 1].find('p:cTn/p:childTnLst/p:par/p:cTn/p:childTnLst', NS)
    for pi in paras:
        a, b = next_id, next_id + 1; next_id += 2
        inner.append(etree.fromstring(f'''<p:par xmlns:p="{P}" xmlns:a="{A}"><p:cTn id="{a}" presetID="3" presetClass="emph" presetSubtype="2" grpId="{grp}" nodeType="withEffect"><p:stCondLst><p:cond delay="0"/></p:stCondLst><p:childTnLst>
<p:animClr clrSpc="rgb" dir="cw"><p:cBhvr override="childStyle"><p:cTn id="{b}" dur="300" fill="hold"/><p:tgtEl><p:spTgt spid="{spid}"><p:txEl><p:pRg st="{pi}" end="{pi}"/></p:txEl></p:spTgt></p:tgtEl><p:attrNameLst><p:attrName>style.color</p:attrName></p:attrNameLst></p:cBhvr><p:to><a:srgbClr val="{color}"/></p:to></p:animClr>
</p:childTnLst></p:cTn></p:par>'''))
timing = root.find('p:timing', NS)
bld = timing.find('p:bldLst', NS)
if bld is None: bld = etree.SubElement(timing, '{%s}bldLst' % P)
bld.append(etree.fromstring(f'<p:bldP xmlns:p="{P}" spid="{spid}" grpId="{grp}" build="p"/>'))
data = etree.tostring(root, xml_declaration=True, encoding='UTF-8', standalone=True)
with zipfile.ZipFile(dst, 'w') as out:
    for info in z.infolist():
        out.writestr(info, data if info.filename == path else z.read(info.filename), compress_type=info.compress_type)
print(f'slide {slide_no}: color changes added on clicks {sorted(plan)}')
