"""Verify a packaged .pokeplugin without pokeldn: structure, manifest and Ed25519 signature.

    python tools/verify_package.py packages/pokeldn-zh-Hans-1.0.0.pokeplugin [--node node]

The manifest is the one pokeldn/app/plugin_store.py checks: "pokeldn plugin signature 1" + id +
version + sorted "<sha256>  <name>" lines. Signature checking uses tools/ed25519.mjs (Node.js), so
this works in CI with no Python dependencies.
"""
import argparse
import hashlib
import base64
import json
import subprocess
import sys
import tomllib
import zipfile
from pathlib import Path, PurePosixPath

SIGNED = b"pokeldn plugin signature 1\n"
SKIP = ("__pycache__", ".DS_Store", ".installed.json", "plugin.sig")
REQUIRED = {"plugin.toml", "strings.toml", "icon.png", "LICENSE"}
FORBIDDEN = (".py", ".exe", ".dll", ".pyd", ".so", ".bin", ".jar")


def manifest(plugin_id: str, version: str, files: dict) -> bytes:
    lines = sorted(f"{hashlib.sha256(data).hexdigest()}  {name}" for name, data in files.items()
                   if name and not any(part in SKIP for part in PurePosixPath(name).parts))
    return SIGNED + f"{plugin_id}\n{version}\n".encode() + "\n".join(lines).encode()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("package", type=Path)
    parser.add_argument("--node", default="node")
    args = parser.parse_args(argv)

    with zipfile.ZipFile(args.package) as archive:
        names = [n for n in archive.namelist() if not n.endswith("/")]
        files = {name: archive.read(name) for name in names}

    errors = []
    missing = sorted(REQUIRED - set(files))
    if missing:
        errors.append(f"missing required files: {missing}")
    if "plugin.sig" not in files:
        errors.append("unsigned package")
    if any(name.startswith("/") or ".." in PurePosixPath(name).parts for name in names):
        errors.append("path traversal in package")
    code = [name for name in names if name.lower().endswith(FORBIDDEN)]
    if code:
        errors.append(f"executable or source files in a data-only pack: {code}")
    if len(files) > 2000:
        errors.append("too many files")

    meta = tomllib.loads(files["plugin.toml"].decode("utf-8"))
    plugin_id, version = str(meta["id"]), str(meta["version"])
    if "plugin.sig" in files:
        signed = json.loads(files["plugin.sig"])
        key = signed.get("key", "")
        signature = signed.get("signature", "")
        try:
            if len(base64.b64decode(key, validate=True)) != 32:
                errors.append("public key is not 32 bytes")
        except ValueError:
            errors.append("public key is not base64")
        payload = manifest(plugin_id, version, files)
        data = args.package.with_suffix(".manifest.bin")
        try:
            data.write_bytes(payload)
            result = subprocess.run([args.node, str(Path(__file__).with_name("ed25519.mjs")),
                                     "verify", key, str(data), signature], capture_output=True)
            if result.returncode != 0:
                errors.append(f"signature does not verify: {result.stderr.decode()[:200]}")
            else:
                print(f"signature: ok ({key})")
        finally:
            data.unlink(missing_ok=True)

    print(f"{args.package.name}: {plugin_id} {version}, {len(files)} files, "
          f"{args.package.stat().st_size} bytes, sha256 {hashlib.sha256(args.package.read_bytes()).hexdigest()}")
    for error in errors:
        print(f"ERROR: {error}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
