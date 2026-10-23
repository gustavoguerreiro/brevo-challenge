# UI crawl, pass 2: settings, integrations, webhooks, executed drafts

Observed 2026-10-22 in the test account (Free plan, pt-BR) through Claude in Chrome.
Nothing was sent, activated or deleted. No credential values were read or recorded.

## Settings map (gear icon, 22 entries)

| Group | Entry | Notes |
|---|---|---|
| Personal | Perfil, Geral, Idioma, E-mail individual | not opened |
| Organization | Usuários | opened, see below |
| Organization | Remetentes, domínio, IPs | `/senders/list`, opened |
| Organization | SMTP & API | `/settings/keys/smtp` and `/settings/keys/api`, opened |
| Organization | Centro de controle da Aura IA | not opened |
| Organization | Segurança | not opened (SMTP & API page points to "Segurança, IPs autorizados") |
| Organization | Localização | crown, plan-gated |
| Organization | Centro de entregabilidade | not opened |
| Organization | Parâmetros de UTM | not opened |
| Data management | Objetos personalizados | crown, plan-gated |
| Data management | Feeds de dados | crown, plan-gated |
| CRM | Contatos, Empresas, Oportunidades | not opened (attribute and field settings expected) |
| Marketing | Campanhas | not opened |
| Conversations | Caixa de entrada, Reuniões | not opened |
| Automations | Automações, E-mails transacionais, SMS transacionais | not opened |
| Commerce | E-commerce | not opened |
| Analysis | Conversões | crown, plan-gated |

Account menu (top right, the account name): Meu perfil, Meu plano, Configurações, Integrações, Pegada de carbono, Sair.
"Uso e plano" popover: Plano Free, 300 e-mails restantes até 22/10/2026 (daily allowance), pre-paid e-mail credits 0, pre-paid SMS credits 0.

## Usuários (`/settings/...` users page)
- Tabs: Usuários, Usuário parceiro, Logs de atividades.
- Licence counters: Marketing 1/1, Sales 1/1, each with "Adicionar licenças" (crown). Button "Adicionar usuários" carries a lock icon (blocked on Free).
- Table columns: e-mail, status, marketing role, sales role. Single row: the owner, Ativo, Proprietário / Proprietário.
- Search box by e-mail.

## Remetentes, domínios e IPs dedicados (`/senders/list`)
- Header button "Adicionar remetente". Tabs: Remetentes, Domínios, IPs dedicados, Cadência de envio.
- Row for the default sender shows state Verificado, links Editar / Endereço IP / Assinatura DKIM / DMARC, tags "IP compartilhado", "Padrão", and the warning "O domínio Freemail não é recomendado" (a freemail address as sender).
- Banner: some senders do not meet the new Google, Yahoo and Microsoft sender requirements; check DKIM status.

## SMTP & API
- `/settings/keys/smtp`: banner to block unauthorised IPs for SMTP keys (button "Ativar para chaves SMTP"), "Suas configurações SMTP", "Suas chaves SMTP". Values on this page are secrets and were not read.
- `/settings/keys/api` (tab "Chaves API e MCP"): button "Gerar chave API", the same IP-blocking banner for API keys, table columns Nome, permissão, Status, Expira em, Última utilização em. **The account has no API keys** ("Você não tem nenhuma chave API"). A sample curl for POST /v3/emailCampaigns is shown.
- Consequence: no API call could be executed in this account without creating a key, and the key value would have to be entered into a command. That was not done, so every `execution.api` path in the catalog is documented from the public spec, not executed.

## Integrações (`/app-store`)
- Tabs: Todas as integrações, Minhas integrações, Webhooks.
- 144 integrations (15 pages of 10), filters "Criado por" (Brevo, Parceiros Brevo) and 20 categories: Análise, Atendimento ao cliente, Automação de marketing, Avaliações, Central de ajuda, CMS, Criação de conteúdo e e-mails, CRM, Database, E-mail Marketing, eCommerce, Ferramentas de desenvolvimento, Formulários / Geração de Leads, Gerenciamento de contatos, Gerenciamento de eventos, IA, Outros, Pesquisas, Produtividade, Serviços de Payment.
- First page, built by Brevo: WordPress, WooCommerce, Shopify, BigCommerce, Google Ads, HubSpot, Salesforce, MailChimp, Klaviyo.

