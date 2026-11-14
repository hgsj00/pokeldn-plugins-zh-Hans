"""Sign an existing .pokeplugin the way pokeldn verifies it.

    python tools/sign_package.py packages/pokeldn-zh-Hans-1.0.0.pokeplugin --key ../keys/zh-hans-signing.pem

Needs Node.js (for Ed25519) because this workspace has no pycryptodome. The manifest is built exactly
as pokeldn/app/plugin_store.py does: "pokeldn plugin signature 1" + id + version + sorted
"<sha256>  <name>" lines; `plugin.sig` holds {"key": base64 raw public key, "signature": base64}.
The tool rewrites the package with the signature and verifies it before returning.
"""
import argparse
import hashlib
import json
import subprocess
import tempfile
import zipfile
from pathlib import Path, PurePosixPath

SIGNED = b"pokeldn plugin signature 1\n"
SKIP = ("__pycache__", ".DS_Store", ".installed.json", "plugin.sig")


def manifest(plugin_id: str, version: str, files: dict) -> bytes:
    lines = sorted(f"{hashlib.sha256(data).hexdigest()}  {name}" for name, data in files.items()
                   if name and not any(part in SKIP for part in PurePosixPath(name).parts))
    return SIGNED + f"{plugin_id}\n{version}\n".encode() + "\n".join(lines).encode()


def run(node: str, *args) -> str:
    result = subprocess.run([node, str(Path(__file__).with_name("ed25519.mjs")), *args],
                            capture_output=True, check=True)
    return result.stdout.decode().strip()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("package", type=Path)
    parser.add_argument("--key", type=Path, required=True, help="Ed25519 private key, PKCS#8 PEM")
    parser.add_argument("--node", default="node", help="Node.js executable")
    args = parser.parse_args()

    import tomllib

    with zipfile.ZipFile(args.package) as archive:
        files = {name: archive.read(name) for name in archive.namelist() if not name.endswith("/")}
    meta = tomllib.loads(files["plugin.toml"].decode("utf-8"))
    plugin_id, version = str(meta["id"]), str(meta["version"])
    payload = manifest(plugin_id, version, files)

    data = args.package.with_suffix(".manifest.bin")
    try:
        data.write_bytes(payload)
        public = run(args.node, "pub", str(args.key))
        signature = run(args.node, "sign", str(args.key), str(data))

        files["plugin.sig"] = json.dumps({"key": public, "signature": signature}).encode()
        with zipfile.ZipFile(args.package, "w", zipfile.ZIP_DEFLATED) as archive:
            for name, content in files.items():
                archive.writestr(name, content)

        # Verify exactly what the app will read back.
        with zipfile.ZipFile(args.package) as archive:
            signed_files = {name: archive.read(name) for name in archive.namelist() if not name.endswith("/")}
        result = run(args.node, "verify", public, str(data), signature)
        if result != "ok":
            raise SystemExit("signature verification failed")
        if manifest(plugin_id, version, signed_files) != payload:
            raise SystemExit("manifest changed after signing")
    finally:
        data.unlink(missing_ok=True)

    print(f"signed {args.package.name} ({plugin_id} {version}); key {public}; "
          f"signature {signature[:16]}…")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
