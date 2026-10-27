# Platform notes and lessons learned

## Package format (Microsoft Learn: "Build plugins for Copilot Cowork")
- Zip with files at the root: manifest.json, color.png (192x192), outline.png (32x32), skills/<name>/SKILL.md.
- Manifest v1.28 is strict (no extra root fields). Required: $schema, manifestVersion, version, id (GUID), developer (name, websiteUrl, privacyUrl, termsOfUseUrl), name.short (<=30), name.full, description.short (<=80), description.full (<=4000), icons, accentColor, agentSkills (<=20 entries of {"folder": "./skills/<name>"}).
- SKILL.md: YAML frontmatter with name (kebab-case, 1-64, equal to the folder name) and description (1-1024, with trigger phrases). Keep the body under about 2,000 words; move detail to references/.
- Companion files per skill: at most 20, each at most 5 MB, at most 10 MB in total; relative paths; safe characters only (letters, digits, - _ . space !); no hidden files or reserved names.
- No archives inside the plugin zip (a zip within a zip is rejected).
- No binary companion files: when a plugin is installed, binary files in skill folders (.docx, .xlsx and similar) are not kept, while text files (references/*.md, *.json, scripts/*.py) are. Ship sample files as base64 inside flat references/asset-NNN.json files, split across asset skills (at most 18 files and about 9.5 MB of payload each, under 3.5 MB per source file), and have setup decode them and check SHA-256. Asset JSON file names avoid the safe-character problem; the original names live inside the JSON. Larger kits: host the files on SharePoint and have setup copy them.
- Publish: admin center upload lists the plugin in Discover; `wiqd plugin share` puts it in Shared with me; `atk install --scope Personal` sideloads for testing. Purview Information Barriers tenants block plugin upload.

## Behaviour to explain to users
- Selecting a plugin enables its skills; it does not run anything. The user says the start phrase. Give each scenario its own start phrase.
- The readiness check compares required skill names with the skills the agent can see. There is no API to query installed plugins.
- Cowork cannot delete SharePoint or OneDrive files; reset removes mail, events and chat messages only.
- New uploads take time to be indexed by search; prompts should name folders so files are read directly.

## Lessons from Caldova UC2 and UC4
- Version 1.0 of both plugins shipped the assets as a nested zip (rejected). The next version shipped them as plain .docx/.xlsx files in assets/ folders, which passed validation but arrived empty after install. Version 1.0.3 (UC2) / 1.0.2 (UC4) use base64 JSON, which survives install. Offline validation cannot detect install-time dropping; always test a real install.
- Original file names with parentheses or & (for example "(07-23)" or "E&O") are not valid companion names; storing them inside JSON avoids the issue.
- Word Online credits tracked changes and comments to the signed-in user, whatever author is requested. Fix in the packaged copy with sanitize_docx.py, and add a visible note under the title naming the counterparty.
- Never retry comment edits in Word Online; duplicates appear and cannot be deleted there. Add exactly one comment and fix the XML afterwards.
- Document properties (creator, last modified by) carry the builder's name; scrub them before distribution.
- Check for name clashes across scenarios (for example a company name reused as a counterparty).
- Seed emails come from the user, so the simulated sender and date go in the body. Teams posts cannot be backdated.
- Real case citations in fictional documents should be verified or replaced before customer use.
