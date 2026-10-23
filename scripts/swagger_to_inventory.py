#!/usr/bin/env python3
"""Turn Brevo's Swagger 2.0 spec into a flat, agent-friendly endpoint inventory.

Usage: python3 -I swagger_to_inventory.py <swagger.yaml> <out_dir>

Outputs (all deterministic, no LLM involved):
  api_endpoints.json   one record per operation, with $refs resolved to inline JSON Schema
  api_summary.md       counts per tag, for sanity checks against the UI crawl
"""
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

import yaml

HTTP_METHODS = {"get", "post", "put", "patch", "delete"}
# The public spec carries example values: sample JWTs, key-shaped strings and a few real-looking addresses. None belongs in a
# catalog that must hold no credentials or identifiers, so every string is passed through redact() before it is written.
PLACEHOLDER_DOMAINS = {"example.com", "example.org", "example.net", "myshop.com", "myshop.fr", "mycompany.com", "company.com",
                       "domain.com", "relay.domain.com", "abc.com", "contact.com"}
JWT = re.compile(r"eyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}")
KEY = re.compile(r"x(?:keysib|smtpsib)-[A-Za-z0-9-]{8,}")
EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@([A-Za-z0-9.-]+\.[A-Za-z]{2,})")
MAX_DEPTH = 6  # guards against recursive definitions


def redact(node):
    if isinstance(node, str):
        node = JWT.sub("REDACTED-DOC-EXAMPLE-JWT", node)
        node = KEY.sub(lambda m: m.group(0).split("-")[0] + "-REDACTED-DOC-EXAMPLE", node)
        return EMAIL.sub(lambda m: m.group(0) if m.group(1).lower() in PLACEHOLDER_DOMAINS else "user@example.com", node)
    if isinstance(node, dict):
        return {k: redact(v) for k, v in node.items()}
    if isinstance(node, list):
        return [redact(v) for v in node]
    return node


def resolve(node, defs, depth=0, seen=()):
    """Inline #/definitions/* references; stop on cycles or excess depth."""
    if depth > MAX_DEPTH:
        return {"note": "max depth reached"}
    if isinstance(node, dict):
        if "$ref" in node:
            name = node["$ref"].split("/")[-1]
            if name in seen:
                return {"$circular": name}
            return resolve(defs.get(name, {}), defs, depth + 1, seen + (name,))
        return {k: resolve(v, defs, depth, seen) for k, v in node.items()}
    if isinstance(node, list):
        return [resolve(v, defs, depth, seen) for v in node]
    return node


def clean_param(p, defs):
    out = {
        "name": p.get("name"),
        "in": p.get("in"),
        "required": bool(p.get("required", False)),
    }
    for key in ("type", "format", "enum", "default", "description", "items", "minimum", "maximum"):
        if key in p:
            out[key] = p[key]
    if "schema" in p:
        out["schema"] = resolve(p["schema"], defs)
    return out


def main(swagger_path, out_dir):
    spec = yaml.safe_load(Path(swagger_path).read_text(encoding="utf-8"))
    defs = spec.get("definitions", {})
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    records = []
    for path, item in spec["paths"].items():
        shared = item.get("parameters", [])
        for method, op in item.items():
            if method not in HTTP_METHODS:
                continue
            params = [clean_param(p, defs) for p in shared + op.get("parameters", [])]
            responses = {}
            for code, r in (op.get("responses") or {}).items():
                responses[str(code)] = {
                    "description": r.get("description"),
                    **({"schema": resolve(r["schema"], defs)} if "schema" in r else {}),
                }
            records.append(
                {
                    "operation_id": op.get("operationId"),
                    "tag": (op.get("tags") or ["untagged"])[0],
                    "method": method.upper(),
                    "path": path,
                    "summary": op.get("summary"),
                    "description": op.get("description"),
                    "parameters": params,
                    "responses": responses,
                    "deprecated": bool(op.get("deprecated", False)),
                }
            )

    records = redact(records)
    records.sort(key=lambda r: (r["tag"], r["path"], r["method"]))
    (out / "api_endpoints.json").write_text(
        json.dumps(records, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    by_tag = defaultdict(list)
    for r in records:
        by_tag[r["tag"]].append(r)
    counts = Counter({t: len(v) for t, v in by_tag.items()})

    lines = [
        f"# API inventory summary",
        f"",
        f"Source: {Path(swagger_path).name} (spec version {spec['info'].get('version')})",
        f"Total operations: {len(records)} across {len(by_tag)} tags",
        f"Deprecated operations: {sum(r['deprecated'] for r in records)}",
        f"",
        f"| Tag | Operations |",
        f"|---|---|",
    ]
    for tag, n in counts.most_common():
        lines.append(f"| {tag} | {n} |")
    (out / "api_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"{len(records)} operations, {len(by_tag)} tags -> {out}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])
