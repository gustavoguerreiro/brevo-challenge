# Brevo UI navigation tree (observed)

Observed 2026-10-22 in the logged-in test account, UI language pt-BR, sidebar DOM links (38 counted; the table lists the distinct destinations). Labels are the UI's Portuguese labels; paths are relative to https://app.brevo.com unless a host is given.

Status: `observed` = seen in the DOM/screenshot. `plan-gated` = marked with a crown icon in the sidebar; not yet verified what the free plan allows.

| Module (PT label) | Sub-item (PT label) | Path | Notes |
|---|---|---|---|
| Início | Home | / | Dashboard, onboarding checklist, "Criar campanha" button |
| CRM | Contatos | /contact/list | |
| CRM | Listas | /contact/list-listing | |
| CRM | Segmentos | /contact/segment | |
| CRM | Empresas | /companies | |
| CRM | Oportunidades (deals) | /crm/deals | |
| CRM | Tarefas | /tasks | |
| CRM | Objetos personalizados (custom objects) | /objects | Not present in the Feb 2025 API spec; check API coverage |
| Marketing | Campanhas | /campaigns/listing | |
| Marketing | Landing pages | # (opens elsewhere) | plan-gated (crown) |
| Marketing | Formulários | /contact/forms-app/subscription | |
| Marketing | Estatísticas | /marketing-reports/statistics | |
| Marketing | Modelos | /templates/listing | |
| Automações | Automações | /automation/automations | |
| Transacional | E-mail > Tempo real | /transactional/email/real-time | |
| Transacional | E-mail > Estatísticas | /transactional/email/statistics | |
| Transacional | E-mail > Logs | /transactional/email/logs | |
| Transacional | SMS > Tempo real | /transactional/sms/real-time | |
| Transacional | SMS > Estatísticas | /transactional/sms/statistics | |
| Transacional | SMS > Logs | /transactional/sms/logs | |
| Conversas | Caixa de entrada | https://conversations-app.brevo.com | Separate sub-app/host |
| Conversas | Telefone | /phone/onboarding | Onboarding screen |
| Conversas | Reuniões | /meetings/offer/all | |
| Comércio | E-commerce | /ecommerce | |
| Comércio | Fidelização (loyalty) | /loyalty | Enterprise plan per help docs |
| Biblioteca | Multimédia | https://content-library.brevo.com/content-hub | Separate sub-app/host |
| Análise | Conversões | # | |
| Análise | Analytics studio | /analytics | |

Header (not in sidebar DOM, still to walk): "Uso e plano", help (?), settings gear, notifications bell, account switcher.

Observed preconditions on the home screen:
- Banner: the phone number must be verified before sending the first campaign or messages.
- Onboarding checklist: import contacts, create the first campaign.
