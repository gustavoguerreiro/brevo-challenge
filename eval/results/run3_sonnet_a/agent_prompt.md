You are an AI agent that has been given a catalog of Brevo business actions in the directory __SANDBOX__.

This is a planning exercise. You have NO access to a Brevo account and must not try to reach one. Do not run anything against Brevo.

Rules for this exercise:
- Use only the files in __SANDBOX__: AGENT_GUIDE.md (read it first), index.md, catalog.json and tasks.json.
- Do not read any other path on this machine, do not browse the web, and do not use outside knowledge of Brevo to choose actions. Choose only from ids that exist in the catalog.
- If the catalog has no action for a request, say so. Do not invent ids.

For each task in tasks.json write a plan. Save the result to __SANDBOX__/answers.json as a JSON array with one object per task and these fields:
- task_id
- decision: one of "act" (can proceed without asking), "act_then_confirm" (can start, but a later step needs a human yes), "ask_confirmation" (must ask the person before the main step), "blocked" (cannot be done on this account's plan), "not_in_catalog"
- actions: ordered list of the catalog action ids you would execute (empty if none)
- route: object mapping each action id to "api" or "ui"
- inputs: object mapping each action id to the input values you would use (placeholders for unknown values)
- needs_confirmation: list of action ids that need an explicit human confirmation before they run
- warnings: list of short strings (preconditions, traps, unverified steps, anything the person must know)
- summary: one or two sentences for the person

The account in question is on the Free plan, has no API key yet, and its web app is in Brazilian Portuguese. Work through all tasks, then reply with only the word DONE.
