#!/usr/bin/env python3
"""Generate catalog actions for every Brevo public API operation not covered by a hand-written action.

Inputs
  inventory/api_endpoints.json   Feb 2025 SDK snapshot (full schemas), from swagger_to_inventory.py
  inventory/api_live_delta.json  operations seen only in the live developer-site spec (names and params)
  scripts/api_action_map.txt     curated ids, risk flags, notes (the reviewed layer)
Outputs
  inventory/api_endpoints_live.json   merged list used by build_catalog.py to validate execution.api
  actions/_generated/<domain>/<name>.yaml   one file per operation (rewritten on every run)

The generator refuses to run if any snapshot or live operation has no row in the map, so a new
endpoint cannot be silently skipped. Generated actions are tier B (documented_only): never executed.

Usage: python3 -I gen_api_actions.py <catalog_root>
"""
import json
import re
import shutil
import sys
from pathlib import Path

import yaml

TODAY = "2026-10-22"
SDK_NOTE = ("Generated from the Brevo public API spec (SDK snapshot, Feb 2025). Not executed: the account had no API key. "
            "Also present in the live developer-site spec read on " + TODAY + ".")
LIVE_NOTE = ("Only in the live developer-site spec read on " + TODAY + " (absent from the Feb 2025 snapshot). "
             "Parameter types were not captured, only names and required flags. Not executed.")
GENERIC_RECOVERY = {
    "400": "Fix the request (the response body carries a machine-readable code and message), then retry.",
    "401": "Check the api-key header; the key may be missing, revoked or restricted by IP.",
    "402": "Add credits or upgrade the plan, then retry.",
    "403": "The key or plan lacks permission for this operation; check key permissions and plan features.",
    "404": "The referenced id does not exist; list the parent collection to find a valid id.",
    "405": "Method not allowed for this resource; re-check the path.",
    "422": "The payload is well formed but semantically invalid; fix the field named in the message.",
    "429": "Rate limit reached; wait and retry with backoff.",
}
DOMAIN_PLAN = {
    "loyalty": ("blocked", "The Loyalty module is gated to an Enterprise plan in the UI (observed). The API calls were not tried; they are expected to fail on Free."),
    "custom_objects": ("blocked", "Custom objects redirect to an upgrade page in the UI on Free (observed). The API calls were not tried; they are expected to fail on Free."),
    "ecommerce": ("limited", "Needs the e-commerce integration or activation (UI shows a plug-in prompt on a new account)."),
    "conversations": ("unknown", "Plan availability not checked."),
}
MASTER_PREFIXES = ("account.create_sub_account", "account.update_sub_account", "account.delete_sub_account", "account.get_sub_account",
                   "account.list_sub_account", "account.get_master_account", "account.create_admin", "account.update_admin",
                   "account.remove_admin", "account.invite_admin", "account.list_admin", "account.get_admin", "account.add_ip",
                   "account.remove_ip", "account.configure_sub", "account.remove_sub", "account.list_corporate", "account.update_sub")
