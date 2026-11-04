# Pull the speaker notes out of a .pptx, one entry per slide, in show order.
# usage: python3 tools/extract_notes.py deck.pptx notes.json [source_mtime_ms]
import zipfile, sys, json, os, hashlib
import xml.etree.ElementTree as ET
NS = {'p':'http://schemas.openxmlformats.org/presentationml/2006/main',
      'a':'http://schemas.openxmlformats.org/drawingml/2006/main',
      'r':'http://schemas.openxmlformats.org/officeDocument/2006/relationships'}
REL = '{http://schemas.openxmlformats.org/package/2006/relationships}Relationship'
def rels(z, path):
    d, f = os.path.split(path); rp = f"{d}/_rels/{f}.rels"; out = {}
    if rp in z.namelist():
        for r in ET.fromstring(z.read(rp)).iter(REL):
            out[r.get('Id')] = (r.get('Type').rsplit('/',1)[-1], os.path.normpath(os.path.join(d, r.get('Target'))))
    return out
def notes_text(xml):
    root = ET.fromstring(xml); paras = []
    for sp in root.iter('{%s}sp' % NS['p']):
        ph = sp.find('.//p:nvPr/p:ph', NS)
        if ph is None or ph.get('type') != 'body': continue
        for para in sp.iter('{%s}p' % NS['a']):
            paras.append(''.join((n.text or '') if n.tag.endswith('}t') else '\n' for n in para.iter() if n.tag.endswith('}t') or n.tag.endswith('}br')))
    return '\n'.join(paras).strip()
src, dst = sys.argv[1], sys.argv[2]
mtime = int(sys.argv[3]) if len(sys.argv) > 3 else int(os.path.getmtime(src) * 1000)
z = zipfile.ZipFile(src)
pres = ET.fromstring(z.read('ppt/presentation.xml')); prel = rels(z, 'ppt/presentation.xml')
slides = []
for n, sid in enumerate(pres.find('p:sldIdLst', NS), 1):
    spath = prel[sid.get('{%s}id' % NS['r'])][1]
    hidden = ET.fromstring(z.read(spath)).get('show') == '0'
    notes = ''
    for typ, tgt in rels(z, spath).values():
        if typ == 'notesSlide': notes = notes_text(z.read(tgt))
    slides.append({'n': n, 'hidden': hidden, 'title': '', 'notes': notes})
out = {'file': os.path.basename(src), 'mtime': mtime, 'slides': slides}
out['hash'] = hashlib.sha256(json.dumps(slides, ensure_ascii=False).encode()).hexdigest()[:16]
json.dump(out, open(dst, 'w'), ensure_ascii=False, indent=1)
print(out['file'], len(slides), 'slides', out['hash'])