## Webhooks (`/app-store/webhooks`)
- Toggle "Webhook de saída" / "Webhook de entrada" (inbound is crown-gated). Button "Adicionar webhook" opens a type picker (outbound or inbound), then a 3-step wizard at `/webhooks/outbound/create`.
- Step 1 "Criar webhook de saída": Nome* (max 64).
- Step 2 "Ponto de extremidade": URL*, "Método de autenticação" (Sem autenticação, Básico, Token), "+ Adicionar objeto" (extra headers, inferred).
- Step 3 "Ações": "Categoria de evento"* (single select) then a list of events, each with an on/off toggle (all on by default). Final button "Ativar webhook". "Cancelar" asks "Descartar alterações?".
- Walked to step 3 and left with "Sair". Nothing was saved: the list is still empty.

### Outbound webhook events by category (labels as shown; 15 categories, 109 events; machine-readable copy in `webhook_events.json`)
- **Transactional email (15):** Soft bounce, Entregues, Enviado, Clicado, Abertura única, Primeira abertura, Reclamação, Diferido, Inscrição cancelada, Bloqueado, Invalid, Carregado por proxy, Aberto, Erro, Hard bounce.
- **Transactional sms (11):** Inscrição cancelada, Responder, Colocado em lista bloqueada, Hard bounce, Inscrito, Enviado, Ignorado, Rejected, Accepted, Entregues, Soft bounce.
- **Marketing email (11):** Entregues, Inscrição cancelada, Atualizado, Excluído, Hard bounce, Soft bounce, Reclamação, Clicado, Aberto, Adicionado a uma lista, Carregado por proxy.
- **Marketing sms (9):** Inscrição cancelada, Responder, Inscrito, Enviado, Ignorado, Accepted, Entregues, Soft bounce, Hard bounce.
- **Conversations (5):** Conversa encerrada, Conversa iniciada, Mensagem recebida, E-mail de vendas clicado, E-mail de vendas aberto.
- **Meetings (3):** Reunião agendada, Reunião cancelada, Reunião iniciada.
- **Phone (1):** Chamada encerrada.
- **WhatsApp (1):** Whatsapp-reply.
- **Cohort (15):** App conectado, Selo ganho, Selo perdido, Desafio concluído, Desafio abandonado, Nova etapa do desafio disponível, Desafio com opt-in, Etapa do desafio concluída, CTA do conteúdo clicado, Conteúdo visualizado, Cohort_perk_received, Vantagem usada, Indicação concluída, Caixa de recompensa recebida, Visita ao centro de missões.
- **Company (1):** Company_merge.
- **Coupon (1):** Unique_coupon_sent.
- **Deals (6):** Deal_association_updated, Deal_attributes_updated, Oportunidade criada, Etapa da oportunidade atualizada, Tarefa concluída, Tarefa criada.
- **Loyalty (24):** balance (expiry reminder, max reached, min reached, unauthorised transaction, expired, updated), subscription (anniversary reminder, created, member added, member removed, anniversary month, revoked, anniversary year), tier (anniversary reminder, anniversary month, membership updated, anniversary year), voucher/coupon (assignment failed, created, expiry reminder, expired, unauthorised redemption, redeemed, revoked).
- **Push (5):** Notificação push clicada, Push_notification_received, Sessão iniciada, Inscrito no notificações push, Cancelamento de inscrições dos notificações push.
- **Website (1):** Página visitada.

Some labels are untranslated internal names (Company_merge, Unique_coupon_sent, Cohort_perk_received, Push_notification_received, Whatsapp-reply, Deal_association_updated). An agent should match on these exact strings.

## Executed in the UI during pass 2 (test data, nothing sent)
- Segment `ZZ_TEST_segment_1` (ID 1): see `evidence/contacts.create_segment.json`.
- Draft e-mail campaign `ZZ_TEST_campaign_1` (ID 1), subject set, not scheduled: see `evidence/email_campaigns.create_campaign.json`.
- Draft automation "Automação #1" (ID 1), trigger "Contato adicionado à lista" set to list ID 3, inactive: see `evidence/automations.create_automation.json`.
