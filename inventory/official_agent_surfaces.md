# Official agent surfaces and how the catalog differs from them

Read 2026-10-22 from Brevo's developer docs and help center (WebFetch, summarised by a small model: treat module lists as accurate, tool-level detail as absent).

## Brevo MCP server
- Main endpoint `https://mcp.brevo.com/v1/brevo/mcp` (all modules). One endpoint per module at `/v1/brevo_<module>/mcp`.
- Auth: an API key created with the MCP option, sent as a bearer token. In the UI: Settings > SMTP & API > tab "Chaves API e MCP" > "Gerar chave API" > tick the MCP-server option. The key is shown once.
- 27 modules: contacts, email_campaign_management, campaign_analytics, templates, transac_templates, deals, companies, tasks, pipelines, notes, sms_campaigns, whatsapp_campaigns, whatsapp_management, lists, segments, attributes, contact_import_export, folders, groups, senders, domains, ips, accounts, users, webhooks_management, external_feeds, processes.
- The docs do not list individual tool names, read/write scope, plan eligibility or rate limits.
- A second MCP server at `https://developers.brevo.com/_mcp/server` only serves the API documentation.

## What it implies for this catalog
- The MCP modules mirror the public REST API areas. None of these appear: automations (workflows), forms, landing pages, pop-ups, conversations inbox settings, meetings, loyalty program setup in the UI, custom objects UI, segment creation (a `segments` module exists, but the public REST API only lists segments, so write support there is unverified).
- Those are the actions an agent can only do through the web UI, and they are where hand-verified UI recipes add the most. They are marked `execution.preferred: ui` in the catalog.
- For everything the REST API covers, the catalog entries point to the API first and keep the UI recipe as a fallback.

## Not verified
- Whether the MCP server exposes a segments-create tool.
- Tool names and parameters (needs a connected client and an MCP key; creating a key was out of scope, see `ui_crawl_pass2_settings.md`).