EXPECTED = "Expected (from the API docs, not verified): "
SIDE_EFFECTS = {
    "contacts.delete_list": ["Contacts stay in the account but leave the list; automations and campaigns that used the list lose that audience."],
    "contacts.delete_folder": ["Lists inside the folder are deleted too."],
    "contacts.delete_contact": ["The contact and its activity history are removed; automations enrolled for it stop."],
    "contacts.add_contact_to_list": ["Can enrol the contact in automations triggered by 'Contato adicionado à lista'."],
    "contacts.delete_attribute": ["The attribute and all stored values are removed from every contact."],
    "email_campaigns.update_campaign": ["If scheduledAt is set on a campaign that has recipients, the campaign is scheduled to send."],
    "email_campaigns.update_campaign_status": ["Depending on the status value the campaign can be queued to send, suspended or archived."],
    "sms_whatsapp.send_sms_campaign": ["Sends SMS to the campaign recipients and consumes SMS credits."],
    "sms_whatsapp.send_transactional_sms": ["Sends a real SMS and consumes SMS credits."],
    "sms_whatsapp.send_whatsapp_message": ["Sends a real WhatsApp message."],
    "loyalty.publish_program": ["The program becomes visible to members and starts accruing."],
    "account.create_sender": ["Brevo e-mails a verification message to the sender address."],
    "account.invite_user": ["An invitation e-mail goes to the invited address."],
    "account.invite_admin_user": ["An invitation e-mail goes to the invited address."],
    "contacts.create_doi_contact": ["A double opt-in confirmation e-mail goes to the contact."],
    "email_campaigns.send_report": ["The campaign report is e-mailed to the given addresses."],
    "email_campaigns.send_test_email": ["A test copy of the campaign is e-mailed to the given addresses."],
    "crm.create_task": ["Can fire automations triggered by 'Tarefa criada'."],
    "crm.update_task": ["Setting a task done can fire 'Tarefa concluída' automations."],
    "ecommerce.create_order": ["Order events can trigger automations that send messages."],
    "ecommerce.create_payment_request": ["A payment request goes to the customer."],
    "conversations.send_automated_message": ["An automated chat message is pushed to the visitor."],
    "sms_whatsapp.send_whatsapp_template_approval": ["The template is submitted to Meta for approval."],
    "integrations.create_event": ["Custom events can trigger automations and appear in segments."],
    "transactional.send_email": ["Delivers real e-mail to the recipients and counts against the sending allowance; scheduledAt delays it."],
    "contacts.import_contacts": ["The import runs asynchronously; the response carries a process id."],
    "contacts.export_contacts": ["The export runs asynchronously; poll the process."],
    "account.create_sub_account": ["May incur plan costs."],
    "account.create_sub_account_api_key": ["Creates a credential; never store the value."],
    "account.create_admin_sso_token": ["Creates a login token for the admin user."],
    "transactional.remove_blocked_contact": ["The address can receive transactional e-mail again."],
}


def trunc(text, n=240):
    text = re.sub(r"\s+", " ", str(text)).strip()
    if len(text) <= n:
        return text
    cut = text[:n].rsplit(" ", 1)[0].rstrip(",;:- ")
    return cut + " …"


def norm(method, path):
    return method.upper(), re.sub(r"\{[^}]+\}", "{}", path)


def parse_map(path):
    rows = []
    for ln in Path(path).read_text(encoding="utf-8").splitlines():
        ln = ln.strip()
        if not ln or ln.startswith("#"):
            continue
        parts = [p.strip() for p in ln.split("|")]
        parts += [""] * (4 - len(parts))
        mp, ident, flags, note = parts[:4]
        method, p = mp.split(" ", 1)
        rows.append({"method": method, "path": p.strip(), "id": ident, "flags": set(flags.split()), "note": note})
    return rows


def clean(s, depth=0):
    """Make a swagger-2 schema fragment a tidy JSON Schema fragment."""
    if isinstance(s, list):
        return [clean(x, depth + 1) for x in s]
    if not isinstance(s, dict):
        return s
    out = {}
    for k, v in s.items():
        if k in ("example", "xml", "readOnly", "x-example", "externalDocs") or k.startswith("x-"):
            continue
        if k == "required" and not isinstance(v, list):
            continue
        if k == "type" and v == "file":
            v = "string"
        if k == "description" and isinstance(v, str):
            v = trunc(v)
        if k == "properties" and isinstance(v, dict):
            v = {pk: clean(pv, depth + 1) for pk, pv in v.items()}
        elif k in ("items", "additionalProperties") and isinstance(v, dict):
            v = clean(v, depth + 1)
        elif k in ("allOf", "anyOf", "oneOf"):
            v = clean(v, depth + 1)
        out[k] = v
    return out


def build_inputs(op):
    props, required = {}, []
    for p in op.get("parameters") or []:
        loc = p.get("in")
        if loc == "body":
            sch = clean(p.get("schema") or {})
            if sch.get("type") == "object" and sch.get("properties"):
                for k, v in sch["properties"].items():
                    key = k if k not in props else k + "_body"
                    v = dict(v)
                    v["x-in"] = "body"
                    props[key] = v
                required += [k for k in sch.get("required", []) if k in props]
            else:
                sch["x-in"] = "body"
                props["body"] = sch
                if p.get("required"):
                    required.append("body")
        else:
            d = {k: p[k] for k in ("type", "format", "enum", "default", "items") if k in p}
            if p.get("type") == "file":
                d["type"] = "string"
            if "type" not in d:
                d["type"] = "string"
            if p.get("description"):
                d["description"] = trunc(p["description"])
            d["x-in"] = loc
            props[p["name"]] = clean(d)
            if p.get("required"):
                required.append(p["name"])
    sch = {"type": "object", "properties": props}
    if required:
        sch["required"] = sorted(set(required))
    return sch


