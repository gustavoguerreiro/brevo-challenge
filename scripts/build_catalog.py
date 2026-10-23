#!/usr/bin/env python3
"""Validate every action YAML and compile the agent-facing catalog.

Usage: python3 -I build_catalog.py <catalog_root>

Checks (any failure exits non-zero):
  1. Each action validates against schema/action.schema.json.
  2. `inputs` / `outputs` are themselves valid JSON Schema.
  3. ids are unique and start with "<domain>.".
  4. depends_on points at existing ids.
  5. executed_verified actions point at an evidence file that exists.
  6. Any execution.api method+path exists in inventory/api_endpoints_live.json with in_live=true
     (catches invented, misspelled or removed endpoints).
  7. No credential-looking strings anywhere in the YAML.
  8. Every cited evidence file exists and is valid JSON; ui.entry is an ASCII path or URL.
     (The build checks that evidence files exist and parse. It does not check what they say.)
  9. Risk lint (see lint_risk): delete is destructive; send and schedule are external effects; anything that
     can schedule a send through an input is an external effect; external effects and destructive actions
     need a human yes and are not reversible; inputs that change consent need an explicit-yes precondition.
 10. Claims lint (see lint_claims): every side effect of a tier B action starts with Expected, Observed or Not observed.

Outputs: catalog.json, index.md (one line per action, for cheap loading), coverage.md
"""
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

CREDENTIAL_PATTERNS = [
    re.compile(r"xkeysib-[A-Za-z0-9-]{20,}"),
    re.compile(r"xsmtpsib-[A-Za-z0-9-]{20,}"),
    re.compile(r"(?i)api[-_ ]?key\s*[:=]\s*['\"]?[A-Za-z0-9_-]{24,}"),
    re.compile(r"(?i)password\s*[:=]\s*\S{6,}"),
]
TIER = {
    "executed_verified": "A",
    "observed_not_executed": "B",
    "documented_only": "B",
    "inferred": "C",
}


# Actions the summary-based lint would flag although they are fine. Each entry says why.
LINT_ALLOW = {
    "conversations.update_message": "'sent by an agent' describes the message, the action edits text only",
    "automations.configure_trigger_coupon_sent": "'Unique coupon sent' is the name of a trigger, nothing is sent",
    "email_campaigns.create_campaign": "draft only; the schedule fields are deliberately not inputs (see its preconditions)",
    "sms_whatsapp.create_sms_campaign": "draft only; the schedule field is deliberately not an input (see its preconditions)",
}
SCHEDULE_INPUT = re.compile(r"(?i)schedul|sendat|send_at|sendnow")
SEND_WORDS = re.compile(r"(?i)\b(sends?|schedul\w+)\b")
CONSENT_INPUT = re.compile(r"(?i)blacklist|blocklist")


def lint_risk(a):
    """Return a list of problems with the risk labelling of one action. Mislabelled risk is the most dangerous kind of error here."""
    out = []
    aid, risk = a["id"], a["risk"]
    verb = aid.split(".", 1)[1].split("_", 1)[0]
    props = (a.get("inputs") or {}).get("properties") or {}
    allowed = aid in LINT_ALLOW
    if verb == "delete" and risk != "destructive":
        out.append(f"{aid}: verb delete but risk is {risk}")
    if verb in ("send", "schedule") and risk != "external_effect":
        out.append(f"{aid}: verb {verb} but risk is {risk}")
    sched = [k for k in props if SCHEDULE_INPUT.search(k)]
    if sched and risk != "external_effect" and not allowed:
        out.append(f"{aid}: input(s) {sched} can schedule a send but risk is {risk}")
    if risk == "write" and SEND_WORDS.search(a.get("summary", "")) and not allowed:
        out.append(f"{aid}: summary mentions sending or scheduling but risk is write")
    if risk in ("external_effect", "destructive"):
        if not a.get("requires_human_confirmation"):
            out.append(f"{aid}: {risk} without requires_human_confirmation")
        if a.get("reversible") is not False:
            out.append(f"{aid}: {risk} must have reversible: false")
    if [k for k in props if CONSENT_INPUT.search(k)] and not any("explicit yes" in p for p in a.get("preconditions", [])):
        out.append(f"{aid}: consent input without an 'explicit yes' precondition")
    return out


MARKED = re.compile(r"^(Expected|Not observed|Observed|None)", re.I)


def lint_claims(a):
    """A tier B action was never executed, so every side effect it lists is an expectation unless it says it was observed."""
    out = []
    if a.get("tier") == "B":
        for line in a.get("side_effects", []):
            if not MARKED.match(line):
                out.append(f"{a['id']}: tier B side effect without an Expected / Observed / Not observed marker: {line[:60]!r}")
    return out


def api_key(method, path):
    # normalise {param} names so /contacts/{identifier} matches /contacts/{id}
    return method.upper(), re.sub(r"\{[^}]+\}", "{}", path)


