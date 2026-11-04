# kaggle-competition-create (Claude Code skill)

A Claude Code skill that creates and fully configures a **private Kaggle Community Prediction competition** end to end: Kaggle CLI first, Playwright MCP for the website-only steps, then verification.

## Install

```bash
git clone <this-repo-url> /tmp/kcc && cp -R /tmp/kcc/kaggle-competition-create ~/.claude/skills/
```

Then ask Claude Code to create a Kaggle competition, or invoke `/kaggle-competition-create`.

## Contents

- `kaggle-competition-create/SKILL.md` - the workflow and rules
- `kaggle-competition-create/scripts/split_data.py` - stdlib-only stratified split that builds train/test/sample_submission/solution (with `Usage` column)
- `kaggle-competition-create/references/lessons.md` - error table and checklist-to-tool map

## Requirements

Kaggle CLI 2.2.x (`uv tool install kaggle --with six`), a Kaggle API token (set `KAGGLE_API_TOKEN` in the shell, never commit it), a phone-verified Kaggle account, and the Playwright MCP server.
