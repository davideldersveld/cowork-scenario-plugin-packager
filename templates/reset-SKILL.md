---
name: {{KIT}}-reset
description: |
  Removes the {{SHORT_TITLE}} demo content from the signed-in user's mailbox, calendar and Teams self-chat so the demo can be run again cleanly. Use when the user says "reset the demo", "clean up the demo", {{TRIGGERS}}"remove the demo emails", or "uninstall the demo content".
license: Sample content for demonstration only
metadata:
  author: {{KIT_AUTHOR}}
  version: "{{VERSION}}"
---

# Reset the {{SHORT_TITLE}} demo

1. Find the items: emails in the signed-in user's mailbox whose subject starts with "{{PREFIX}}"; calendar events whose subject starts with "{{PREFIX}}"; messages in the user's Teams chat with themselves that start with "{{PREFIX}}Teams thread". Use a single script to collect them.
2. Show a table: Type | Count | Example subject. Only items with the "{{PREFIX}}" prefix are in scope. Never touch anything else.
3. Ask for one confirmation, then delete the listed emails, calendar events and chat messages. Report Deleted / Failed per type.
4. Files: Cowork cannot delete SharePoint or OneDrive files. Tell the user to delete the "{{ROOT_FOLDER}}" folder from the library where it was deployed, or keep it for the next run.
5. Outputs the demo created (memos, minutes, trackers) are listed but not deleted; the user decides.
