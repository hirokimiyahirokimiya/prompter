// Encrypts the extracted speaker notes so the public repo only holds ciphertext.
// usage: PROMPTER_PASS=... node tools/seal.mjs notes.json script.enc.json
// Writes nothing (exit code 3) when the notes are unchanged.
import { readFileSync, writeFileSync, existsSync } from 'node:fs';
import { webcrypto as C } from 'node:crypto';
const [src, dst] = process.argv.slice(2);
const pass = process.env.PROMPTER_PASS;
if (!pass) { console.error('PROMPTER_PASS missing'); process.exit(2); }
const notes = JSON.parse(readFileSync(src, 'utf8'));
const prev = existsSync(dst) ? JSON.parse(readFileSync(dst, 'utf8')) : null;
if (prev && prev.hash === notes.hash) { console.log('unchanged', notes.hash); process.exit(3); }
const b64 = u => Buffer.from(u).toString('base64');
const salt = prev ? Buffer.from(prev.salt, 'base64') : C.getRandomValues(new Uint8Array(16));
const iv = C.getRandomValues(new Uint8Array(12));
const base = await C.subtle.importKey('raw', new TextEncoder().encode(pass), 'PBKDF2', false, ['deriveKey']);
const key = await C.subtle.deriveKey({ name: 'PBKDF2', salt, iterations: 250000, hash: 'SHA-256' }, base, { name: 'AES-GCM', length: 256 }, false, ['encrypt']);
const payload = { file: notes.file, mtime: notes.mtime, slides: notes.slides.filter(s => !s.hidden).map(s => ({ n: s.n, t: s.notes })) };
const ct = new Uint8Array(await C.subtle.encrypt({ name: 'AES-GCM', iv }, key, new TextEncoder().encode(JSON.stringify(payload))));
const out = { v: 1, hash: notes.hash, srcMtime: notes.mtime, updated: new Date().toISOString(), salt: b64(salt), iv: b64(iv), ct: b64(ct) };
writeFileSync(dst, JSON.stringify(out));
console.log('sealed', notes.hash, payload.slides.length, 'slides');
