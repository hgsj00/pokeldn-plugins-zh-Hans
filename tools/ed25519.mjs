// Ed25519 helpers for signing a .pokeplugin the way pokeldn's plugin_store expects.
//   node tools/ed25519.mjs gen
//   node tools/ed25519.mjs sign KEY.pem MANIFEST.bin       -> base64 signature
//   node tools/ed25519.mjs verify PUB_BASE64 MANIFEST.bin SIG_BASE64
// pokeldn uses pycryptodome's Ed25519 (RFC 8032); Node's Ed25519 is the same curve and encoding,
// and the private key is written as PKCS#8 PEM, which pycryptodome imports.
import crypto from "node:crypto";
import fs from "node:fs";

const [command, ...args] = process.argv.slice(2);

if (command === "gen") {
  const { publicKey, privateKey } = crypto.generateKeyPairSync("ed25519");
  const pem = privateKey.export({ type: "pkcs8", format: "pem" });
  const raw = Buffer.from(publicKey.export({ format: "jwk" }).x, "base64url");
  process.stdout.write(JSON.stringify({ pem, public: raw.toString("base64") }));
} else if (command === "pub") {
  const [keyPath] = args;
  const key = crypto.createPrivateKey(fs.readFileSync(keyPath));
  const raw = Buffer.from(crypto.createPublicKey(key).export({ format: "jwk" }).x, "base64url");
  process.stdout.write(raw.toString("base64"));
} else if (command === "sign") {
  const [keyPath, dataPath] = args;
  const key = crypto.createPrivateKey(fs.readFileSync(keyPath));
  process.stdout.write(crypto.sign(null, fs.readFileSync(dataPath), key).toString("base64"));
} else if (command === "verify") {
  const [publicKey, dataPath, signature] = args;
  const raw = Buffer.from(publicKey, "base64");
  const der = Buffer.concat([Buffer.from("302a300506032b6570032100", "hex"), raw]);
  const key = crypto.createPublicKey({ key: der, format: "der", type: "spki" });
  const ok = crypto.verify(null, fs.readFileSync(dataPath), key, Buffer.from(signature, "base64"));
  process.stdout.write(ok ? "ok" : "bad");
  if (!ok) process.exit(1);
} else {
  process.stderr.write("usage: ed25519.mjs gen|sign|verify\n");
  process.exit(2);
}
