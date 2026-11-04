# Add a small label (yellow bold text on a dark translucent chip) to a slide,
# appearing with an existing click (fade in together with what that click shows).
# usage: python3 tools/add_label.py in.pptx out.pptx SLIDE CLICK CX_EMU CY_EMU TEXT [W_EMU H_EMU SIZE_100PT]
import zipfile, sys, os
from lxml import etree
P='http://schemas.openxmlformats.org/presentationml/2006/main'
A='http://schemas.openxmlformats.org/drawingml/2006/main'
R='http://schemas.openxmlformats.org/officeDocument/2006/relationships'
PR='http://schemas.openxmlformats.org/package/2006/relationships'
NS={'p':P,'a':A}
src, dst, slide_no, click, cx, cy, text = sys.argv[1:8]
slide_no, click, cx, cy = int(slide_no), int(click), int(cx), int(cy)
w = int(sys.argv[8]) if len(sys.argv) > 8 else 566928
h = int(sys.argv[9]) if len(sys.argv) > 9 else 329184
size = int(sys.argv[10]) if len(sys.argv) > 10 else 1800
z = zipfile.ZipFile(src)
pres = etree.fromstring(z.read('ppt/presentation.xml'))
rels = {r.get('Id'): os.path.normpath(os.path.join('ppt', r.get('Target'))) for r in etree.fromstring(z.read('ppt/_rels/presentation.xml.rels')).iter('{%s}Relationship' % PR)}
path = [rels[s.get('{%s}id' % R)] for s in pres.find('p:sldIdLst', NS)][slide_no - 1]
root = etree.fromstring(z.read(path))
ids = [int(e.get('id')) for e in root.iter() if e.tag in ('{%s}cNvPr' % P, '{%s}cTn' % P) and (e.get('id') or '').isdigit()]
spid = max(int(e.get('id')) for e in root.iter('{%s}cNvPr' % P) if (e.get('id') or '').isdigit()) + 1
root.find('.//p:cSld/p:spTree', NS).append(etree.fromstring(f'''<p:sp xmlns:p="{P}" xmlns:a="{A}">
<p:nvSpPr><p:cNvPr id="{spid}" name="Label {text}"/><p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr>
<p:spPr><a:xfrm><a:off x="{cx - w // 2}" y="{cy - h // 2}"/><a:ext cx="{w}" cy="{h}"/></a:xfrm><a:prstGeom prst="roundRect"><a:avLst/></a:prstGeom>
<a:solidFill><a:srgbClr val="000000"><a:alpha val="62000"/></a:srgbClr></a:solidFill><a:ln><a:noFill/></a:ln></p:spPr>
<p:txBody><a:bodyPr wrap="none" lIns="45720" tIns="0" rIns="45720" bIns="0" anchor="ctr"><a:noAutofit/></a:bodyPr><a:lstStyle/>
<a:p><a:pPr algn="ctr"/><a:r><a:rPr lang="ja-JP" altLang="en-US" sz="{size}" b="1" dirty="0"><a:solidFill><a:srgbClr val="FFD60A"/></a:solidFill><a:latin typeface="Helvetica Neue"/><a:ea typeface="Hiragino Sans"/></a:rPr><a:t>{text}</a:t></a:r></a:p></p:txBody></p:sp>'''))
seq = root.find('.//p:timing//p:cTn[@nodeType="mainSeq"]/p:childTnLst', NS)
inner = seq.findall('p:par', NS)[click - 1].find('p:cTn/p:childTnLst/p:par/p:cTn/p:childTnLst', NS)
ctn = max(int(c.get('id')) for c in root.iter('{%s}cTn' % P)) + 1
grp = max([int(c.get('grpId')) for c in root.iter('{%s}cTn' % P) if c.get('grpId')] + [-1]) + 1
inner.append(etree.fromstring(f'''<p:par xmlns:p="{P}"><p:cTn id="{ctn}" presetID="10" presetClass="entr" presetSubtype="0" fill="hold" grpId="{grp}" nodeType="withEffect"><p:stCondLst><p:cond delay="0"/></p:stCondLst><p:childTnLst>
<p:set><p:cBhvr><p:cTn id="{ctn+1}" dur="1" fill="hold"><p:stCondLst><p:cond delay="0"/></p:stCondLst></p:cTn><p:tgtEl><p:spTgt spid="{spid}"/></p:tgtEl><p:attrNameLst><p:attrName>style.visibility</p:attrName></p:attrNameLst></p:cBhvr><p:to><p:strVal val="visible"/></p:to></p:set>
<p:animEffect transition="in" filter="fade"><p:cBhvr><p:cTn id="{ctn+2}" dur="500"/><p:tgtEl><p:spTgt spid="{spid}"/></p:tgtEl></p:cBhvr></p:animEffect></p:childTnLst></p:cTn></p:par>'''))
timing = root.find('p:timing', NS)
bld = timing.find('p:bldLst', NS)
if bld is None: bld = etree.SubElement(timing, '{%s}bldLst' % P)
bld.append(etree.fromstring(f'<p:bldP xmlns:p="{P}" spid="{spid}" grpId="{grp}" animBg="1"/>'))
data = etree.tostring(root, xml_declaration=True, encoding='UTF-8', standalone=True)
with zipfile.ZipFile(dst, 'w') as out:
    for info in z.infolist():
        out.writestr(info, data if info.filename == path else z.read(info.filename), compress_type=info.compress_type)
print(f'slide {slide_no}: label "{text}" on click {click}')
