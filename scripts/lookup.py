#!/usr/bin/env python3
"""Small helper so that an agent (or a person) does not have to load the whole catalog.json (1.5 MB).

Usage:
  python3 -I scripts/lookup.py <catalog_root> get <action_id> [--full]   print one action (every field an agent needs; --full adds file and tier)
  python3 -I scripts/lookup.py <catalog_root> search <word> [<word> ...]  list ids whose id, summary or UI label match all words
  python3 -I scripts/lookup.py <catalog_root> deps <action_id>            print the action and the actions that can prepare what it needs
                                                                           (candidates: run one only if the needed object is missing)
  python3 -I scripts/lookup.py <catalog_root> related <action_id>         actions that reach the same capability by another door
"""
import json
import sys
from pathlib import Path

COMPACT = ["id", "summary", "description", "ui_label_pt", "risk", "requires_human_confirmation", "reversible", "plan_availability",
           "preconditions", "inputs", "outputs", "side_effects", "postcondition_check", "errors", "limits", "depends_on", "related",
           "execution", "provenance"]


def load(root):
    return {a["id"]: a for a in json.loads((Path(root) / "catalog.json").read_text(encoding="utf-8"))["actions"]}


def show(a, full=False):
    d = a if full else {k: a[k] for k in COMPACT if k in a}
    print(json.dumps(d, indent=1, ensure_ascii=False))


def order(cat, aid, seen=None):
    seen = seen if seen is not None else []
    for d in cat[aid].get("depends_on", []):
        if d not in seen:
            order(cat, d, seen)
    if aid not in seen:
        seen.append(aid)
    return seen


def main(argv):
    if len(argv) < 3:
        sys.exit(__doc__)
    cat = load(argv[0])
    cmd = argv[1]
    if cmd == "get":
        if argv[2] not in cat:
            sys.exit(f"unknown action id: {argv[2]}")
        show(cat[argv[2]], "--full" in argv)
    elif cmd == "search":
        words = [w.lower() for w in argv[2:]]
        for aid, a in sorted(cat.items()):
            hay = " ".join([aid, a["summary"], a.get("ui_label_pt", "")]).lower()
            if all(w in hay for w in words):
                print(f"{aid} [{a['tier']}, {a['risk']}] {a['summary']}")
    elif cmd == "related":
        if argv[2] not in cat:
            sys.exit(f"unknown action id: {argv[2]}")
        for aid in cat[argv[2]].get("related", []):
            print(f"{aid} [{cat[aid]['tier']}, {cat[aid]['risk']}] {cat[aid]['summary']}")
    elif cmd == "deps":
        if argv[2] not in cat:
            sys.exit(f"unknown action id: {argv[2]}")
        for aid in order(cat, argv[2]):
            print(f"{aid} [{cat[aid]['tier']}, {cat[aid]['risk']}] {cat[aid]['summary']}")
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main(sys.argv[1:])
