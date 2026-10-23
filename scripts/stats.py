#!/usr/bin/env python3
"""Print the headline numbers of the compiled catalog (used to fill the write-up)."""
import json
import sys
from collections import Counter
from pathlib import Path

c = json.loads((Path(sys.argv[1]) / "catalog.json").read_text(encoding="utf-8"))["actions"]
ui_only = [a for a in c if "api" not in a["execution"]]
both = [a for a in c if "api" in a["execution"] and "ui" in a["execution"]]
api_only = [a for a in c if "api" in a["execution"] and "ui" not in a["execution"]]
t = Counter(a["tier"] for a in c)
print(f"actions {len(c)}; tier A {t['A']}, B {t['B']}, C {t.get('C', 0)}")
print(f"ui only {len(ui_only)}, api+ui {len(both)}, api only {len(api_only)}")
print("free plan:", dict(Counter(a['plan_availability'].get('free') for a in c)))
print("needs human yes:", sum(a['requires_human_confirmation'] for a in c))
print("risk:", dict(Counter(a['risk'] for a in c)))
