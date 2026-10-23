# Brevo action catalog

A catalog of the business actions a person can perform in Brevo, written for AI agents to read: 442 actions, each with inputs, risk, plan limits, preconditions, side effects, a post-condition check and a note on how far it was verified. It was built by reverse engineering the product: the web app (crawled and, where safe, executed), the public API specification and the help centre.

- Start here: `WRITEUP.md` (approach, how AI was used, gaps and next steps).
- To use the catalog as an agent: `AGENT_GUIDE.md`, then `index.md`, then look entries up in `catalog.json`.
- Numbers: see `coverage.md`, or run `python3 -I scripts/stats.py .`.

## What is in the box

| Path | What it is |
|---|---|
| `catalog.json` | All actions, compiled. This is the file an agent loads (1.5 MB). |
| `index.md` | One line per action (id, tier, risk, whether a human must confirm, preferred route, summary). Load this first (about 14k tokens). |
| `AGENT_GUIDE.md` | The rules for an agent that uses the catalog: which fields to read, how far to trust each tier, known traps, which safety rules the build enforces and which the agent must keep, what never to do. |
| `coverage.md` | Counts per tier and per domain. |
| `actions/` | The source of truth: one YAML file per action. `_generated/` (280 actions) comes from the API inventory and a curated map, `_generated_ui/` (44) from the automation node reference. The other folders (42 actions, plus 76 in `ui_observed/`) are written from what was seen and done in the web app. |
| `overlays/` | UI evidence layered on top of 38 generated API actions (steps, labels, side effects, verification, `related`). |
| `reference/automation_nodes.json` | The 45 building blocks of the automation editor (22 triggers, 19 actions, 4 rules) with what was seen for each. |
| `schema/action.schema.json` | JSON Schema (draft 2020-12) that every action must satisfy. |
| `evidence/` | One JSON file per verified flow: steps run, what the UI answered, side effects, test data left behind. |
| `inventory/` | Raw discovery output: API inventory (snapshot and live spec), webhook events, UI route maps, crawl notes. |
| `eval/` | The blind test: 31 tasks, the answers written before the run, the scorer, the baselines and the results of every run (`eval/README.md`). |
| `scripts/` | The generators, the validator, the secrets scan, `swagger_to_inventory.py` (API inventory from the Swagger file), `uimk.py` (helper that wrote the hand-authored UI-only entries with consistent defaults; kept for provenance, not needed to rebuild), `lookup.py` (look an action up without loading the whole file) and `package.sh`. |
| `TEST_DATA.md` | Every object created in the test account, so that it can be removed. |

## An action, in short

One action is one thing a person can do ("create a segment", "duplicate an e-mail campaign"). Fields:

- `id`: `<domain>.<verb>_<entity>`, from a closed list of verbs and domains.
- `summary`, `ui_label_pt` (the label in the Portuguese web app).
- `risk`: `read`, `write`, `destructive` or `external_effect`; `requires_human_confirmation`; `reversible`.
- `plan_availability`: what the Free plan allows (`available`, `limited`, `blocked`, `unknown`) with a note.
- `preconditions`, `inputs` (JSON Schema), `outputs`, `side_effects`, `postcondition_check` (required), `errors` (condition and recovery), `limits`.
- `depends_on`: actions that can prepare what this one needs (run one only if the object does not exist). `related`: the same capability through another door (for example the `content.*` and `transactional.*` template actions).
- `execution.preferred` (`api` or `ui`), `execution.api` (method, path, operation id) and `execution.ui` (entry route and numbered steps).
- `provenance`: where it came from, the verification level, which route was verified, the date, the evidence file and notes on what was and was not checked.

Verification tiers: **A** executed on a real test account through the route(s) in `provenance.verified_via`, then read back (43 actions; all 43 were run through the web app, none through the API; 21 of them prefer the API route, which was never called); **B** observed on screen or taken from the API documentation, not executed (399); **C** inferred (none in this version). Plan-locked features have entries too, marked `plan_availability.free: blocked` (83 actions, 52 of them in loyalty): 27 were seen at an upgrade panel or lock icon, 56 (loyalty and custom objects, API-only) are inferred from the gated module page.

## Rebuild

```
python3 -I scripts/gen_api_actions.py .         # API inventory + overlays -> actions/_generated
python3 -I scripts/gen_automation_actions.py .  # reference/automation_nodes.json -> actions/_generated_ui
python3 -I scripts/build_catalog.py .           # validate everything, write catalog.json, index.md, coverage.md
python3 -I eval/score.py . <answers.json>       # score an agent's answers
python3 -I scripts/lookup.py . search segment   # find actions; also `get <id>`, `deps <id>` (what can prepare it) and `related <id>`
python3 -I scripts/scan_secrets.py .            # fail if a credential-shaped string or an entry of SCAN_DENY_FILE is in the repo
sh scripts/package.sh . ../catalog.zip          # scan, rebuild, then zip
```

Run both generators before `build_catalog.py`: each one deletes and recreates its folder. Requires Python 3.10+, `pyyaml` and `jsonschema`. The validator fails the build on: a schema violation, an unknown or removed API endpoint, a missing evidence file or one that is not valid JSON (it does not check what the file says), a tier A action without a verified route, a dangling `depends_on` or `related`, a duplicated id, a non-ASCII UI route, a credential-looking string, or a risk label that breaks the rules in `AGENT_GUIDE.md` section 5 (a delete that is not `destructive`, a send or schedule that is not `external_effect`, an input named blacklist/blocklist without an explicit-yes precondition, or a side effect of a tier B action that does not start with Expected, Observed, Not observed or None).

`inventory/api_endpoints.json` was produced by `scripts/swagger_to_inventory.py` from the Swagger file of Brevo's public Go SDK (github.com/getbrevo/brevo-go, snapshot of February 2025). `inventory/api_endpoints_live.json` marks which of those operations exist in the live OpenAPI files on developers.brevo.com (read on 2026-10-22). The SDK copy itself is not included.

## Safety

No credentials of any kind are in this repository: no API keys, SMTP keys, passwords, session data or the account owner's e-mail address. `scripts/scan_secrets.py` checks for credential shapes and, when `SCAN_DENY_FILE` points at a private list of strings kept outside the repository (the owner's address, the account name), for those too; `package.sh` runs it before zipping. The test account is a free Brevo account; no e-mail or SMS was sent, no automation was activated, no campaign was scheduled and no object was deleted (an undo removed one automation step; it was restored). One test template was activated and deactivated again, a contact was put on the blocklist and restored, an SMS draft and several other drafts were created, and a few test objects were renamed and duplicated. Destructive and external-effect actions are documented but were not run. See `TEST_DATA.md`. The `inventory/` files contain example values (addresses, ids, key-shaped strings) copied from Brevo's public API specification; the key-shaped ones are redacted.
