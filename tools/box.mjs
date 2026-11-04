// Encrypt/decrypt small JSON files with the shared passphrase (same format the phone uses).
// node tools/box.mjs open  in.enc.json out.json
// node tools/box.mjs close in.json out.enc.json
import { readFileSync, writeFileSync } from 'node:fs';
import { webcrypto as C } from 'node:crypto';
const [cmd, a, b] = process.argv.slice(2);
const pass = process.env.PROMPTER_PASS;
const key = async (salt, use) => C.subtle.deriveKey({ name: 'PBKDF2', salt, iterations: 250000, hash: 'SHA-256' },
  await C.subtle.importKey('raw', new TextEncoder().encode(pass), 'PBKDF2', false, ['deriveKey']), { name: 'AES-GCM', length: 256 }, false, [use]);
if (cmd === 'open') {
  const env = JSON.parse(readFileSync(a, 'utf8'));
  const pt = await C.subtle.decrypt({ name: 'AES-GCM', iv: Buffer.from(env.iv, 'base64') }, await key(Buffer.from(env.salt, 'base64'), 'decrypt'), Buffer.from(env.ct, 'base64'));
  writeFileSync(b, Buffer.from(pt).toString('utf8'));
} else if (cmd === 'close') {
  const salt = C.getRandomValues(new Uint8Array(16)), iv = C.getRandomValues(new Uint8Array(12));
  const ct = await C.subtle.encrypt({ name: 'AES-GCM', iv }, await key(salt, 'encrypt'), new TextEncoder().encode(readFileSync(a, 'utf8')));
  const b64 = u => Buffer.from(u).toString('base64');
  writeFileSync(b, JSON.stringify({ v: 1, updated: new Date().toISOString(), salt: b64(salt), iv: b64(iv), ct: b64(ct) }));
} else { console.error('open|close'); process.exit(2); }
