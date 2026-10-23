# Helper used to author hand-written, UI-only catalog actions with consistent defaults.
# Usage inside a script:  exec(open('scripts/uimk.py').read())
import pathlib
import yaml

ROOT = pathlib.Path('.')
T = "2026-10-22"
AVAIL = {"free": "available"}


def dump(path, d):
    path = pathlib.Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(d, sort_keys=False, allow_unicode=True, width=110), encoding='utf-8')


def ui_only(id_, summary, label, risk, steps, entry, inputs, post, evidence, ver, via=None, notes="", plan=None,
            pre=None, se=None, errors=None, conf=False, reversible=True, outputs=None, internal=None, limits=None,
            depends=None, sources=None):
    d = {"id": id_, "domain": id_.split(".")[0], "summary": summary, "ui_label_pt": label, "risk": risk,
         "reversible": reversible, "requires_human_confirmation": conf or risk in ("destructive", "external_effect"),
         "plan_availability": plan or AVAIL, "preconditions": pre or [], "inputs": inputs}
    if outputs:
        d["outputs"] = outputs
    d.update({"side_effects": se or ["Changes account data."], "postcondition_check": post, "errors": errors or [],
              "limits": limits or [], "depends_on": depends or [],
              "execution": {"preferred": "ui", "ui": {"entry": entry, "steps": steps, **({"internal_service": internal} if internal else {})}},
              "provenance": {"sources": sources or ["ui"], "verification": ver, "verified_at": T, "evidence": evidence,
                             **({"verified_via": via} if via else {}), "notes": notes}})
    return d


def save_actions(actions, folder):
    for a in actions:
        dump(ROOT / "actions" / folder / (a["id"].split(".", 1)[1] + ".yaml"), a)
    print(len(actions), "actions written to actions/" + folder)


def idobj(name="id", desc=""):
    return {"type": "object", "required": [name], "properties": {name: {"type": "integer", "description": desc}}}
