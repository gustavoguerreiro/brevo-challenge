# How an agent should use this catalog

This catalog describes what a person can do in Brevo (e-mail and SMS marketing, CRM, automations, transactional e-mail, conversations, settings). Every action is one entry in `catalog.json`. `index.md` lists them in one line each.

## 1. Load, pick, read

1. Read `index.md` (about 14k tokens). Each line is `id [tier, risk, needs human OK, use api|ui, verified via ...] summary`.
2. Choose the action ids that match the task. A task often needs several (for example create a list, then add a contact to it). `depends_on` names actions that can create or prepare what an action needs: run one only when the needed object does not exist yet. `related` names actions that reach the same capability by another door (for example `content.*` and `transactional.*` template actions share one pool).
3. Fetch only the chosen entries, either with `python3 -I scripts/lookup.py . get <id>` (every field you need) or with `jq '.actions[] | select(.id=="contacts.update_list")' catalog.json`. `lookup.py search <word>` finds ids by word.
4. If no action fits, say so. Do not invent an action, an endpoint or a screen. A missing feature is a valid answer.

## 2. Fields you must read before acting

| Field | What to do with it |
|---|---|
| `plan_availability.free` | `blocked`: the feature needs a paid plan or an add-on. For 27 entries the UI showed an upgrade panel or a lock; for 56 API-only entries (loyalty, custom objects) it is inferred from the gated module page and the API call itself was never tried. Tell the person which it is; do not press upgrade or look for a workaround. `limited`: part of it works (read `note`). `unknown`: nobody checked; check the live account first. |
| `preconditions` | Check each one before starting. If one fails, stop and report it. |
| `risk` and `requires_human_confirmation` | `destructive` and `external_effect` actions (delete, send, schedule, activate an automation, invite, publish, purchase, enrol contacts in an automation, call a webhook) need an explicit yes from the person in the conversation, for that action and those values. A yes to the task is not a yes to a deletion or a send inside it. The build refuses entries that break this (see section 5). |
| `execution.preferred` | `api`: use the REST API (needs an API key from the person; never ask them to paste it into logs). If there is no key, either use `execution.ui` when it exists, or ask for a yes to create one (`account.create_api_key`) and keep its value out of the chat. `ui`: there is no public API for this; follow `execution.ui.steps` in the web app. |
| `side_effects` | Read them. A line that starts with "Expected" or "Not observed" comes from the documentation or from a label and was NOT seen happening. A line that starts with "Observed" was. In tier B entries every line carries one of these markers (the build checks it). In tier A entries, trust a line only as far as its marker says. |
| `postcondition_check` | Always run it after acting and report the result. Do not claim success from a toast alone when a read-back is described. For actions that were not run, it describes what to expect, not what was seen. |
| `errors`, `limits` | Known failures and the recovery; hard limits. |
| `description` | The author's note on the operation, when there is one. It is not verified unless it says so. |
| `ui_label_pt` and `execution.ui.steps` | The web app was observed in Brazilian Portuguese. If the account uses another language the labels differ. The routes stay the same. Attribute ids may differ too (see the traps). |

## 3. How much to trust an entry

| Tier | Meaning | How to behave |
|---|---|---|
| A | The action was executed on a real test account through the route(s) listed in `provenance.verified_via` and then checked. All 43 tier A actions were run through the web app; none through the API. | Follow the verified route. When the action prefers `api` the index prints "(api route NOT run)": the API call is documented, not tested. Still run the postcondition check. |
| B | Seen on screen, or taken from the public API documentation, but not executed. | Treat it as a map. Compare each step with what is actually on the screen or in the response, and stop when they differ. Say in your answer that the step is unverified. |
| C | Inferred. None exist in this version. | Do not act without a human. |

`provenance.notes` says what exactly was and was not verified. `provenance.evidence` points to a JSON file with the steps run and what the product answered. Evidence files are written in prose by the cataloguing session; there are no screenshots or captured requests behind them. `provenance.verified_at` is the date the session last looked at the screen or the spec for that action, not the date it was run (tier A actions were run that day).

