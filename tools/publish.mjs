// Publishes the extracted speaker notes as script.json for the phone (plain text: the notes hold no personal data).
// usage: node tools/publish.mjs notes.json script.json
// Writes nothing (exit code 3) when the notes are unchanged.
import { readFileSync, writeFileSync, existsSync } from 'node:fs';
const [src, dst] = process.argv.slice(2);
const notes = JSON.parse(readFileSync(src, 'utf8'));
const prev = existsSync(dst) ? JSON.parse(readFileSync(dst, 'utf8')) : null;
if (prev && prev.notesHash === notes.hash && prev.srcMtime === notes.mtime) { console.log('unchanged', notes.hash); process.exit(3); }
const out = { v: 2, hash: `${notes.hash}.${notes.mtime}`, notesHash: notes.hash, srcMtime: notes.mtime, updated: new Date().toISOString(),
  file: notes.file, mtime: notes.mtime, slides: notes.slides.filter(s => !s.hidden).map(s => ({ n: s.n, t: s.notes })) };
writeFileSync(dst, JSON.stringify(out, null, 1) + '\n');
console.log('published', notes.hash, out.slides.length, 'slides');
