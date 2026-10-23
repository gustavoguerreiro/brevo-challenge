# UI crawl, pass 1: screens, visible actions, internal API services

Observed 2026-10-22, the test account, pt-BR UI, free plan (to confirm on "Uso e plano"). Method: navigate to each sidebar path, wait for load, record (a) fetch/XHR hosts and paths from resource timing (query strings and payloads stripped; third-party analytics dropped) and (b) the visible buttons in the main area. Read-only: nothing was created, edited or sent.

Finding: Brevo's web app talks to per-domain internal services, not the public `api.brevo.com/v3`. The service hosts are listed per screen. These are internal and undocumented, so they are evidence of what the UI can do, not a stable contract for agents.

## Contacts, lists, segments

| Screen | Path | Visible actions (PT) | Internal services observed |
|---|---|---|---|
| Contatos | /contact/list | Adicionar contatos, Importar contatos, Carregar uma lista ou um segmento, Adicionar filtro, Personalizar colunas | contacts-api (settings, get-attributes, lists_and_segments), contacts-api-v2 (v3/app/objects/contact/attributes), segments-api (query, count, paginated_count, events, associations), views-manager-service (saved views), contact-service-api (consent-groups) |
| Listas | /contact/list-listing | Criar uma lista, Recalcular agora | contacts-api-v2 (lists/get-folders, lists/get-lists) |
| Segmentos | /contact/segment | Criar um segmento | segments-api (segment/listing, segment/folder/listing) |

## CRM

| Screen | Path | Visible actions (PT) | Internal services observed |
|---|---|---|---|
| Empresas | /companies | Importar empresas, Criar empresa, Adicionar filtro, Modificar filtros, Personalizar colunas | crm-backend-api (companies, attributes, pipeline/details, account-settings) |
| Oportunidades (deals) and Tarefas | /crm/deals and /tasks redirect to /crm/onboarding | Começar grátis (activates the sales CRM) | crm-backend-api (pipeline-template, tasktypes, organization/config) |
| Objetos personalizados | /objects redirects to /objects/upgrade | Atualizar (upgrade) | unified-objects (app/objects/plan) |

Precondition: Deals and Tasks are not usable until the CRM is activated via "Começar grátis". Custom objects are plan-gated.

## Marketing

| Screen | Path | Visible actions (PT) | Internal services observed |
|---|---|---|---|
| Campanhas | /campaigns/listing | (create flow is behind the "Criar campanha" button on Início) | email-campaigns-backend (email-campaign/api/campaigns), folder-engine, tag-engine |
| Formulários | /contact/forms-app/subscription | Criar um formulário de inscrição; types: Inscrição, Cancelamento de assinatura, Atualização de perfil | forms-api |
| Estatísticas | /marketing-reports/statistics | Exportar (arquivo .csv) | marketing-report-statistics (campaigns/statistics, campaigns/calendar) |
| Modelos | /templates/listing | Criar pasta, Criar modelo, E-mail (channel filter) | email-campaigns-backend (email-template/api/templates), editor-api |
| Landing pages | (crown icon in sidebar) | not opened yet | plan-gated |

## Automations

| Screen | Path | Visible actions | Internal services observed |
|---|---|---|---|
| Automações | /automation/automations | none detected in the main area on first load (the list probably renders in a frame or after load; re-check) | workflow-apis (v1/workflow/metaInfo), automation-engine-http-public |

## Transactional

| Screen | Path | Visible actions (PT) | Internal services observed |
|---|---|---|---|
| E-mail, Tempo real | /transactional/email/real-time | Setup wizard: 1 Configuração, 2 Verificação; Configurações de SMTP, Configurações de API, Configurar com Postfix, Configurar com PHP, Próximo | transactional-app-backend (email/realtime/wizard/status, smtp/credentials) |
| E-mail, Estatísticas | /transactional/email/statistics | same wizard until set up | same |
| E-mail, Logs | /transactional/email/logs | Atualizar, Baixar CSV, filter by Destinatário, Mais filtros | transactional-app-backend (email/logs, email/logs/filters) |
| SMS, Tempo real, Estatísticas | /transactional/sms/real-time, /transactional/sms/statistics | Setup wizard: 1 Configuração, 2 Verificação, Próximo | transactional-app-backend-sms |
| SMS, Logs | /transactional/sms/logs | Atualizar, Download, filter by Remetente, Mais filtros | transactional-app-backend-sms (sms/logs, sms/tags) |

## Conversations, commerce, analytics

| Screen | Path | Visible actions (PT) | Notes |
|---|---|---|---|
| Reuniões | /meetings/offer/all redirects to /meetings/onboarding | none detected | meetings-api (plan, users/expert) |
| Telefone | /phone/onboarding | Adicionar pacote | phone-management-api; needs a purchased package |
| E-commerce | /ecommerce | Instalar plug-in | analytics-api (store detection); needs a store connection |
| Fidelização | /loyalty | Atualizar para Enterprise, Saiba mais | loyalty-api; Enterprise only |
| Analytics studio | /analytics | Atualizar, Selecione Professional, Fale conosco | cdp-analytics-api; Professional plan |
| Caixa de entrada | conversations-app.brevo.com | not opened yet | separate host |
| Biblioteca > Multimédia | content-library.brevo.com | not opened yet | separate host |

## Not yet walked

Header menus (Uso e plano, help, settings gear, notifications, account switcher), "Criar campanha" channel options, landing pages, conversions, the inbox and media library sub-apps, and every create/edit dialog (fields, validation, required flags).
