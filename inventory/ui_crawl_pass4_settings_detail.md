# UI crawl, pass 4: settings pages in detail

Observed 2026-10-22 in the test Free account (pt-BR). Read only: nothing was saved on these pages. The settings app has its own left menu
(`Settings`) with the groups below; most pages are plain forms or lists of cards that open sub-pages.

## Personal
| Page | Path | What it holds |
|---|---|---|
| Perfil | /profile/information | Tabs Informações and Senha. Sections: Informações pessoais, Informações da Empresa, Preferências de comunicação (marketing tips opt-in). |
| Geral | /settings/advanced | Fuso horário, formato de hora (24h/12h), formato de data (DD-MM-AAAA / MM-DD-AAAA); Notificações (mute Brevo activity notice, e-mail when SMS credits drop below a threshold); 'Suas faturas' (invoices by e-mail on renewal); 'Acesso a sua conta' (allow Brevo support access, on by default); button Salvar; **'Fechar sua conta' > 'Encerrar a conta definitivamente'** (destroys all data, never to be run by an agent). |
| Idioma | /settings/localization | 7 UI languages (English US/UK, Français, Italiano, Español, Português Brasil, Deutsch), time zone, 'Salvar as preferências'. |
| E-mail individual | conversations-app.brevo.com/individual-email/settings | 'Conectar e-mail individual' (one's own mailbox for logging, sending and receiving from Contatos, Oportunidades, Empresas), 'Endereços de e-mail e domínios excluídos' list. Needs a mailbox connection (OAuth). |

## Organization
| Page | Path | What it holds |
|---|---|---|
| Usuários | /settings/users (see pass 2) | Invite users (blocked on Free). |
| Remetentes, domínio, IPs | /senders/list (see pass 3) | Senders, domains, dedicated IPs, sending cadence. |
| SMTP & API | /settings/keys/smtp, /settings/keys/api (see pass 2) | SMTP credentials, API and MCP keys (tab 'Chaves API e MCP'). |
| Centro de controle da Aura IA | /aura-settings | Toggles for Aura agents. 'Agente de marketing' is on in this account (subject lines, messages, e-mail design); 'Agente de vendas' needs a package ('Get package'). |
| Segurança | /security/two-factor-authentication | Tabs 'Autenticação em dois fatores' (enable with an authenticator app or SMS verification) and 'IPs autorizados'. |
| Localização | crown | Plan-gated. |
| Centro de entregabilidade | /compliance | 'Centro de capacidade de entrega': 'Status de envio de e-mails' (here: Envio restrito, with a contact-support link and an explanation), 'Pontuação de capacidade de entrega' (none yet). This is the page behind the red 'account suspended for marketing e-mails' banner. |
| Parâmetros de UTM | /global/utms | Toggle 'Ativar rastreamento UTM': Brevo then adds UTM parameters to campaigns, templates and scenarios; can be overridden per campaign, template or scenario. |

## Data management
| Page | Path | What it holds |
|---|---|---|
| Objetos personalizados | /objects (upgrade) | Plan-gated. |
| Feeds de dados | crown | Plan-gated. |

## CRM > Contatos (`/contact/settings`)
Cards: Atributos de contato; Atributos de empresas; Pontuações (crown); Webhooks; Contatos não engajados (identify unengaged contacts to exclude from campaigns); Aberturas da Apple MPP em segmentos (include or exclude Mail Privacy Protection opens in segments); Consentimento de rastreamento por pixel por contato (track opens and clicks only for contacts who consented); Grupos de consentimento (GDPR consent groups).

## Marketing > Campanhas (`/campaign-settings`)
Cards, each with a button: Configurações padrão (default account preferences and contact info shown in campaigns); Lista de teste (contacts that receive a test version before the full send); Páginas de cancelamento de inscrição (customise the unsubscribe page); Google Analytics (track web traffic from campaigns); Valores globais calculados (daily metrics on the dashboard); Webhooks; Seus remetentes e domínios (SPF, DKIM); Obter um IP dedicado (buy); WhatsApp (manage WhatsApp Business accounts, buy); Conversões (Professional plan, new); Push (subscription prompts and pressure settings); ID do remetente SMS (request a sender ID).

## Conversas, Automações, Comércio
| Page | Path | What it holds |
|---|---|---|
| Caixa de entrada | conversations-app.brevo.com/settings | Read afterwards. Canais: Widget do chat, E-mail, Facebook/Instagram/WhatsApp/SMS (crown). Geral: Preferências, Respostas salvas (crown), Integrações. Chatbot e automação: Chatbot de IA, Ações e chats direcionados, Formulário de contato, Cenários do chatbot. Equipe: Operadores, Grupos, Regras de atribuição. Pessoal: Perfil de conversa, Disponibilidade, Notificações. Nothing was changed. |
| Reuniões | /meetings/settings | redirects to onboarding in this account (no content) |
| E-mails transacionais | /transactional/email/settings | Cards: Configuração (SMTP), Webhook, Contatos bloqueados ou cancelados, Domínios bloqueados, Tags, Regras de retenção (how long logs and previews are kept, separately), Rastreamento (opens, clicks, bounces). |
| SMS transacionais | /transactional/sms/settings | Cards: Configuração (SMS API), Contatos bloqueados ou cancelados, Regras de retenção. |
| E-commerce | /ecommerce/settings | empty here (no store connected) |
| Conversões | crown | Plan-gated. |

## Notes for agents
- The gear icon in the top bar opens the settings app on the CRM > Contatos page by default. Use the left menu, not the URL of a page you have not seen.
- Several pages live on other hosts (conversations-app.brevo.com, my.brevo.com for the list settings). A browser session may need permission for each host.
