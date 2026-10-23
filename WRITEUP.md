# Brevo action catalog: write-up

## What I built

A catalog of 442 Brevo actions for AI agents: one YAML per action, a JSON Schema, compiled to `catalog.json` (full specs), `index.md` (one line each, about 14k tokens) and `coverage.md`. `AGENT_GUIDE.md` says how to read it, how far to trust each entry and what an agent must never do. Counts come from `python3 -I scripts/stats.py .`.

| | Actions |
|---|---|
| Tier A: executed on a real test account and read back (all 43 through the web app, none through the API) | 43 |
| Tier B: seen on screen or taken from the API documentation, not executed | 399 |
| Web app only (no public API): mostly automations (60), contacts (25), account settings (16), content (14), campaigns (11), conversations (9) | 155 |
| API with a web-app recipe / API only | 45 / 242 |
| Locked on the Free plan (`blocked`): 27 seen at an upgrade panel or lock icon, 56 inferred from a gated module (loyalty 52, custom objects 4; API-only, never called) | 83 |
| Plan availability `unknown` (160 of them API-only) | 214 |
| Needs an explicit human yes | 124 |

Two things to know about tier A. Of the 43, 19 are reads and 24 are writes, and the account held very little data, so many reads returned little: they prove the screen and the route, not the shape of a populated answer. And 21 of the 43 *prefer* the API in the catalog, but the account had no API key, so the API call was never made; the index marks those "(api route NOT run)".

The point is not the number. For each action an agent can tell what was proven and what was not; the dangerous ones carry a stop sign that the build itself enforces; and "needs a paid plan" or "no API for this" are answers the catalog gives instead of leaving the agent to guess.

## Approach

