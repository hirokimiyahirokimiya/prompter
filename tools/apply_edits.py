# Write slide-note edits made on the phone into a NEW version of the deck.
# usage: python3 tools/apply_edits.py deck.pptx edits.json outdir [existing file names...]
# edits.json: {"edits":[{"n":3,"text":"...","base":"..."}]}  (n = slide position in the show)
# A slide is changed only when its current note still equals "base" (what the phone started from);
# otherwise it is reported as a conflict and left alone. Prints a JSON report.
import zipfile, sys, json, os, re, copy, datetime
from lxml import etree
P = 'http://schemas.openxmlformats.org/presentationml/2006/main'
A = 'http://schemas.openxmlformats.org/drawingml/2006/main'
R = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
PR = 'http://schemas.openxmlformats.org/package/2006/relationships'
NS = {'p': P, 'a': A}
def norm(t): return re.sub(r'\s+', '', t or '')
def rels(z, path):
    d, f = os.path.split(path); rp = f"{d}/_rels/{f}.rels"; out = {}
    if rp in z.namelist():
        for r in etree.fromstring(z.read(rp)).iter('{%s}Relationship' % PR):
            out[r.get('Id')] = (r.get('Type').rsplit('/', 1)[-1], os.path.normpath(os.path.join(d, r.get('Target'))))
    return out
def body_sp(root):
    for sp in root.iter('{%s}sp' % P):
        ph = sp.find('.//p:nvPr/p:ph', NS)
        if ph is not None and ph.get('type') == 'body': return sp
def text_of(sp):
    paras = []
    for para in sp.iter('{%s}p' % A):
        paras.append(''.join((n.text or '') if n.tag == '{%s}t' % A else '\n' for n in para.iter() if n.tag in ('{%s}t' % A, '{%s}br' % A)))
    return '\n'.join(paras).strip()
def set_text(sp, new):
    tx = sp.find('p:txBody', NS)
    old = tx.findall('a:p', NS)
    first = old[0] if old else None
    ppr = first.find('a:pPr', NS) if first is not None else None
    r0 = sp.find('.//a:r/a:rPr', NS)
    end = first.find('a:endParaRPr', NS) if first is not None else None
    for p in old: tx.remove(p)
    for line in new.split('\n'):
        p = etree.SubElement(tx, '{%s}p' % A)
        if ppr is not None: p.append(copy.deepcopy(ppr))
        if line:
            r = etree.SubElement(p, '{%s}r' % A)
            if r0 is not None: r.append(copy.deepcopy(r0))
            t = etree.SubElement(r, '{%s}t' % A); t.text = line
        if end is not None: p.append(copy.deepcopy(end))
def next_name(name, existing):
    today = (datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))).strftime('%Y-%m-%d')
    m = re.match(r'^(.*_v)(\d+)(_\d{4}-\d{2}-\d{2})?(\.pptx)$', name, re.I)
    if m:
        v = int(m.group(2)) + 1
        while True:
            cand = f"{m.group(1)}{v}_{today}{m.group(4)}"
            if cand not in existing: return cand
            v += 1
    base = name[:-5]; i = 1
    while True:
        cand = f"{base}_スマホ修正{i}_{today}.pptx"
        if cand not in existing: return cand
        i += 1
src, editf, outdir = sys.argv[1], sys.argv[2], sys.argv[3]
existing = set(sys.argv[4:])
edits = json.load(open(editf)).get('edits', [])
z = zipfile.ZipFile(src)
pres = etree.fromstring(z.read('ppt/presentation.xml')); prel = rels(z, 'ppt/presentation.xml')
order = [prel[s.get('{%s}id' % R)][1] for s in pres.find('p:sldIdLst', NS)]
changed, report = {}, {'applied': [], 'already': [], 'conflicts': []}
for e in edits:
    n = int(e['n'])
    if not (1 <= n <= len(order)): report['conflicts'].append({'n': n, 'why': 'スライドがありません'}); continue
    notes = [t for typ, t in rels(z, order[n-1]).values() if typ == 'notesSlide']
    if not notes: report['conflicts'].append({'n': n, 'why': 'ノート欄がありません'}); continue
    path = notes[0]
    root = changed.get(path) or etree.fromstring(z.read(path))
    sp = body_sp(root)
    if sp is None: report['conflicts'].append({'n': n, 'why': 'ノート欄がありません'}); continue
    cur = text_of(sp)
    if norm(cur) == norm(e['text']): report['already'].append(n); continue
    if norm(cur) != norm(e.get('base', '')): report['conflicts'].append({'n': n, 'why': 'パワポ側でも直されています'}); continue
    set_text(sp, e['text']); changed[path] = root; report['applied'].append(n)
if changed:
    out = next_name(os.path.basename(src), existing)
    with zipfile.ZipFile(os.path.join(outdir, out), 'w') as w:
        for info in z.infolist():
            data = etree.tostring(changed[info.filename], xml_declaration=True, encoding='UTF-8', standalone=True) if info.filename in changed else z.read(info.filename)
            w.writestr(info, data, compress_type=info.compress_type)
    report['out'] = out
print(json.dumps(report, ensure_ascii=False))
