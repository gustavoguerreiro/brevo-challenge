#!/usr/bin/env python3
"""Negative control: a plan made by plain keyword overlap with the index, no reading of risk, plan or guide.

It shows that the scorer does not pass a plan just because it names a plausible action.
Usage: python3 -I eval/baseline_naive.py <catalog_root> <out_answers.json>
"""
import json
import re
import sys
from pathlib import Path

STOP = set("the a an of to and in on for my our i we it is be with that this use as at by from you me can do not now all so up".split())


def words(s):
    return {w for w in re.findall(r"[a-z]+", s.lower()) if w not in STOP and len(w) > 2}


def main(root, out):
    root = Path(root)
    cat = json.loads((root / "catalog.json").read_text(encoding="utf-8"))["actions"]
    tasks = json.loads((root / "eval/tasks.json").read_text(encoding="utf-8"))
    answers = []
    for t in tasks:
        q = words(t["prompt"])
        scored = sorted(cat, key=lambda a: -len(q & words(a["id"].replace("_", " ").replace(".", " ") + " " + a["summary"])))
        best = scored[0]
        answers.append({"task_id": t["id"], "decision": "act", "actions": [best["id"]],
                        "route": {best["id"]: best["execution"]["preferred"]}, "inputs": {}, "needs_confirmation": [],
                        "warnings": [], "summary": ""})
    Path(out).write_text(json.dumps(answers, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
