#!/usr/bin/env python3
"""Generate one catalog action per automation-editor step type (triggers, actions, rules).

Source of truth: reference/automation_nodes.json (what was seen in the UI and how far it was verified).
Output: actions/_generated_ui/automations/*.yaml. Run: python3 -I scripts/gen_automation_actions.py <repo-root>

The verification tier of each generated action follows the observation level of the node:
  executed_saved  -> executed_verified (verified_via: ui)
  panel_observed  -> observed_not_executed
  palette_only    -> observed_not_executed, with an explicit note that no setting was seen
"""
import json
import shutil
import sys
from pathlib import Path

import yaml

EVIDENCE = "evidence/automations.build_steps.json"
HAND_WRITTEN_SLUGS = {("trigger", "contact_added_to_list")}  # actions/automations/configure_trigger_contact_added_to_list.yaml
TODAY = "2026-10-22"
VERB = {"trigger": "configure_trigger", "action": "add_action", "rule": "add_rule"}
KIND_EN = {"trigger": "trigger", "action": "action step", "rule": "rule step"}


def build(node, root):
    kind, slug = node["kind"], node["slug"]
    ident = f"automations.{VERB[kind]}_{slug}"
    level = node["level"]
    label = node["label_pt"]
    props = {}
    required = []
    for f in node["fields"]:
        p = {"type": f["type"], "description": f"UI label '{f['ui_label_pt']}'." + (" " + f["description"] if f.get("description") else "")}
        if f.get("enum"):
            p["enum"] = f["enum"]
        if f["type"] == "array":
            p["items"] = {"type": "string"}
        props[f["name"]] = p
        if f.get("required"):
            required.append(f["name"])
    config = {"type": "object", "properties": props}
    if required:
        config["required"] = required
    if level == "palette_only":
        config["description"] = "Settings of this step were NOT opened in the UI, so the fields are unknown. Open the step in the editor and read its panel before relying on this entry."
        config["additionalProperties"] = True
    inputs = {"type": "object", "required": ["automation_id"], "properties": {
        "automation_id": {"type": "integer", "description": "ID of the draft automation, as shown in /automation/edit/<id>."},
        "config": config}}
    if kind != "trigger":
        inputs["properties"]["after_step_id"] = {"type": "integer", "description": "Optional. Step to attach the block after; by default the block goes at the end of the flow."}
    risk = node.get("risk") or "write"
    pre = ["A draft automation exists (automations.create_automation) and its editor is open at /automation/edit/<id>."]
    if kind == "trigger":
        pre.append("The canvas has no trigger yet. A second trigger could not be dropped onto a canvas that already had one.")
    else:
        pre.append("The automation has a trigger (see the configure_trigger_* actions).")
    if node["gated_in_free"]:
        pre.append("This block shows a crown icon in the free plan palette, so it is plan-gated.")
    if node.get("notes"):
        pre.append(node["notes"])
    if level == "executed_saved":
        se = ["Changes the draft only. Observed: nothing ran and the automation stayed inactive (Desativada)."]
    else:
        se = ["Expected (from the label, not seen): changes the draft only. Nothing runs while the automation is inactive (Desativada)."]
    if node.get("latent_effect"):
        le = node["latent_effect"]
        se.append("Expected (not seen; no automation was ever activated): once the automation is activated, " + le[0].lower() + le[1:])
    steps = [
        "Open /automation/edit/<automation_id>.",
        f"In the palette choose the tab '{ {'trigger': 'Gatilhos', 'action': 'Ações', 'rule': 'Regras'}[kind] }' (or type part of the name in 'Buscar por nome da etapa').",
        f"Drag the block '{label}' onto the dashed zone 'Solte o bloco aqui'" + (" at the top of the canvas." if kind == "trigger" else " between two steps, or on a connector."),
        "Wait about 3 seconds after any undo before dragging again, otherwise the editor can stay stuck in the drag state until the page is reloaded.",
    ]
    if node["fields"]:
        steps.append("In the side panel fill: " + "; ".join(f"'{f['ui_label_pt']}'" + ("*" if f.get("required") else "") for f in node["fields"]) + ".")
    elif level != "palette_only":
        steps.append("The panel has no settings to fill.")
    else:
        steps.append("Read the side panel that opens; its fields were not recorded.")
    steps.append("Press 'Salvar' in the panel. 'Cancelar' leaves an unsaved card marked 'Defina e salve essa ação.'.")
    verif = "executed_verified" if level == "executed_saved" else "observed_not_executed"
    prov = {"sources": ["ui"], "verification": verif, "verified_at": TODAY, "evidence": EVIDENCE if kind != "trigger" or level != "palette_only" else "evidence/automations.create_automation.json"}
    if verif == "executed_verified":
        prov["verified_via"] = ["ui"]
        prov["notes"] = "Dropped, configured and saved on the inactive draft automation; the canvas card showed the choice."
    elif level == "panel_observed":
        prov["notes"] = "The block was dropped and its settings panel was read, then cancelled. The save was not exercised."
    else:
        prov["notes"] = "Only the palette entry was seen. No block was dropped, so the settings are unknown."
    if node["gated_in_free"]:
        plan = {"free": "blocked", "note": "Crown icon in the palette of the free account."}
    elif level == "palette_only":
        plan = {"free": "unknown", "note": "Seen in the palette without a crown, but never dropped on the canvas."}
    else:
        plan = {"free": "available"}
    summary_kind = KIND_EN[kind]
    d = {
        "id": ident, "domain": "automations",
        "summary": f"Add the {summary_kind} '{label}' ({node['group']}) to an automation. UI only.",
        "ui_label_pt": label, "risk": risk, "reversible": risk != "destructive",
        "requires_human_confirmation": risk == "destructive",
        "plan_availability": plan, "preconditions": pre, "inputs": inputs,
        "outputs": {"type": "object", "properties": {"step_id": {"type": "integer", "description": "Shown as 'ID da etapa #N' in the panel. IDs are allocated at drop time and are not reused after an undo."}}},
        "side_effects": se,
        "postcondition_check": "The canvas card shows the saved choice instead of the orange 'Defina e salve essa ação.', and the header reads 'Salva hoje às HH:MM'.",
        "errors": [{"condition": "Step left unsaved or incomplete", "symptom": "Card shows 'Defina e salve essa ação.' in orange.", "recovery": "Open the card, fill the required fields and press Salvar, or remove the card with the undo arrow or the card menu."}],
        "limits": [], "depends_on": ["automations.create_automation"],
        "execution": {"preferred": "ui", "ui": {"entry": "/automation/edit/<automation_id>", "steps": steps}},
        "provenance": prov,
    }
    if node.get("latent_effect"):
        d["description"] = ("Adding this step only changes the draft. What it does to contacts starts when the automation is activated "
                            "(automations.activate_automation), and activation always needs an explicit human yes.")
    return ident, d


def main(root):
    root = Path(root)
    data = json.loads((root / "reference/automation_nodes.json").read_text(encoding="utf-8"))
    out = root / "actions/_generated_ui/automations"
    if out.parent.exists():
        shutil.rmtree(out.parent)
    out.mkdir(parents=True)
    n = 0
    for node in data["nodes"]:
        if (node["kind"], node["slug"]) in HAND_WRITTEN_SLUGS:
            continue
        ident, d = build(node, root)
        (out / f"{ident.split('.', 1)[1]}.yaml").write_text(yaml.safe_dump(d, sort_keys=False, allow_unicode=True, width=110), encoding="utf-8")
        n += 1
    print(f"generated {n} automation step actions")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
