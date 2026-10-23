# UI crawl, pass 5: forms, statistics, media, transactional setup, automation list

Observed 2026-10-22, test account (Free plan, pt-BR). Details and limits are in `evidence/ui.misc_pages_pass5.json`,
`evidence/automations.manage_list.json` and `evidence/content.template_lifecycle.json`.

| Area | Route | What is there |
|---|---|---|
| Forms | /contact/forms-app/subscription, /contact/forms-app/update | Tabs Inscrição, Cancelamento de assinatura, Atualização de perfil. Create flow asks for type (full page/embedded or pop-up, pop-up is crown) and name. Editor not opened. |
| Marketing statistics | /marketing-reports/statistics | Date range, ten summary tiles, tables per channel with CSV export. |
| Templates | /templates/listing | One pool of e-mail templates shared by Marketing, Automações and Transacional. Row menu changes with the state of the template. |
| Template editors | /editor/classic/html/<id> | Three ways to build the body: drag and drop, simple editor, custom HTML (plain text area). |
| Transactional | /transactional/email/real-time | SMTP and API setup wizard, Estatísticas, Logs, Modelos (same list as Marketing), SMS. |
| Media library | /content-hub | Upload, import by URL, folders, AI image generation. |
| Automation list | /automation/automations | Tabs by status, row menu (Duplicar, Renomear, Atribuir uma tag [crown], Ver relatório, Ver detalhes, Registros de acesso, Excluir), activity page, logs, messages page, per-automation settings. |
| Conversions, Analytics studio | /conversions/listing | Upsell pages (crown). |
