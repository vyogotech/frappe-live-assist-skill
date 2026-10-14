# Contributing to Frappe Live Assist Skills

Thank you for contributing! Assistant skills guide AI agents in real Frappe Desk environments,
so safety, precision, and adherence to design rules are paramount.

## Writing a New Skill

1. **Folder and File**: Create `skills/<skill-name>/SKILL.md`. Folder name must match the frontmatter `name`.
2. **Frontmatter**:
   ```yaml
   ---
   name: your-skill-name
   description: Max 200 characters explaining when the model should load this skill.
   risk: read-only | writes | always-ask
   ---
   ```
3. **Machine-Readable Field Declarations**:
   Embed a YAML block inside an HTML comment naming all DocTypes and fields referenced:
   ```markdown
   <!-- records:
   DocType Name:
     - fieldname1
     - fieldname2
   -->
   ```
4. **Size Cap**: Keep the total file size under 8,192 bytes (8 KB).
5. **Invented Data**: Use only `.test`, `example.org`, or `example.com` domains. Never include real personal emails, phone numbers, or passwords.
6. **Scenario**: Add a companion scenario at `scenarios/<skill-name>.yaml`.

## Running Validation

Before submitting a pull request, run all checks:

```bash
python scripts/validate.py
python scripts/check_fields.py --schema-dir ../frappe
python scripts/run_scenarios.py
```
