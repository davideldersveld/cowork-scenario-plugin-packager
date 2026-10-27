# <Plugin short name> – Cowork plugin install guide

Package: <zip name> (version <x.y.z>). All content is fictional sample data.

## Prerequisites
- Microsoft 365 Copilot with Copilot Cowork (desktop or web; custom plugins are not supported on mobile).
- The **<required plugin>** plugin turned on (Cowork > Sources & Skills > Plugins). The demo checks for its <n> skills before it runs.
- A SharePoint site or OneDrive where you can create folders (a dedicated demo site is recommended).

## Install
- Organization-wide (admin): Microsoft 365 admin center > Manage apps > Upload custom app > ... > Add agent > upload the zip. It appears under Cowork > Sources & Skills > Plugins > Discover.
- Personal test: `npm install -g @microsoft/m365agentstoolkit-cli`, `atk auth login`, `atk install --file-path "<path>\<zip>" --scope Personal`.

## Run
1. Turn on **<plugin short name>** and **<required plugin>** in Sources & Skills > Plugins.
2. Start a new conversation and say: **<start phrase>**.
3. Cowork checks the required skills, deploys the files and sample mail, Teams and calendar items if needed (it asks where), then runs the phases and stops at each approval gate.
4. To clean up, say: **reset the <scenario> demo**, and delete the "<root folder>" folder by hand.

## Skills in the plugin
| Skill | Purpose |
|---|---|
| <kit>-demo | Readiness check, deploy if needed, guided run with gates and optional answer key |
| <kit>-setup | Deploys the files and seeds sample items for the signed-in user only |
| <kit>-reset | Removes the seeded emails, calendar entries and chat messages |
| <kit>-assets-1..N | Store the sample files as text (base64 JSON); used only by setup, which decodes and checks them |

## Before publishing
- Replace the placeholder developer URLs in manifest.json.
- Optional: replace color.png (192x192) and outline.png (32x32, white on transparent).
- Run `wiqd plugin validate --mode deep` or upload to a test tenant to confirm against the live validation service.
