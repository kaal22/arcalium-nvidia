#!/usr/bin/env python3
import json
import pathlib
import subprocess
import sys

repo = pathlib.Path(r"/mnt/c/Users/Kaal/Desktop/Antigravity Websites/KAAL Business/Arcalium NVIDIA")
notes = (repo / "output/release-0.2.1-notes.md").read_text(encoding="utf-8")
payload = {
    "tag_name": "0.2.1",
    "target_commitish": "b6d5ccc0dee4d50de97c2e277bc1e8d5729ad3e7",
    "name": "Arcalium OS NVIDIA Edition 0.2.1",
    "body": notes,
    "draft": False,
    "prerelease": False,
    "make_latest": "true",
}
payload_path = repo / "output/release-0.2.1-payload.json"
payload_path.write_text(json.dumps(payload), encoding="utf-8")
print("wrote", payload_path)

r = subprocess.run(
    [
        "gh",
        "api",
        "-X",
        "POST",
        "repos/kaal22/arcalium-nvidia/releases",
        "--input",
        str(payload_path),
    ],
    capture_output=True,
    text=True,
)
print(r.stdout)
print(r.stderr, file=sys.stderr)
sys.exit(r.returncode)
