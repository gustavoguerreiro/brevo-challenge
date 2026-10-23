# UI crawl, pass 3: contacts, companies, templates, campaigns, senders

Observed 2026-10-22, test account (Free plan, pt-BR). Nothing was sent, activated, imported or deleted.

## Contacts (`/contact/list`)
- Header "Contatos <n>", buttons "Adicionar contatos" (create) and "Importar contatos". View tabs: "Todos os contatos" and "+" (save a new view); gear = view settings.
- Controls: "Carregar uma lista ou um segmento" (load a list or segment as the view), "Adicionar filtro", "Personalizar colunas", search box. Default columns: CONTATO, INSCRITO, COLOCADO EM LISTA BLOQUEADA, E-MAIL, WHATSAPP, LANDLINE_NUMBER, ÚLTIMA ALTERAÇÃO, DATA DE CRIAÇÃO.
- Row selection shows a bulk bar: "Adicionar a uma(s) lista(s)", "Lista bloqueada" (blocklist), and a menu "Mais ações": Modificar, Atribuir (assign owner), Copie o número de SMS para o WhatsApp, Adicionar à automação, Exportar, Excluir definitivamente. None was run.
- IDs: the account owner's contact is the first record; the test contact opened at `/contact/index/2`.

## Single contact (`/contact/index/<id>`)
- Tabs: Visão geral, Histórico, Listas, Preferences. Prev/next arrows ("1 de 2").
- Action bar: Anotação (note), E-mail, Ligar, SMS, Tarefa, Mais. "Mais": Reunião, Oportunidade, Arquivo, Adicionar à automação, Excluir definitivamente.
- Overview cards: Preferences (shows Subscribed, Campanhas, E-mails transacionais, pencil to edit), Informações (attribute fields, gear to choose fields), Pontuações (locked, upsell), Campanhas (sent, delivered, unique opens, unique clicks), Histórico recente, Empresas ("Adicionar empresas"), Oportunidades ("Adicionar oportunidades"), custom object card (upsell).
- Tab Preferences: "Campanhas e automações" > Campanhas (dropdown, now Inscrito); "Transacional" > E-mails transacionais (dropdown, now Inscrito) and "Remetentes" with a pencil to restrict which senders may e-mail this contact. Subscription state is changed here with the dropdowns.

## Contact import wizard (`/contact/import/options`)
- Reached with "Importar contatos". First a dialog "Importar seus dados para a Brevo" asks the data type: Contatos, Empresas, Oportunidades, Notas. A side tip says the order is contacts first, then companies/deals/tasks, then notes.
- Next page "Importar contatos para criação ou atualização em massa": three methods: "Importar de um arquivo" (csv, xlsx or txt), "Copiar e colar", "Importar de outra ferramenta".
- File page `/contact/import/upload`: step 1 "Carregue seu arquivo" (drag and drop zone, link "Baixe um arquivo de exemplo (.csv)"). Later steps (column mapping, list choice) were not reached because no file was uploaded.

## Companies (`/companies`)
- Header "Empresas", buttons "Importar empresas" and "Criar empresa". Same table controls (filter, columns, search by name or domain). Empty account shows "Você ainda não tem nenhuma empresa" with "Crie sua primeira empresa". The create form was not opened.

## Templates (`/templates/listing`)
- Header "Modelos"; buttons "Criar pasta" (crown) and "Criar modelo". Tab "E-mail". List filters: search, status.
- "Criar modelo" asks "Qual modelo você deseja criar?": Modelo de e-mail, Modelo do WhatsApp, Modelo push (crown).
- E-mail editor `/templates/email/create` (becomes `/templates/email/edit/<id>` as soon as the name is confirmed): name with pencil (default "Novo modelo"), status Inativa, buttons "Pré-visualizar e testar" and "Salvar" (menu: Salvar, Salvar e ativar). Fields: Conteúdo ("Adicionar conteúdo"), E-mail do remetente*, Nome do remetente*, Linha de assunto* (emoji and variable buttons), Pré-visualização do texto (keep under 35 characters), "Mostrar configurações avançadas". Warning when the sender domain is not authenticated: Brevo substitutes @brevosend.com.
- Executed: template ZZ_TEST_template_1 saved inactive (toast "Modelo salvo com sucesso!", ID #2, listed as Inativo). Row actions: Pré-visualização, Duplicar, Ativar, Excluir.

## Campaigns list (`/campaigns/listing`)
- Header "Campanhas"; buttons "Criar pasta" (crown), "Gerar campanha com IA", "Criar campanha". Filters: search, status, tags (crown), folder (crown). Row columns: Destinatários, Aberturas, Cliques, Inscrição cancelada, Conversões.
- Row menu: Editar, Pré-visualizar e testar, Duplicar, Adicionar à pasta (crown), Atribuir etiqueta (crown), Compartilhar modelo, Excluir. "Duplicar" opens a dialog "Duplicar campanha?" with check boxes (all on): Remetente, Destinatários, Assunto, Design, Configurações adicionais. It was cancelled.
- "Criar campanha" opens "Criar uma campanha": section Padrão with cards E-mail, SMS, WhatsApp (crown), Push (crown), Pop-up (crown); section Automatizada with "Criar do zero" (goes to the automation editor) and pre-built automations filtered by "Tipo de automação pré-construído" (Mais populares, Todos, Aumentar o engajamento, Aumentar tráfego, Aumentar a receita, Construir relacionamentos) and "Canal" (email shown). E-mail pre-builts under Mais populares: Mensagem de boas-vindas, Carrinho abandonado, Atividade de marketing, Compra de produto, Data de aniversário.
- SMS setup `/sms-campaign/campaign-setup`: Nome da campanha (0/128), Tags (crown), Pasta (crown), buttons Cancelar and "Criar uma campanha". Not created (the account has 0 SMS credits and creating SMS drafts was not part of the test-data permission).

## Senders, domains (`/senders/list`, `/senders/domain/list`)
- "Adicionar remetente" opens `/senders/add`: From Name*, From Email* (format name@domain), live phone preview, button disabled until filled. Submitting would send a verification e-mail to that address, so it was not run.
- Tab Domínios: empty state "Configurar seu domínio", button "Adicionar um domínio". Tabs IPs dedicados and Cadência de envio exist.
