---
name: cowork-scenario-plugin-packager
description: |
  Packages a scenario demo (sample files in OneDrive or SharePoint, sample emails, Teams messages and calendar entries, phase prompts, approval gates and an answer key) into an installable Copilot Cowork plugin .zip that checks its required skills, deploys its assets to a SharePoint site or OneDrive the user chooses, runs the guided demo and resets afterwards. Use when the user asks to "package this scenario as a Cowork plugin", "build a demo plugin for UC5", "turn these demo files into a plugin", "create a scenario plugin", "repackage the demo kit", or "validate my scenario plugin".
license: MIT
metadata:
  author: David Eldersveld
  version: "1.2.1"
---

# Cowork scenario plugin packager

Builds one plugin per scenario with generated skills: `<kit>-demo` (readiness check, deploy if needed, phased run with gates), `<kit>-setup` (deploy files and seed mail, Teams and calendar), `<kit>-reset` (remove seeded items) and `<kit>-assets-1..N` (the sample files, base64-encoded in flat `references/asset-NNN.json` text files). Never put binary files or archives inside the plugin: a zip within the plugin zip is rejected, and binary companion files (.docx, .xlsx, .pdf, .png in a skill folder) are dropped when the plugin is installed. Follows the Microsoft Learn package format for Copilot Cowork plugins (manifest v1.28, skills only, no connector).

## Inputs to collect (search first, ask only for what is missing)

| Input | Default |
|---|---|
| Scenario name, kit id (kebab-case, e.g. `caldova-uc5`) and file prefix (e.g. `UC5-`) | Derive from the user's request |
| Sample files | All files in the user's OneDrive or a named SharePoint folder whose names start with the prefix |
| Folder layout (phase folders) | Group files by phase from the scenario document; "00 Start Here" for diagrams or readme |
| Required plugin and skills | The skills the phase prompts use, with phase and purpose for each |
| Phases, prompts, gates, answer key | From the scenario document the user wrote; otherwise draft them and show for approval |
| Seed content | Emails, Teams messages and calendar entries with the prefix in subject; else none |
| Developer URLs and icons | Placeholders (example.com) and generated icons; tell the user to replace before publishing |

## Workflow

1. **Collect the files.** In one script, list the source folder, keep files whose names start with the prefix, and download each into the session workspace (for example `working/<kit>/stage/`). Confirm the count against what the scenario expects. Add any diagram or readme for "00 Start Here".
2. **Clean the files** with `scripts/sanitize_docx.py`:
   - Every Office file: `--core-author "<Kit author>"` removes the builder's name from document properties.
   - Each marked-up draft: `--author "<counterparty lawyer>" --initials XX --date <markup date>T14:30:00Z --keep-comment-prefix "<counterparty name>"`. Tracked changes made in Word Online are credited to the signed-in user; this reattributes them, removes duplicate comments and strips the user's identity.
   - Name clashes between scenarios: `--replace "Old Name=>New Name"`.
   - Check the JSON report (insertions, deletions, authors, comments). Then convert the draft to PDF with LibreOffice to confirm it still opens.
3. **Capture seed content** as `seed-content.json` in the format in `references/seed-content-format.md`. Take it from the script that created the items or rebuild it from the user's "<prefix>" emails, Teams messages and events. Bodies must already show the simulated sender and date, because items are sent from the user to themselves.
4. **Write the scenario references** in `working/<kit>/references/`, using the skeletons in `references/reference-skeletons.md`: `scenario.md`, `phase-prompts.md` (with "[Demo folder]/<subfolder>" paths and a stop at the end of each prompt), `gates.md` and `answer-key.md` (planted issue, where, expected skill).
5. **Write `spec.json`** from `references/spec-template.json`. Rules: kit id kebab-case and at most 52 characters; folder names use only letters, digits, spaces, - _ . !; `files_per_asset_skill` 1-19 (default 18, because each skill allows 20 companion files and 10 MB); at most 20 skills in total (3 + asset skills); `name_short` at most 30 characters; `desc_short` at most 80; `desc_full` at most 4000; give each scenario a distinct `start_phrase` so several demo plugins can be on at once.
6. **Build and validate:** `python scripts/build_scenario_plugin.py working/<kit>/spec.json --out working/<kit>/build`. It generates the demo, setup and reset skills from `templates/`, encodes each sample file as `references/asset-NNN.json` (folder, original name, size, SHA-256, base64 data) and splits them across `<kit>-assets-N` skills (at most 18 files and about 9.5 MB of payload per skill; any single file must be under about 3.5 MB), records everything in the setup skill's `asset-manifest.json`, writes `required-skills.md`, the manifest and icons, zips everything with files at the root and runs `scripts/validate_plugin.py`. The validator rejects nested archives, binary companion files, unsafe file names and companion-limit breaches. Fix every error and rebuild. Warnings need a decision.
7. **Smoke test:** extract the built zip to a fresh folder and run `python <extract>/skills/<kit>-setup/scripts/stage_assets.py <extract>/skills/<kit>-setup <test dir>` (it finds the sibling asset skills). Confirm `missing` and `failed_checksum` are empty, the original file names are restored, every Office file opens and the decoded files are byte-identical to the sources. Also test the inline fallback decode in the setup SKILL.md. Confirm the zip contains only .md, .json, .py and the two icon .png files. Check every required skill name against your own available skills list.
8. **Write the install guide** from `references/install-guide-template.md`.
9. **Publish:** copy `<kit>-legal-demo.zip` (or `<kit>-plugin.zip`) and the guide to the output folder and name both files to the user.

## Report to the user

Give a table: Item | Result (files packaged, seed items, skills generated, validation errors and warnings, smoke test). Then list the remaining actions: placeholder URLs, branded icons, live validation (`wiqd plugin validate --mode deep` or a test-tenant upload), and the facts in `references/platform-notes.md` the user must know (selecting a plugin does not auto-run it; the readiness check compares names; Cowork cannot delete SharePoint files).

## Additional resources

- `scripts/build_scenario_plugin.py` – generates, zips and validates the plugin from `spec.json`
- `scripts/validate_plugin.py` – offline checks for manifest, icons, ASKILL codes and companion-file limits
- `scripts/sanitize_docx.py` – fixes markup attribution, duplicate comments, dates, document properties and name clashes
- `scripts/stage_assets.py` – copied into each setup skill; decodes the asset JSON files into the workspace with original names and verifies size and SHA-256
- `templates/demo-SKILL.md`, `templates/setup-SKILL.md`, `templates/reset-SKILL.md`, `templates/assets-SKILL.md` – the generated skill bodies
- `references/spec-template.json` – annotated spec (based on Caldova UC4)
- `references/reference-skeletons.md` – skeletons for scenario, prompts, gates and answer key
- `references/seed-content-format.md` – seed JSON format
- `references/install-guide-template.md` – install guide text
- `references/platform-notes.md` – Cowork packaging rules and lessons learned