def build_outputs(op):
    for code, r in (op.get("responses") or {}).items():
        if str(code).startswith("2") and isinstance(r, dict) and r.get("schema"):
            return clean(r["schema"])
    return None


def body_missing(delta_line, method):
    parts = [x.strip() for x in delta_line.split("|")]
    body = parts[2] if len(parts) > 2 else ""
    return method in ("POST", "PUT", "PATCH", "DELETE") and "not captured" in body


def inputs_from_live(delta_line):
    """'GET /x/{id} | id*(p),limit(q) | json a*,b' -> input schema with unknown types."""
    parts = [x.strip() for x in delta_line.split("|")]
    params = parts[1] if len(parts) > 1 else ""
    body = parts[2] if len(parts) > 2 else ""
    props, required = {}, []
    loc_name = {"p": "path", "q": "query", "h": "header"}
    for tok in [t for t in params.split(",") if t]:
        m = re.match(r"([^*(]+)(\*?)\((\w)\)", tok.strip())
        if m:
            n, req, loc = m.groups()
            props[n] = {"description": "Type not captured.", "x-in": loc_name.get(loc, loc)}
            if req:
                required.append(n)
    toks = body.split(" ", 1)
    if len(toks) == 2 and toks[1].strip() and not toks[1].startswith("("):
        for t in toks[1].split(","):
            t = t.strip()
            if not t:
                continue
            req = t.endswith("*")
            n = t.rstrip("*")
            if n.endswith(" items"):
                n = n[:-6]
            props[n] = {"description": "Type not captured.", "x-in": "body"}
            if req:
                required.append(n)
    sch = {"type": "object", "properties": props}
    if required:
        sch["required"] = sorted(set(required))
    return sch


def risk_of(method, flags, ident):
    if "read" in flags:
        return "read"
    if "ext" in flags:
        return "external_effect"
    if "destructive" in flags:
        return "destructive"
    if "write" in flags:
        return "write"
    if method == "GET":
        return "read"
    if method == "DELETE":
        return "destructive"
    return "write"


def plan_of(domain, ident, flags):
    if domain in DOMAIN_PLAN:
        return {"free": DOMAIN_PLAN[domain][0], "note": DOMAIN_PLAN[domain][1]}
    if ident.startswith(MASTER_PREFIXES):
        return {"free": "unknown", "note": "Master-account (corporate) feature; availability on a Free account was not checked."}
    return {"free": "unknown", "note": "Plan availability of this API call was not checked."}


def postcondition(method, op, ident):
    """Generic read-back instruction. It is derived from the verb, not from a run: nothing generated here was executed."""
    codes = [str(c) for c in (op.get("responses") or {}).keys()] if op else []
    verb = ident.split(".", 1)[1].split("_", 1)[0]
    if method == "GET":
        return "HTTP 200 with the requested data."
    if verb == "create" or (verb == "add" and "201" in codes):
        return "HTTP 201 (or 200) returning the new id; read the item back with its get_/list_ action to confirm."
    if verb == "delete":
        return "HTTP 204 (or 200); then a get_ of the same id should answer 404 (expected, not tested)."
    if verb == "remove":
        return "HTTP 204 (or 200); list the parent collection and confirm the item is gone."
    if verb in ("update", "configure", "verify"):
        return "HTTP 204 (or 200); read the item back with its get_/list_ action and compare the fields you changed."
    if verb == "send":
        return "HTTP 2xx with a message id or empty body; confirm delivery in the matching logs or statistics action."
    return "HTTP 2xx; read the affected item back to confirm."


