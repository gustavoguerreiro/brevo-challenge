#!/usr/bin/env python3
"""Scan the repository for credentials and personal identifiers before it is packaged or sent.

Usage: python3 -I scripts/scan_secrets.py <repo_root>

What it flags (any hit exits non-zero and lists file:line, never the matched text):
  - Brevo API or SMTP key shapes (xkeysib-..., xsmtpsib-...) that are not the redaction placeholder
  - JSON Web Tokens
  - Brevo SMTP login shapes (<id>@smtp-brevo.com)
  - assignments of api key, password, secret or token to a long literal
  - any e-mail address whose domain is not in the placeholder allowlist (example.com and the spec's own sample domains)
  - anything listed, one per line, in the file named by the SCAN_DENY_FILE environment variable (use it for the real owner
    address, names and ids; keep that file OUTSIDE the repository so that no real identifier is hard-coded here)

It skips sources/ (a third-party SDK snapshot that is not delivered), deliver/ (drafts that hold names on purpose),
caches and binary files. It reads text only, so it cannot see inside images or archives.
"""
import os
import re
import sys
from pathlib import Path

SKIP_DIRS = {"sources", "deliver", "__pycache__", ".git"}
PLACEHOLDER_DOMAINS = {"example.com", "example.org", "example.net", "myshop.com", "myshop.fr", "mycompany.com", "company.com",
                       "domain.com", "relay.domain.com", "abc.com", "contact.com",
                       "notacme.com"}  # an invented example in a blind-evaluation answer (eval/results/run3_nocatalog), not a real address
PATTERNS = {
    "brevo key shape": re.compile(r"x(?:keysib|smtpsib)-(?!REDACTED)[A-Za-z0-9-]{16,}"),
    "jwt": re.compile(r"eyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}"),
    "smtp login shape": re.compile(r"\b[0-9a-z]{6,}@smtp-brevo\.com\b"),
    "secret assignment": re.compile(r"(?i)\b(api[-_ ]?key|password|passwd|secret|token)\b\s*[:=]\s*['\"]?[A-Za-z0-9_\-/+=]{24,}"),
}
EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@([A-Za-z0-9.-]+\.[A-Za-z]{2,})")


def main(root):
    root = Path(root)
    deny = []
    deny_file = os.environ.get("SCAN_DENY_FILE")
    if deny_file:
        deny = [ln.strip().lower() for ln in Path(deny_file).read_text(encoding="utf-8").splitlines() if ln.strip()]
    hits, scanned = [], 0
    for p in sorted(root.rglob("*")):
        if not p.is_file() or any(part in SKIP_DIRS for part in p.relative_to(root).parts):
            continue
        if p.suffix.lower() in (".zip", ".png", ".jpg", ".jpeg", ".gif", ".pdf", ".pyc"):
            continue
        try:
            text = p.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        scanned += 1
        rel = p.relative_to(root)
        for no, line in enumerate(text.splitlines(), 1):
            for name, pat in PATTERNS.items():
                if pat.search(line):
                    hits.append(f"{rel}:{no}: {name}")
            for m in EMAIL.finditer(line):
                if m.group(1).lower() not in PLACEHOLDER_DOMAINS:
                    hits.append(f"{rel}:{no}: e-mail address outside the placeholder domains")
            low = line.lower()
            for d in deny:
                if d in low:
                    hits.append(f"{rel}:{no}: matches an entry of the deny file")
    if hits:
        print(f"SCAN FAILED: {len(hits)} hit(s) in {scanned} files")
        for h in hits[:100]:
            print(" -", h)
        sys.exit(1)
    print(f"scan clean: {scanned} text files, {'with' if deny else 'without'} a deny file")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
