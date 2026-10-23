#!/usr/bin/env python3
"""Build the input of the raw-API baseline: what someone has if all they have is Brevo's public API specification.

Usage: python3 -I eval/make_api_baseline_input.py <catalog_root> <out.json>

One row per operation of the SDK snapshot that still exists in the live spec: method, path, tag, operation id, summary and the
names of the parameters. No ids from the catalog, no risk, no plan, no UI knowledge.
"""
import json
import sys
from pathlib import Path


def main(root, out):
    root = Path(root)
    ops = json.loads((root / "inventory/api_endpoints.json").read_text(encoding="utf-8"))
    live = {(a["method"], a["path"]) for a in json.loads((root / "inventory/api_endpoints_live.json").read_text(encoding="utf-8")) if a.get("in_live")}
    rows = []
    for o in ops:
        if (o["method"], o["path"]) not in live:
            continue
        rows.append({"method": o["method"], "path": o["path"], "tag": o["tag"], "operation_id": o["operation_id"],
                     "summary": o.get("summary"), "parameters": [p.get("name") for p in o.get("parameters", []) if isinstance(p, dict)]})
    Path(out).write_text(json.dumps(rows, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"{len(rows)} operations written")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])
