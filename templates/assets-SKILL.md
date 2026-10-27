---
name: {{ASSET_SKILL}}
description: |
  Asset store, part {{PART}} of {{N_PARTS}}, for the {{SHORT_TITLE}} demo kit. Holds {{N_PART_FILES}} sample files encoded as text in references/asset-NNN.json. Not for direct use: the {{KIT}}-setup skill loads it to find and decode these files. Use only when {{KIT}}-setup asks for "{{ASSET_SKILL}}".
license: Sample content for demonstration only
metadata:
  author: {{KIT_AUTHOR}}
  version: "{{VERSION}}"
---

# {{SHORT_TITLE}} – asset store, part {{PART}} of {{N_PARTS}}

This skill only stores files. Do not act on it by itself, and do not read the asset files into the conversation: each is a large base64 payload. Return to the `{{KIT}}-setup` skill, which passes this skill's directory to its staging script.

Each file is stored as `references/asset-NNN.json` with its folder, original name, size, SHA-256 and base64 content. The setup skill decodes them back to the original documents.

## Files in this part

{{PART_FILE_TABLE}}