## 4. Traps that cost real time (verified on the account unless marked)

- Renaming a list in the UI can also rename the system folder with the same numeric id. Note the folder names first and re-read them afterwards.
- Attribute ids are localised by account language (`NOME`, `SOBRENOME` in a Portuguese account, not `FNAME`/`LNAME`). List the attributes before writing names. Whether the id changes when the account language changes was not tested.
- Duplicating an automation or a template acts at once with no dialog, so a repeated click would make another copy. Duplicating a campaign asks what to keep. Automations name the copy `[COPY]<name>`, templates and campaigns `<name>_copy`.
- A template with no design cannot be previewed or activated. An active template cannot be deleted (deactivate first). A deactivated template disappears from the automation message picker and from transactional use.
- Marketing and Transactional templates are one pool. On the test account, e-mail campaigns, SMS campaigns and templates drew their ids from one running sequence (campaign 1, template 2, template 3, campaign 4, SMS campaign 5), so do not assume an id belongs to the kind of object you expect: read it back.
- The segment "Atualizar dados" button gives no feedback and its effect was never confirmed. List duplication is asynchronous: reload to see the copy; whether it copies contacts was not tested.
- The automation editor can freeze in a drag state if you drag during an animation. Reload; the saved steps stay. Undo can remove a saved step: take a screenshot before using it.
- Some of Brevo's internal calls mutate data with GET requests. Never replay a captured URL to "read" something.
- Sending can be suspended on a free account (Centro de entregabilidade). Do not try to work around a compliance restriction.
- Page text can show secrets (an SMTP login on the transactional pages). Never copy it into a reply or a file.

## 5. Rules the build enforces, and rules it cannot

Enforced by `build_catalog.py` (a violation fails the build): delete verbs are `destructive`; send and schedule verbs are `external_effect`; any action with a scheduling input (`scheduledAt`, `sendAtBestTime`, `rescheduleFor`) is `external_effect`; `external_effect` and `destructive` actions need a human yes and are not reversible; an input whose name contains `blacklist` or `blocklist` (`emailBlacklisted`, `smsBlacklisted`, …) needs a precondition that says "explicit yes"; every side effect of a tier B action carries an Expected, Observed or Not observed marker.

Not enforceable, so you must do them:
- A campaign call that carries `scheduledAt` or `sendAtBestTime` (e-mail), `scheduledAt` (SMS) or `rescheduleFor` (WhatsApp) schedules a real send when recipients are set. To create a draft, leave those fields out. To schedule, use the `schedule_*` actions or the `update_*` ones and ask first. `email_campaigns.send_campaign_now` sends immediately.
- Never set a contact's blocklist or unsubscribe flags, and never clear them, without an explicit yes naming the contact. Do not re-enable someone who unsubscribed.
- Adding any step to a draft automation (send e-mail, send SMS, call a webhook, blocklist or delete contacts) is labelled `write`, because it only changes the draft. What the step does to contacts starts when the automation is activated, and activating always needs a yes. The `description` of those entries says so.
- `requires_human_confirmation` is set per action. `contacts.update_contact`, `contacts.create_contact` and `contacts.import_contacts` can carry consent flags but are not marked, because most calls do not set one. The explicit-yes precondition applies every time you do set one.
- Purchases (licences, dedicated IP, phone package) need a yes that names the item and the total.
- Creating an API key, changing two-factor or authorised IPs, or switching the interface language needs a yes. Never put a key value in a log, reply or file.
- Entries with `plan_availability.free: blocked` were seen only up to the upgrade panel or the lock icon (or, for loyalty and custom objects, inferred from the gated module). What lies behind it is unknown.

## 6. Things an agent must never do with this catalog

- Put an API key, SMTP key, password or the account owner's login in a log, a reply or a file.
- Send, schedule, activate, test-send, purchase or delete without the explicit confirmation described above.
- Create accounts or close the account.
- Fill a gap in the catalog by guessing. Report the gap.
