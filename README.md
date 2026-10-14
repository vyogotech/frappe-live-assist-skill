# Frappe Live Assist Skills

Standard assistant skills for embedded Frappe and ERPNext AI assistants.

Status: Active. Bundled with `frappe-ai-agent` and extensible via per-site `AI Skill` doctypes in `frappe_ai`.

## Why Assistant Skills

Large system prompts degrade small model reasoning. An assistant skill is a concise Markdown
document loaded **on demand**:
* The system prompt holds a one-line catalog entry.
* A read-only `load_skill` tool returns the skill instructions only when the task requires them.
* Format: Open `SKILL.md` standard with YAML frontmatter (`name`, `description`, `risk`) and Markdown body.

## Shipped Skills

| Skill | Description | Risk |
| --- | --- | --- |
| `system-health` | Inspect System Health Report, scheduler, queues, failed jobs, and errors | read-only |
| `user-create` | Create a user with a welcome email; never handle passwords directly | always-ask |
| `user-password-reset` | Guide password reset flow; explain assistant limitations | read-only |
| `user-access` | Manage user status, roles, and permissions; never remove last System Manager | always-ask |
| `print-format` | Jinja print formats from real DocType fields with child table loops | writes |
| `letter-head` | Letter heads with HTML content; enforce single default | writes |
| `custom-field` | Custom fields and property setters; duplicate and position checks | writes |
| `client-script` | Form scripts with plain-words explanation and full code display | always-ask |
| `web-research-records` | Web search and page fetch to create and deduplicate records | writes |

## Design Rules

1. **Explicit tools**: State only tools actually used.
2. **Schema discovery**: Learn fields from DocType definitions (`get_document` on DocType); never guess field names.
3. **Child tables**: Structured as lists of row objects.
4. **Duplicate prevention**: Check for existing records prior to creation.
5. **Verified data**: Addresses, emails, and phone numbers must come directly from read pages or existing records.
6. **No passwords in chat**: Never request, store, or output user passwords.
7. **Capability honesty**: Explicitly declare what the assistant cannot do.
8. **Invented domains**: Examples use RFC 2606 reserved domains (`.test`, `example.org`).
9. **Size constraint**: Under 8 KB per skill.

## Repository Structure

```text
skills/<name>/SKILL.md        One folder per skill, folder name = skill name
scenarios/<name>.yaml         Scripted conversation per skill, invented data only
scripts/validate.py           Format, size, link, and no-real-data checks
scripts/check_fields.py       Verify skill fields against Frappe DocType schemas
scripts/run_scenarios.py      Scenario runner and validator
NOTICE.md                     Provenance and licensing notice
README.md                     This document
CONTRIBUTING.md               Contribution guidelines
LICENSE                       MIT License
.github/workflows/ci.yml      CI workflow
```

## Running Tests

Validate skill formatting, size, and data safety:
```bash
python scripts/validate.py
```

Verify fields against DocType definitions:
```bash
python scripts/check_fields.py --schema-dir ../frappe
```

Validate scenarios:
```bash
python scripts/run_scenarios.py
```