def load_overlays(d):
    """overlays/<id>.yaml: UI evidence layered on top of an API-generated action.
    Keys: ui{entry,steps,internal_service}, ui_label_pt, preconditions/side_effects/errors/limits (appended),
    postcondition_check, plan_availability, risk, requires_human_confirmation, summary (replace),
    provenance{verification,verified_via,evidence,sources,notes}."""
    out = {}
    if d.exists():
        for f in sorted(d.glob("*.yaml")):
            o = yaml.safe_load(f.read_text(encoding="utf-8"))
            if o.get("id") != f.stem:
                sys.exit(f"overlay {f.name}: id must equal the file name")
            out[o["id"]] = o
    return out


CONSENT_RULE = ("Inputs {} change e-mail/SMS consent. Set them only on an explicit yes from the person, naming the contact or list; "
                "never set them to false to re-enable someone who unsubscribed or was blocked.")
SUMMARY_OVERRIDES = {
    "account.verify_sender": "Complete a sender's verification with the OTP code received by e-mail.",
    # the spec's own summaries are often four words long ("Update a list."); these say what the call changes
    "account.create_domain": "Add a sending domain to the account; authenticating it is a separate step.",
    "account.create_sender": "Add a sender (name and address); Brevo e-mails a verification message to the address.",
    "account.delete_domain": "Delete a sending domain from the account (destructive; confirm first).",
    "account.delete_sender": "Delete a sender from the account (destructive; confirm first).",
    "account.delete_sub_account": "Delete a sub-account of a corporate (master) account.",
    "account.delete_sub_account_group": "Delete a group of sub-accounts of a corporate (master) account.",
    "account.invite_user": "Invite a person to the account with chosen permissions; an invitation e-mail goes out. Locked on Free.",
    "account.remove_admin_user": "Revoke an admin user's access to the account.",
    "account.remove_user": "Revoke a user's access to the account.",
    "account.update_sender": "Change the name or e-mail address of an existing sender.",
    "account.update_sub_account_plan": "Change the plan (credits and features) of a sub-account of a corporate account.",
    "account.verify_domain": "Authenticate a sending domain by checking its DNS records; the domain must exist already.",
    "contacts.create_attribute": "Create a custom contact attribute (name, category and type such as date or text).",
    "contacts.create_folder": "Create a folder that groups contact lists.",
    "contacts.delete_attribute": "Delete a contact attribute (destructive; confirm first).",
    "contacts.delete_contact": "Delete a contact and its history for good (destructive; confirm first).",
    "contacts.delete_list": "Delete a contact list (destructive; confirm first). Its contacts are expected to stay in the account.",
    "contacts.export_contacts": "Export contacts (all, or a list or segment) to a file you can download.",
    "contacts.get_contact": "Read one contact: attributes, list memberships, subscription status and recent activity.",
    "contacts.import_contacts": "Import contacts from a file or a JSON body into chosen lists; runs asynchronously.",
    "contacts.list_attributes": "List the contact attributes of the account with their categories and types.",
    "contacts.list_contacts": "List contacts, with filters for list, segment and modification date, and paging.",
    "contacts.list_folders": "List the folders that group contact lists (system folders included).",
    "contacts.list_lists": "List contact lists with their folder, counts and paging.",
    "contacts.list_segments": "List the saved segments. The API reads segments but cannot create them.",
    "contacts.update_attribute": "Change the values or the calculation of an existing contact attribute.",
    "contacts.update_contact": "Change a contact's attributes, list memberships or subscription status (blocklist flags change consent).",
    "contacts.update_folder": "Rename a folder of contact lists.",
    "contacts.update_list": "Rename a contact list or move it to another folder.",
    "crm.create_company": "Create a company in the CRM, optionally linked to contacts and deals.",
    "crm.create_deal": "Create a deal in the CRM pipeline; the CRM must be activated on the account first.",
    "crm.create_file": "Upload a file to attach to a CRM contact, company or deal.",
    "crm.create_note": "Create a note linked to CRM contacts, companies or deals.",
    "crm.create_task": "Create a CRM task (type, due date, assignee) linked to contacts, companies or deals.",
    "crm.delete_company": "Delete a CRM company (destructive; confirm first).",
    "crm.delete_deal": "Delete a CRM deal (destructive; confirm first).",
    "crm.delete_file": "Delete a CRM file (destructive; confirm first).",
    "crm.delete_note": "Delete a CRM note (destructive; confirm first).",
    "crm.delete_task": "Delete a CRM task (destructive; confirm first).",
    "crm.update_company": "Change the attributes of a CRM company.",
    "crm.update_deal": "Change the attributes or pipeline stage of a CRM deal.",
    "crm.update_note": "Change the text or links of a CRM note.",
    "crm.update_task": "Change the fields or the done state of a CRM task.",
    "ecommerce.create_category": "Create or update a product category in the e-commerce catalogue.",
    "ecommerce.create_orders": "Create orders in batch from your shop's data (order events can trigger automations).",
    "ecommerce.create_payment_request": "Create a payment request for a contact; the contact can be notified by e-mail.",
    "ecommerce.create_product": "Create or update one product in the e-commerce catalogue.",
    "ecommerce.create_products": "Create or update products in the e-commerce catalogue in batch.",
    "ecommerce.delete_payment_request": "Delete a payment request (destructive; confirm first).",
    "email_campaigns.delete_campaign": "Delete an e-mail campaign (destructive; confirm first).",
    "email_campaigns.update_campaign": "Edit an e-mail campaign; with a schedule field and recipients set it schedules a real send.",
    "integrations.create_event": "Record a custom event for a contact (track API); events can trigger automations.",
    "integrations.create_external_feed": "Create an external feed (a URL whose content can be inserted into campaigns).",
    "integrations.delete_external_feed": "Delete an external feed (destructive; confirm first).",
    "integrations.delete_webhook": "Delete an outbound webhook (destructive; confirm first).",
    "integrations.update_external_feed": "Change an external feed's URL, authentication or headers.",
    "integrations.update_webhook": "Change a webhook's URL or events; a new URL starts receiving contact data.",
    "sms_whatsapp.delete_sms_campaign": "Delete an SMS campaign (destructive; confirm first).",
    "sms_whatsapp.send_test_sms": "Send a test SMS of a campaign to the numbers you give (uses SMS credits).",
    "sms_whatsapp.send_whatsapp_message": "Send a WhatsApp message to a contact's number.",
    "sms_whatsapp.update_sms_campaign": "Edit an SMS campaign; with a schedule field set it schedules a real send.",
    "transactional.delete_hardbounces": "Delete hard-bounce records so those addresses can be e-mailed again (confirm first).",
    "transactional.update_template": "Change a transactional e-mail template (name, subject, sender, body or active state).",
}
# operations whose effect cannot be cleanly undone although they are plain writes
REVERSIBLE_FALSE = {"contacts.import_contacts", "crm.import_companies", "crm.import_deals", "loyalty.redeem_reward"}


