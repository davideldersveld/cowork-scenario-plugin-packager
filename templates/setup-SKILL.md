---
name: {{KIT}}-setup
description: |
  Deploys the {{SHORT_TITLE}} demo kit ({{N_FILES}} fictional sample files plus sample emails, Teams messages and calendar entries) to a SharePoint site or OneDrive folder the user chooses. Use when the user says "deploy the demo", "set up the demo", "install the demo files", {{TRIGGERS}}"deploy the demo kit to [site URL]", or when the {{KIT}}-demo skill finds the files missing.
license: Sample content for demonstration only
metadata:
  author: {{KIT_AUTHOR}}
  version: "{{VERSION}}"
---

# Deploy the {{SHORT_TITLE}} demo kit

All content is fictional sample data marked "SAMPLE DATA – FICTIONAL – FOR DEMONSTRATION ONLY".

## Step 1: Choose the destination

1. If the user gave a SharePoint site URL or name, find the site and list its document libraries. Use the "Documents" library unless the user names another.
2. If the user gave nothing, ask once: "Deploy to your OneDrive (folder '{{ROOT_FOLDER}}') or to a SharePoint site? If SharePoint, paste the site URL." Default to OneDrive if they have no preference.
3. Recommend a dedicated demo site or folder, not a working site.
4. Ask whether to also add the sample mailbox, Teams and calendar items (default yes). These go only to the signed-in user.

## Step 2: Stage the files

1. The sample files are stored as text in {{N_PARTS}} asset skills in this plugin: {{ASSET_SKILL_LIST}}. Each holds flat `references/asset-NNN.json` files (one per sample file, base64-encoded). Load each asset skill with the skill tool to get its directory. Do not read the asset files into the conversation.
2. Run `python scripts/stage_assets.py <this skill's directory> working/{{KIT}} <asset skill directory> [<asset skill directory> ...]`. It decodes every file into the session workspace under its folder with its original name, checks size and SHA-256, and reports anything missing. If you cannot pass the directories, run it with only the first two arguments: it looks for the asset skills as sibling folders and then searches nearby.
3. If `scripts/stage_assets.py` is not present, decode with this Python instead, passing each asset skill directory in `dirs`:
   ```python
   import base64, glob, json, os
   dirs = ["<asset skill directory 1>", "<asset skill directory 2>"]
   for d in dirs:
       for p in sorted(glob.glob(os.path.join(d, "references", "asset-*.json"))):
           doc = json.load(open(p, encoding="utf-8"))
           out = os.path.join("working/{{KIT}}", doc["folder"]); os.makedirs(out, exist_ok=True)
           open(os.path.join(out, doc["name"]), "wb").write(base64.b64decode(doc["data"]))
   ```
   Then count the files against `references/asset-manifest.json`.
4. If any file is missing or fails its checksum, stop and report it. Do not seed emails, Teams messages or calendar entries without the files.

## Step 3: Create folders and upload

1. Create a top-level folder "{{ROOT_FOLDER}}" in the destination library, with the subfolders listed in the manifest.
2. Upload every file to its subfolder, keeping the exact filename. Run the uploads in one script, not one call at a time.
3. If a file already exists, skip it and report it as already present. Never overwrite.
4. Upload a short "README – {{ROOT_FOLDER}}.md" to the first folder stating: fictional sample data, the as-of date ({{AS_OF}}), the folder list, and "To start, select the demo plugin and say: {{START_PHRASE}}".

## Step 4: Seed the mailbox, Teams and calendar (if the user agreed)

Use `references/seed-content.json`.
1. Emails ({{N_EMAILS}}): send each one to the signed-in user only, with the subject and HTML body as given. The body already shows the simulated sender and date. Never add other recipients.
2. Teams ({{N_TEAMS}}): post each message in the user's chat with themselves.
3. Calendar ({{N_EVENTS}}): create each event on the user's own calendar with no attendees and no online meeting, using the given subject, start, end, all-day flag, location and show-as values. Times are local to the user.
4. Skip any item whose exact subject already exists, so a rerun does not create duplicates.

## Step 5: Verify and report

1. Count the uploaded "{{PREFIX}}" files in the destination (expect {{N_FILES}}) and the seeded items.
2. Report a table: Item | Expected | Created | Skipped | Failed, plus the folder link.
3. Note that search can take time to index new files; the demo prompts read the folders directly.
4. Tell the user the next step: "Say: {{START_PHRASE}}".

## Additional resources

- {{ASSET_SKILL_LIST}} – asset skills holding the sample files as base64 text in `references/asset-NNN.json`
- `references/asset-manifest.json` – folder, original file name, stored payload, asset skill, size and SHA-256 for every file
- `references/seed-content.json` – sample emails, Teams messages and calendar entries
- `scripts/stage_assets.py` – decodes the files from the asset skills into the workspace with their original names and verifies size and SHA-256