def main(root):
    root = Path(root)
    schema = json.loads((root / "schema/action.schema.json").read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)
    inventory = json.loads((root / "inventory/api_endpoints_live.json").read_text(encoding="utf-8"))
    # only operations present in the live spec are acceptable targets (removed ones must not be catalogued)
    known_api = {api_key(r["method"], r["path"]) for r in inventory if r.get("in_live")}

    actions, errors = [], []
    for f in sorted((root / "actions").rglob("*.yaml")):
        raw = f.read_text(encoding="utf-8")
        for pat in CREDENTIAL_PATTERNS:
            if pat.search(raw):
                errors.append(f"{f.name}: credential-looking string matches {pat.pattern}")
        try:
            a = yaml.safe_load(raw)
        except yaml.YAMLError as e:
            errors.append(f"{f.name}: YAML error {e}")
            continue
        for err in validator.iter_errors(a):
            loc = "/".join(str(p) for p in err.absolute_path) or "(root)"
            errors.append(f"{f.name}: {loc}: {err.message[:160]}")
        for key in ("inputs", "outputs"):
            if key in a:
                try:
                    Draft202012Validator.check_schema(a[key])
                except Exception as e:
                    errors.append(f"{f.name}: {key} is not valid JSON Schema: {str(e)[:120]}")
        if not str(a.get("id", "")).startswith(str(a.get("domain", "?")) + "."):
            errors.append(f"{f.name}: id must start with its domain")
        ev = a.get("provenance", {}).get("evidence")
        if a.get("provenance", {}).get("verification") == "executed_verified":
            if not ev or not (root / ev).exists():
                errors.append(f"{f.name}: executed_verified needs an existing evidence file")
        if a.get("provenance", {}).get("verification") == "executed_verified":
            via = a.get("provenance", {}).get("verified_via")
            if not via:
                errors.append(f"{f.name}: executed_verified needs provenance.verified_via (ui and/or api)")
            for path_kind in via or []:
                if path_kind not in a.get("execution", {}):
                    errors.append(f"{f.name}: verified_via lists '{path_kind}' but execution has no such path")
        # any cited evidence file must exist and be valid JSON (not only for tier A)
        if ev:
            if not (root / ev).exists():
                errors.append(f"{f.name}: evidence file {ev} does not exist")
            else:
                try:
                    json.loads((root / ev).read_text(encoding="utf-8"))
                except ValueError as e:
                    errors.append(f"{f.name}: evidence file {ev} is not valid JSON: {str(e)[:80]}")
        # UI entry routes must be plain ASCII paths or URLs (an accent-normalisation pass once turned /logs/scenarios into a path with an accent)
        ui_entry = (a.get("execution", {}).get("ui") or {}).get("entry")
        if ui_entry is not None and (not ui_entry.isascii() or not (ui_entry.startswith("/") or ui_entry.startswith("http"))):
            errors.append(f"{f.name}: ui.entry must be an ASCII path or URL, got {ui_entry!r}")
        api = a.get("execution", {}).get("api")
        if api and api_key(api["method"], api["path"]) not in known_api:
            errors.append(f"{f.name}: API {api['method']} {api['path']} not in the live spec inventory")
        a["_file"] = str(f.relative_to(root))
        a["tier"] = TIER.get(a.get("provenance", {}).get("verification"), "C")
        actions.append(a)

    for a in actions:
        errors += lint_risk(a)
        errors += lint_claims(a)
    ids = Counter(a["id"] for a in actions if "id" in a)
    errors += [f"duplicate id {i}" for i, n in ids.items() if n > 1]
    for a in actions:
        for field in ("depends_on", "related"):
            for d in a.get(field, []):
                if d not in ids:
                    errors.append(f"{a['id']}: {field} unknown id {d}")
                if d == a["id"]:
                    errors.append(f"{a['id']}: {field} points at itself")

    if errors:
        print(f"FAILED with {len(errors)} problem(s):")
        for e in errors:
            print(" -", e)
        sys.exit(1)

    (root / "catalog.json").write_text(
        json.dumps({"catalog": "brevo", "actions": actions}, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )
    by_domain = defaultdict(list)
    for a in actions:
        by_domain[a["domain"]].append(a)
    lines = ["# Brevo action index", "", "Load this first, together with AGENT_GUIDE.md (rules for using the catalog). Fetch the full spec of one action from catalog.json by id.", "",
             "Legend: tier A = executed through the route(s) in `verified_via` and read back, B = observed or documented, not executed, C = inferred. risk: read / write / destructive / external_effect. `blocked on Free` = the feature needs a paid plan.", ""]
    for dom in sorted(by_domain):
        lines.append(f"## {dom}")
        for a in sorted(by_domain[dom], key=lambda x: x["id"]):
            vv = a.get("provenance", {}).get("verified_via")
            vtxt = f", verified via {'+'.join(vv)}" if vv else ""
            if vv and a["execution"]["preferred"] not in vv:
                vtxt += f" ({a['execution']['preferred']} route NOT run)"
            conf = ", needs human OK" if a.get("requires_human_confirmation") else ""
            blocked = ", blocked on Free" if a.get("plan_availability", {}).get("free") == "blocked" else ""
            lines.append(f"- `{a['id']}` [{a['tier']}, {a['risk']}{conf}{blocked}, use {a['execution']['preferred']}{vtxt}] {a['summary']}")
        lines.append("")
    (root / "index.md").write_text("\n".join(lines), encoding="utf-8")

    tiers = Counter(a["tier"] for a in actions)
    cov = ["# Coverage", "", f"Actions: {len(actions)}", "",
           "| Tier | Count |", "|---|---|"] + [f"| {t} | {tiers.get(t, 0)} |" for t in "ABC"] + ["",
           "| Domain | Actions |", "|---|---|"] + [f"| {d} | {len(v)} |" for d, v in sorted(by_domain.items())]
    (root / "coverage.md").write_text("\n".join(cov) + "\n", encoding="utf-8")
    print(f"OK: {len(actions)} actions, tiers {dict(tiers)}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
