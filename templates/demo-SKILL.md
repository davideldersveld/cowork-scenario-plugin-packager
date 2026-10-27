---
name: {{KIT}}-demo
description: |
  Starts and runs the {{SHORT_TITLE}} scenario demo end to end with the {{REQUIRED_PLUGIN}} skills. {{SUMMARY}} Checks that the required skills are installed, deploys the sample files if needed, then walks the presenter through {{N_PHASES}} phases with human approval gates. Use when the user selects this demo plugin or says "start", "start the demo", {{TRIGGERS}}"next phase", or "continue the demo".
license: Sample content for demonstration only
metadata:
  author: {{KIT_AUTHOR}}
  version: "{{VERSION}}"
---

# {{TITLE}}

Everything in this demo is fictional sample data. Every output is a draft for professional review, not advice. Never send, post or share anything to anyone other than the signed-in user during the demo.

## Step 0: Readiness check (always first, every new session)

1. Read `references/required-skills.md`. For each of the {{N_SKILLS}} required skills, confirm a skill with that exact name (or ending with that name after a plugin prefix) is in your list of available skills. Do not invoke them to test.
2. Confirm you can reach the user's OneDrive or SharePoint, Outlook mail and calendar, and Teams chat tools.
3. Show the result as a table: Skill | Status (Available / Missing).
4. If any required skill is missing, STOP. Tell the user which skills are missing and that they come from the {{REQUIRED_PLUGIN}} plugin: open Cowork > Sources & Skills > Plugins, find "{{REQUIRED_PLUGIN}}" (Discover or Shared with me), turn it on, then start a new conversation and say "{{START_PHRASE}}". If it is not listed, their Microsoft 365 admin must make it available. Do not run any phase with missing skills.
5. If everything is available, say "Ready: all {{N_SKILLS}} {{REQUIRED_PLUGIN}} skills are available" and continue.

## Step 1: Make sure the sample files are deployed

1. Search the user's OneDrive and SharePoint for files whose names start with "{{PREFIX}}". If {{N_FILES}} are found, note the folder ("{{ROOT_FOLDER}}") and continue.
2. If fewer are found, tell the user the sample files are not deployed and run the `{{KIT}}-setup` skill. Resume here when it reports success.
3. Remind the presenter that newly uploaded files can take time to appear in search. Phase prompts name the folder so the files can be read directly.

## Step 2: Introduce the scenario

Present `references/scenario.md` as a short briefing: the scenario, the phases and the gates. Offer two modes and ask which one to use:
- **Presenter mode:** run each phase, then show the matching rows of `references/answer-key.md` so the audience sees what the skills found.
- **Audience mode:** run each phase without the answer key.

## Step 3: Run the phases with human gates

Use the prompts in `references/phase-prompts.md`, in order. For each phase:
1. Tell the user the phase name, the skills it uses, and the inputs (folder names).
2. Run the phase prompt as written, replacing [Demo folder] with the deployed folder location.
3. Summarize the outputs and where they were saved.
4. At a gate, STOP. Show the gate from `references/gates.md` (decision, who decides, what Cowork did) and ask "Approve, revise, or stop?". Continue only on an explicit approval. Record the decision in a running log.

Phase order: {{PHASE_ORDER}}.

The user can say "skip to phase N" or "next phase". If they skip ahead, warn which earlier outputs the phase expects and use the source files instead.

## Step 4: Wrap up

Give a closing table: Phase | Skills used | Outputs | Gate decision. Count the distinct {{REQUIRED_PLUGIN}} skills used (target {{N_SKILLS}}). In presenter mode, show the answer-key score (planted issues found / total). Offer the `{{KIT}}-reset` skill to remove the demo emails, calendar entries and chat messages.

## Rules

- Draft only. Create email and Teams content as drafts addressed to the signed-in user; never send to other people.
- Mark every output "{{OUTPUT_MARKING}}".
- Quote the source document and section for every finding. Separate facts found in the files from assumptions.
- Reference digests and any citations in the sample files are illustrative and unverified; say so if the user relies on them.

## Additional resources

- `references/required-skills.md` – the {{N_SKILLS}} skills checked in Step 0, and where each is used
- `references/scenario.md` – scenario, parties, inputs and outputs by phase
- `references/phase-prompts.md` – the prompt for each phase
- `references/gates.md` – the human approval gates
- `references/answer-key.md` – the planted issues each phase should find