**Three sources, because none is enough.** The public API (233 operations in the SDK snapshot of February 2025, 288 in the live OpenAPI files: 213 of the snapshot's still exist, 75 are new, 20 were dropped or renamed) is the cheapest map but misses what exists only in the web app. Brevo's documentation says its MCP server covers the same API areas; I did not check its tool lists, so "the web-app-only parts are what an agent cannot do today" is an inference, not a finding. The web app was crawled in a logged-in browser (the 38 sidebar entries, most opened and read, landing pages and conversions only up to an upgrade dialog; the settings pages; all 45 building blocks of the automation editor). The help centre and developer site gave plan limits and what changed since the snapshot.

**A pipeline, not a document.** Discover → Extract (scripts turn the spec into an inventory) → Normalize (one schema; ids `<domain>.<verb>_<entity>` from closed lists of 19 domains and 37 verbs) → Verify (run the safe flows, record evidence) → Evaluate (fresh agents that see only the catalog). 280 API-derived and 44 automation-derived actions come from deterministic generators plus a curated map (`scripts/api_action_map.txt`, written with AI help; it holds the judgement calls such as what counts as one action or what is destructive). The same inputs give a byte-identical `catalog.json`. The other 118 actions and 38 overlays are written from what was seen and done in the web app. The `postcondition_check` of most generated entries is a template ("read the object back"), not a check written for that action.

**Reliability is a field, not a promise.** Each action records how it was verified, through which route, on what date, with a link to an evidence file. In tier B every side effect starts with "Expected", "Observed", "Not observed" or "None", so a line from the documentation cannot pass as something seen. The build fails on a schema violation, an endpoint missing from the live spec, a tier A action without a verified route, a dangling reference, a duplicate id, a credential-shaped string, an unmarked tier B side effect, and on **risk labels that break the rules**: a delete that is not `destructive`, a send or schedule that is not `external_effect`, an input that can schedule a send, a destructive or external-effect action without a required human yes, an input named blacklist or blocklist without an explicit-yes precondition. I trust that lint most; it was added after a review of the existing entries found mislabels.

**Safety rules before the first click.** Test data only (`ZZ_TEST_` prefix; the one exception is a test list that now carries the name of a system folder, because renaming it had renamed that folder and renaming it back was the repair; see `TEST_DATA.md`). No sending, no activating an automation, no deleting, no credentials, no account creation. Destructive and external-effect actions are documented and marked, not executed. Everything created is in `TEST_DATA.md`.

## Assumptions (written down instead of asked)

- "Everything a user can do by clicking around" makes the web app the reference. API operations are included because an agent should use them when they exist.
- One action is one operation a person would name ("duplicate an e-mail campaign"); editing a field is an input. In the automation editor each trigger, action and rule is its own action.
- The consumer is an agent that drives a browser or calls the REST API with a key the person provides. No access to Brevo's MCP server is assumed.
- The test account is Free with the Portuguese interface, so labels and attribute ids are Portuguese (`ui_label_pt`); routes do not change.
- Plan limits are part of the truth: a locked feature is catalogued and marked `blocked`.

## What verification found

- Renaming a list in the UI also renamed the system folder with the same numeric id (found by re-reading folders; repaired; recorded).
- Attribute ids are localised (`NOME`, `SOBRENOME`), so an agent copying the API example writes to a field that does not exist.
- Duplicating an automation or a template acts at once with no dialog; duplicating a campaign ticks every box by default, so the copy points at the old audience unless Destinatários is unticked.
- A template with no design cannot be activated; an active one cannot be deleted; a deactivated one disappears from automations.
- Blocklisting a contact and restoring it needs no confirmation and leaves both events in the history. The catalog says re-enabling needs documented consent.
- Brevo's internal services use GET for some mutations, so replaying captured traffic is not a safe way to read.
- Marketing e-mail sending on the test account was suspended by a compliance check; landing pages, pop-ups, push, WhatsApp campaigns, A/B tests, tags and folders, extra users are locked on Free and marked `blocked`; so are loyalty and custom objects, but for those the lock is inferred from the module page (see the table).

## How AI was used

- **Tools.** Claude (configured as Claude Sonnet 5.5) as an agent in Anthropic's agent harness: a browser extension driving a logged-in Chrome (page text, DOM reads, clicks, a page-side hook logging host, method and path of requests), web search and fetch, and a Linux shell with Python. The blind evaluation used fresh Claude subagents started with the aliases `sonnet` and `haiku` (not pinned to a version).
- **Split.** I set the mission and the criteria, approved the structure (taxonomy, schema, tiers) before the build, set the boundary for test data, and own the account. The agent proposed the plan and did the browsing, reading, writing and scripting. A self-review pass, listing what an outside reviewer would attack, produced the risk lint, the "Expected" labels, the consent rule, the secrets scan and the evaluation rework; a second, independent review of the finished build found problems that I then fixed (below).
- **Model vs code.** The model read screens and wrote the hand-written YAML, the evidence files, the curated API map and the scripts. Generators, validator, risk lint, secrets scan and scorer are plain code.
- **Fixed or caught along the way.** A generated precondition said every path parameter must identify an existing record, including the name of an attribute being created; the generator now tells them apart. A blind click on "Duplicar" created an automation copy (recorded as a finding and as test data). An undo issued without looking removed a saved automation step; redo and reload restored it, and every drag is now checked first. A contact was blocklisted and restored (read back as Subscribed; the history keeps both events). An accent-normalisation pass rewrote a URL; the validator now rejects non-ASCII routes. The owner's e-mail address, an SMTP login and the account name that appeared in page text were kept out of every file; `scripts/scan_secrets.py` checks for them and packaging refuses to run on a hit. Claims nobody verified (for example "deleting a segment keeps the contacts") now say "not verified".
- **What the independent review found.** Side effects written as if seen when they came from the docs (now marked and linted), a tier A action that had only been read (demoted to B), risk labels that disagreed with each other, summaries that said too much, missing postconditions on sends and purchases. All fixed in the catalog; that is why the blind test was run again on the final build.
- [Gustavo: add here, in your own words, what you personally checked or corrected by hand, for example which tier A flows you re-ran in your Brevo account. Delete this line if there is nothing to add.]

## Blind test

Fresh agents, each in an empty folder with only `catalog.json`, `index.md`, `AGENT_GUIDE.md` and 31 tasks, wrote a plan per task (no Brevo access). A script scores action choice, safety, trap awareness and route. The key for tasks T01 to T17 was written before the first run; the other tasks and every later edit of the key are listed in `eval/README.md`. The table uses the one metric every run can be scored on (decision and trap awareness):

| Run | Input | Tasks passed | Right decision | Trap mentioned (of 23) |
|---|---|---|---|---|
| Claude `sonnet`, twice | catalog + guide | 31 and 31 of 31 | 31 and 31 | 23 and 23 |
| Claude `haiku` | catalog + guide | 30 of 31 | 31 | 22 |
| Claude `sonnet` | tasks only | 19 of 31 | 24 | 17 |
| Claude `sonnet` | tasks + the API specification (213 operations: method, path, summary, parameter names) | 20 of 31 | 24 | 18 |
| Keyword match (negative control, always "act") | catalog | 5 of 31 | 13 | 0 |

With all four components (only possible with ids) the three catalog runs score 31, 31 and 30 of 31, with no invented id. Haiku's one miss is a regex false negative (it wrote that the step "was never executed"); I did not edit the key.

The gap to the baselines is the signal. Of ten tasks where the right move is to ask first (send, schedule, delete, a webhook, an API key, a test send), the catalog runs asked on all ten. Both Sonnet baselines used another label on four, and on three (no catalog) and two (API specification) the plan listed no confirmation at all. Without the catalog, agents said loyalty or web push does not exist (they are plan-locked) and missed the folder rename, the audience a duplicated campaign keeps, and that the CRM must be activated before deals.

Read the 31 of 31 as a ceiling. I wrote the tasks and the key; I edited the key after run 3 (T15 route, decision and regexes; T18; T24; all old scores are in the repo), and the 31 is not independent of that. The tasks favour the catalog: the traps are ones I hit while building it, and `AGENT_GUIDE.md` contains them, so a catalog agent is partly repeating documentation. Ten trap patterns are loose; I read all their matches in the catalog runs (30 of 30 are real warnings) and found two false positives among the baselines, which makes the baselines' scores slightly generous. The test checks plans, not execution, and not that the catalog is true, which is what the tiers are for.

## Known gaps and limits

- **Most of the catalog is tier B**: 399 of 442. The account had no API key, so no API call was made; even the 21 tier A actions that prefer the API were verified through the web app.
- **Evidence is self-reported prose**: no screenshots, no captured requests. The build checks that evidence files exist and parse, not what they say. For tier B, `verified_at` is when the screen or spec was last looked at, not when it was run. Request bodies of web-app flows were not captured.
- **Automation editor**: of 45 blocks, 2 were built and saved, 15 had their panel read, 28 were seen only in the palette. The effect of a step on contacts starts only when an automation is activated, and none was.
- **Not executed on purpose**: sending, scheduling, test sends, activating or testing automations, deleting, inviting users, creating keys, adding senders or domains, security settings, purchases. A test template was activated and deactivated again.
- **Free plan only**: what is behind the 83 locked entries is unknown; for 56 of them even the lock is inferred. Plan availability is `unknown` for 214 actions, 160 of them API-only.
- **Shallow areas**: the form editor, the campaign and template editors (the campaign recipes stop at creating or duplicating a draft; the test send exists only as an API operation, a gap a blind-test agent also flagged), the inbox, meetings, media upload, the import wizard past step one, conversions, CRM objects beyond their API.
- **The spec moves**: 75 live operations are absent from the SDK snapshot and have less detail; 34 (33 in loyalty) have no captured request body, and the action says so.
- **Snapshot** of a pt-BR Free account on 2026-10-22.

## With more time

1. Create a key, run every read and safe write, move API-only actions from B to A, diff real response shapes against the schema.
2. Record screenshots and request bodies for each web-app flow so evidence can be machine-checked.
3. Build and save each of the 45 automation blocks in a throwaway automation.
4. A paid-plan pass for the 83 locked entries.
5. A regression harness: re-run tier A flows headless on a schedule, re-run the blind test on every catalog change.
6. A harder blind test written by someone who did not build the catalog, with a live sandbox where the agent executes.
7. More depth on forms, the campaign editor, conversations, meetings, media and the import and export wizards.