def apply_overlay(d, ov):
    for k in ("preconditions", "side_effects", "errors", "limits", "depends_on", "related"):
        if ov.get(k):
            d[k] = list(d.get(k, [])) + list(ov[k])
    for k in ("postcondition_check", "plan_availability", "risk", "requires_human_confirmation", "summary", "ui_label_pt"):
        if k in ov:
            d[k] = ov[k]
    if "risk" in ov and "reversible" not in ov:
        d["reversible"] = ov["risk"] in ("read", "write")
    if "reversible" in ov:
        d["reversible"] = ov["reversible"]
    if ov.get("ui"):
        d["execution"]["ui"] = ov["ui"]
    if ov.get("preferred"):
        d["execution"]["preferred"] = ov["preferred"]
    pv = ov.get("provenance")
    if pv:
        cur = d["provenance"]
        for src in pv.get("sources", []):
            if src not in cur["sources"]:
                cur["sources"].append(src)
        for k in ("verification", "verified_via", "evidence", "verified_at"):
            if k in pv:
                cur[k] = pv[k]
        if pv.get("notes"):
            cur["notes"] = (pv["notes"] + " " + cur.get("notes", "")).strip()


def main(root):
    root = Path(root)
    inv = json.loads((root / "inventory/api_endpoints.json").read_text(encoding="utf-8"))
    delta = json.loads((root / "inventory/api_live_delta.json").read_text(encoding="utf-8"))
    rows = parse_map(root / "scripts/api_action_map.txt")

    # index delta lines for live-only ops
    live_lines = {}
    for ln in delta["added_in_live"]["non_loyalty_with_params"]:
        mp = ln.split("|")[0].strip()
        m, p = mp.split(" ", 1)
        live_lines[norm(m, p)] = ln
    for ln in delta["added_in_live"]["loyalty_method_path_only"]:
        m, p = ln.split(" ", 1)
        live_lines[norm(m, p)] = ln + " | " + ",".join(f"{x}*(p)" for x in re.findall(r"\{([^}]+)\}", p)) + " | json (body not captured)"

    snap = {}
    for r in inv:
        snap.setdefault(norm(r["method"], r["path"]), []).append(r)

    by_key = {}
    for row in rows:
        by_key.setdefault(norm(row["method"], row["path"]), []).append(row)

    errors = []
    # coverage checks
    for k, ops in snap.items():
        if k not in by_key:
            errors.append(f"snapshot operation without a map row: {k}")
    for k in live_lines:
        if k not in by_key:
            errors.append(f"live-only operation without a map row: {k}")
    for k, rs in by_key.items():
        if k not in snap and k not in live_lines:
            errors.append(f"map row for an operation that is in neither spec: {k}")
        for r in rs:
            if "live" in r["flags"] and k not in live_lines:
                errors.append(f"row flagged live but not in the live delta: {k}")
    ids = [r["id"] for r in rows if r["id"] != "-" and "handwritten" not in r["flags"]]
    dups = {i for i in ids if ids.count(i) > 1}
    errors += [f"duplicate id in map: {d}" for d in sorted(dups)]
    if errors:
        print("FAILED:")
        for e in errors:
            print(" -", e)
        sys.exit(1)

    # hand-written coverage (api method+path) and ids
    hand_api, hand_ids = set(), set()
    for f in (root / "actions").rglob("*.yaml"):
        if "_generated" in f.parts:
            continue
        a = yaml.safe_load(f.read_text(encoding="utf-8"))
        hand_ids.add(a["id"])
        api = a.get("execution", {}).get("api")
        if api:
            hand_api.add(norm(api["method"], api["path"]))
    for r in rows:
        if "handwritten" in r["flags"] and r["id"] not in hand_ids:
            print(f"WARNING: map says {r['id']} is hand-written but no such action file exists yet")

    # merged inventory
    merged = []
    for k, ops in snap.items():
        row = by_key[k][0]
        for o in ops:
            merged.append({"method": o["method"], "path": o["path"], "operation_id": o["operation_id"], "tag": o["tag"],
                           "in_live": "removed" not in row["flags"], "source": "snapshot"})
    for k, ln in live_lines.items():
        m, p = k[0], None
        mp = ln.split("|")[0].strip()
        m, p = mp.split(" ", 1)
        merged.append({"method": m, "path": p, "operation_id": None, "tag": "live", "in_live": True, "source": "live"})
    (root / "inventory/api_endpoints_live.json").write_text(json.dumps(merged, indent=1), encoding="utf-8")

    overlays = load_overlays(root / "overlays")
    out_root = root / "actions/_generated"
    if out_root.exists():
        shutil.rmtree(out_root)
    count = 0
    for row in rows:
        k = norm(row["method"], row["path"])
        f = row["flags"]
        if row["id"] == "-" or "handwritten" in f or "removed" in f or "dup" in f:
            continue
        if k in hand_api:
            continue
        ident = row["id"]
        domain = ident.split(".")[0]
        is_live = "live" in f
        op = None
        if not is_live:
            op = snap[k][0]
        inputs = inputs_from_live(live_lines[k]) if is_live else build_inputs(op)
        risk = risk_of(row["method"], f, ident)
        needs_conf = "conf" in f or risk in ("destructive", "external_effect")
        base_summary = (op.get("summary") if op else None) or ident.split(".", 1)[1].replace("_", " ").capitalize()
        summary = base_summary.rstrip(".") + "."
        # Brevo reuses the same summary text for two different operations; keep the catalog unambiguous
        summary = SUMMARY_OVERRIDES.get(ident, summary)
        if is_live:
            summary = ident.split(".", 1)[1].replace("_", " ").capitalize() + " (" + row["method"] + " " + row["path"] + ")."
        pre = ["An API key (header api-key) that can access this account."]
        if is_live and body_missing(live_lines[k], row["method"]):
            pre.append("The request body schema was not captured here. Read it from the live spec (developers.brevo.com/openapi/<area>.json) before calling.")
            inputs["x-body-not-captured"] = True
        verb = ident.split(".", 1)[1].split("_")[0]
        pparams = {x["name"]: x for x in ((op or {}).get("parameters") or []) if x.get("in") == "path"}
        for pn in re.findall(r"\{([^}]+)\}", row["path"]):
            spec = pparams.get(pn, {})
            if spec.get("enum"):
                # an enumerated path value is a choice, not a record id
                pre.append(f"Path value '{pn}' must be one of: {', '.join(map(str, spec['enum']))}.")
            elif verb == "create" and pn.lower().endswith("name"):
                # the last path segment of a create call is the name the new record gets
                pre.append(f"Path value '{pn}' is the name of the new record; it must not exist yet.")
            elif verb == "create" and pn == "type":
                pre.append(f"Path value '{pn}' selects the kind of record to create; allowed values were not captured, read the live spec.")
            else:
                pre.append(f"Path value '{pn}' must identify an existing record.")
        consent = [k for k in inputs.get("properties", {}) if re.search(r"(?i)blacklist|blocklist", k)]
        if consent:
            pre.append(CONSENT_RULE.format(", ".join(consent)))

        errs = []
        if op:
            for code, r in (op.get("responses") or {}).items():
                if str(code).startswith("2"):
                    continue
                desc = (r.get("description") if isinstance(r, dict) else "") or ""
                errs.append({"condition": f"HTTP {code}: {desc}".strip(": "), "recovery": GENERIC_RECOVERY.get(str(code), "Inspect the response body and correct the request.")})
        if not errs:
            errs = [{"condition": "Request rejected (any 4xx)", "recovery": "Read the response body code and message, fix the request and retry."}]
        # every side effect written here comes from the API documentation or from general knowledge of the call, not from a run
        se = [EXPECTED + s for s in SIDE_EFFECTS.get(ident, [])]
        if risk == "external_effect":
            se.append(EXPECTED + "reaches real recipients or third parties and cannot be recalled.")
        if risk == "destructive":
            se.append(EXPECTED + "removes data; the public API documents no undo.")
        if not se:
            se = [EXPECTED + "changes account data."] if risk == "write" else [EXPECTED + "none; read only."]
        d = {
            "id": ident,
            "domain": domain,
            "summary": summary,
            "risk": risk,
            "reversible": risk in ("read", "write"),
            "requires_human_confirmation": needs_conf,
            "plan_availability": plan_of(domain, ident, f),
            "preconditions": pre,
            "inputs": inputs,
        }
        outs = build_outputs(op) if op else None
        if outs:
            d["outputs"] = outs
        d.update({
            "side_effects": se,
            "postcondition_check": postcondition(row["method"], op, ident),
            "errors": errs,
            "limits": [],
            "depends_on": [],
            "execution": {"preferred": "api", "api": {"method": row["method"], "path": row["path"],
                                                      "auth": "api-key header (never store the value)."}},
            "provenance": {"sources": ["api_docs"], "verification": "documented_only", "verified_at": TODAY,
                           "notes": (LIVE_NOTE if is_live else SDK_NOTE) + (" Marked deprecated in the spec." if "deprecated" in f else "")},
        })
        if row["note"]:
            # reviewer's note on the operation (from the docs or from reading the spec); not a precondition
            d["description"] = "Author's note (from the docs or from reading the spec; not verified): " + row["note"]
        if op and op.get("operation_id"):
            d["execution"]["api"]["operation_id"] = op["operation_id"]
        ov = overlays.pop(ident, None)
        if ov:
            apply_overlay(d, ov)
        if ident in REVERSIBLE_FALSE:
            d["reversible"] = False
        name = ident.split(".", 1)[1]
        outdir = out_root / domain
        outdir.mkdir(parents=True, exist_ok=True)
        (outdir / f"{name}.yaml").write_text(yaml.safe_dump(d, sort_keys=False, allow_unicode=True, width=110), encoding="utf-8")
        count += 1
    if overlays:
        print("FAILED: overlays with no matching generated action: " + ", ".join(sorted(overlays)))
        sys.exit(1)
    print(f"generated {count} actions; merged inventory has {len(merged)} operations "
          f"({sum(1 for m in merged if m['in_live'])} in the live spec)")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
