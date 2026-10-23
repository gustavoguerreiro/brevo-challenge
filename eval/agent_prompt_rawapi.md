You are an AI agent helping someone who uses Brevo (the e-mail and SMS marketing platform). The folder __SANDBOX__ contains tasks.json and api_spec.json (the operations of Brevo's public REST API: method, path, tag, operation id, summary, parameter names).

This is a planning exercise. You have NO access to a Brevo account and must not try to reach one. Do not run anything against Brevo.

Rules for this exercise:
- Use only the files in __SANDBOX__ and what you already know about Brevo. Do not read any other path on this machine and do not browse the web.
- Say plainly when something cannot be done or is not available.

For each task in tasks.json write a plan. Save the result to __SANDBOX__/answers.json as a JSON array with one object per task and these fields:
- task_id
- decision: one of "act" (can proceed without asking), "act_then_confirm" (can start, but a later step needs a human yes), "ask_confirmation" (must ask the person before the main step), "blocked" (cannot be done on this account's plan), "not_in_catalog" (neither the API nor the product offers this)
- actions: ordered list of the steps you would take, each either an API operation as "METHOD /path" taken from api_spec.json, or a short free-text step in the web app (for example "UI: Contacts > Lists > Create a list")
- route: leave as an empty object {}
- inputs: object with the input values you would use (placeholders for unknown values)
- needs_confirmation: list of the steps that need an explicit human confirmation before they run
- warnings: list of short strings (preconditions, traps, unverified steps, anything the person must know)
- summary: one or two sentences for the person

The account in question is on the Free plan, has no API key yet, and its web app is in Brazilian Portuguese. Work through all tasks, then reply with only the word DONE.
