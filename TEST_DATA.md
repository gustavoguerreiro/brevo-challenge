# Test data left in the Brevo account (to be deleted by the account owner)

Everything below was created or changed in the test Free account on 2026-10-22 for verification.
Nothing was sent to a real recipient and nothing was deleted. No credentials were created or stored.
The create panels for forms, companies and senders, the API key form, the media and conversation pages and the paid-feature panels were opened and left without saving: nothing was created there. The only exception is the SMS draft below.

| Object | ID | Name | Notes |
|---|---|---|---|
| Contact | 2 | zz_test_contact_1@example.com (NOME ZZ_TEST, SOBRENOME ZZ_TEST_LAST) | Member of list 6 |
| List | 3 | **marketing_automation** (created as ZZ_TEST_list_1) | Renamed on purpose, see "Side effect" below. Delete this list, NOT the system folder. |
| List | 6 | ZZ_TEST_list_2_dup | Duplicate of list 3 |
| Segment | 1 | ZZ_TEST_segment_1 | Filter: e-mail contains zz_test |
| Segment | 2 | ZZ_TEST_segment_2_dup | Duplicate of segment 1 |
| E-mail template | 2 | ZZ_TEST_template_1 | Saved inactive, no body |
| E-mail template | 3 | ZZ_TEST_template_1_copy | Made with 'Duplicar'; has a one-line HTML body; activated once and deactivated again, so it is inactive |
| E-mail campaign | 1 | ZZ_TEST_campaign_1 | Draft, subject set, never scheduled |
| E-mail campaign | 4 | ZZ_TEST_campaign_1_copy | Draft made with 'Duplicar' (all parts kept), never scheduled |
| SMS campaign | 5 | ZZ_TEST_sms_1 | Draft created in the UI to read the SMS editor; no content, sender or recipients; never scheduled or sent (the account has no SMS credits). E-mail and SMS campaigns share one id sequence |
| Automation | 1 | ZZ_TEST_automation_1 | Inactive draft. Trigger 'Contato adicionado à lista' on list 3, step #2 'Adicionar a uma lista' (list 6). Never activated or tested |
| Automation | 2 | [COPY]ZZ_TEST_automation_1 | Inactive copy made by the 'Duplicar' menu entry (no dialog was shown, so the click created it at once) |

Do not delete: the system folder `marketing_automation`, the list `identified_contacts` (ID 4), the list 'Sua primeira lista' (ID 2) and the default folder ('Sua primeira pasta' in the interface).

## Side effect to know about
Renaming list ID 3 through the Brevo UI also renamed the system folder `marketing_automation` (numeric ID collision, see
`evidence/contacts.update_list.json`). The folder was restored to its original name `marketing_automation` by renaming the list to that
same name, so list 3 now carries the name `marketing_automation`. It is a test list and can be deleted.

## Changes made and reverted (check these first)
- Contact 2: its campaign subscription was switched to 'Colocado em lista bloqueada' and back to 'Inscrito' (a toast confirmed each change). Re-read later the same day: the contact shows 'Subscribed' for campaigns and transactional e-mail. The contact's history keeps both events (unsubscribed, then subscribed again), so this left a permanent trail.
- List 3: renamed three times (see above). Segment 1: renamed and renamed back. Segment 1 'Atualizar dados' was clicked once with no visible effect.
- Template 3: activated and deactivated once (it is inactive now).
- Automation 1: an undo issued without checking the screen removed a saved step; redo and a reload restored it (`evidence/automations.build_steps.json`). Re-read later the same day (read only): the trigger on list 3 and step #2 (add to list 6) are both on the canvas, and the automation is still inactive.
