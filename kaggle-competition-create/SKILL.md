---
name: kaggle-competition-create
description: Create and fully configure a private Kaggle Community Prediction competition end to end, using the Kaggle CLI first and Playwright MCP for website-only steps. Use when the user wants to create, host, set up, or generate a Kaggle competition (private or otherwise), upload competition data or a solution file, set a scoring metric, or get a competition to 10/10 on the launch checklist.
---

# Kaggle competition creation (CLI first, Playwright for the rest)

Proven flow (Kaggle CLI 2.2.x). Work in this order. Track done/failed/pending and never claim a step worked without checking it.

## 0. Rules of engagement
- **Never launch** the competition and **never invite anyone** unless the user explicitly says so. Default is private, host-only.
- Never print or save the API token. Pass it as `export KAGGLE_API_TOKEN=...` inside the command only. Remind the user to revoke a one-time token at the end.
- Don't bypass phone verification, CAPTCHA, or MFA. Stop and ask the user.
- Don't chain `create` after a validation step with `&&`/`;`. Validate first, then create.
- Quote subcommands as separate words: `kaggle competitions settings get X`, not `"settings get"`. `--debug` is a global flag (`kaggle --debug competitions ...`).

## 1. Gather the spec (ask only for what's missing)
Title (<=60 chars), slug (globally unique; append the username), brief description (<=140 chars), dataset source URL (or let the user say "you pick"), target column and positive class, metric, deadline, who gets access. If the user says "you pick", choose a small public tabular dataset from its original source (UCI etc.) and say so.

## 2. Set up the CLI and auth
```bash
export PATH="$HOME/.local/bin:$PATH"
kaggle --version || uv tool install kaggle --with six   # plain install fails: missing `six`
export KAGGLE_API_TOKEN=<token>; kaggle config view | sed 's/KGAT_[a-z0-9]*/[redacted]/g'
```
Host commands live under `kaggle competitions`: `init, create, data update, settings get/update, solution create/status, host-add, launch, submit --sandbox`. Check `-h` before using any of them.

## 3. Prepare data locally (own scratch dir, never the project root)
Use `scripts/split_data.py` (stdlib only, stratified split, anonymized ids, writes `data/` and `private/`):
```bash
python3 -I scripts/split_data.py --src raw.csv --target diagnosis --out build --id-col id --test-frac 0.3 --usage-split
```
Outputs: `data/train.csv`, `data/test.csv`, `data/sample_submission.csv`, `private/solution.csv` (with `Usage` column when `--usage-split`). Then validate: header-stripped ids match across test, sample_submission, solution; no train/test id overlap; no empty cells. (Compare after dropping the header rows. An earlier check failed only because both headers contain `id`.)

**The solution file must have a `Usage` column** with values Public / Private / Ignored (about 50/50, stratified), plus the id column and target. Without it the site rejects the file.

## 4. Create the competition (CLI)
```bash
kaggle competitions init <dir>          # writes competition-metadata.json
# edit: title, slug, briefDescription, "privacy": "PRIVATE"
kaggle competitions create -p <dir>     # prints the competition URL
```
- Error `400 FAILED_PRECONDITION: Phone verification required` means the user must verify their phone at kaggle.com/settings. Pause and ask, then rerun.
- The default deadline is in the past. It must be fixed (step 6).

## 5. Upload data and solution (CLI)
```bash
kaggle competitions data update <slug> -p build/data -m "Initial data"
kaggle competitions files <slug>
```
Do **not** upload the solution yet: it fails with `Scoring metric must be set to upload a solution` until step 6a is done.

## 6. Website-only steps (Playwright MCP, browser is already logged in)
Open `https://www.kaggle.com/competitions/<slug>/settings/launch-checklist` and work down the 10 tasks. Re-read the banner text `completed N of 10` to confirm progress.

a. **Scoring metric**: Settings > Evaluation Metric > Select Metric. Click the radio (`role=radio`, nth index), then the **Select** button. Click the label/radio, not the row's external-link icon (it opens a new tab; close it). Defaults for F1 are `average=binary, pos_label=1`. Common picks: Accuracy, F1, ROC AUC, Log Loss, MSE, MAE.
Then **upload the solution via CLI**: `kaggle competitions solution create <slug> -p solution_with_usage.csv`, and confirm with `solution status --json` (`ready: true`).

b. **Sandbox submission** (CLI): `kaggle competitions submit <slug> -f build/data/sample_submission.csv -m "Sandbox test" --sandbox --wait 300`. A score of 0 is fine; it only has to score successfully.

c. **Deadline / Key Dates**: settings/key-dates. The API returns 403 for this, so use the form. Spinbuttons can't be `fill`ed: click the Month spinbutton, then `page.keyboard.type('MMDDYYYYhhmmssAM/PM')` (e.g. `02012027115900PM`). Fill both End Date and Private Leaderboard Release Date, click the *enabled* Save (`button[aria-disabled="false"]`). Deadline must be in the future and at most one year after launch. Verify with `settings get` (shown in UTC).

d. **Dataset description and license** (Data tab): Edit dataset description, and Metadata > Edit License. Pick the license that matches the original source (check the source page; UCI shows it). The license dropdown options contain external-link icons: click the option text via a mouse click offset from the option's left edge.

e. **Overview tab**: Edit Abstract, then Edit Section for Description and Evaluation. All sections must lose their default text.

f. **Rules tab**: Edit Section. Replace every `[INSERT]` in the competition-specific block (title, sponsor, address, website slug, prizes, winner license, data access), delete the "choose 1 of 3" data-use block in 4a and keep one paragraph consistent with the dataset license, and replace the winners' license brackets (use "None" if there are no prizes). Confirm no `[INSERT`/`[CHOOSE` remains. Tell the user which legal values were assumed.

## 7. Playwright editing gotchas (these cost time before)
- Markdown editors are a MUI `textarea`, and `Meta+A`/`Control+A` then Delete and `fill` do **not** reliably clear them. Set the value with the native setter, then dispatch an input event:
  `Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype,'value').set.call(t, text); t.dispatchEvent(new Event('input',{bubbles:true}))`
  Pick the visible textarea (`offsetHeight>0`), since hidden duplicates exist.
- Save buttons: several `Save` buttons are in the DOM. Use `getByRole('button',{name:'Save',exact:true}).first()` (a loose match hits the disabled "Edit X (Save or Cancel to enable)" button). If a click is intercepted, dismiss the cookie banner ("OK, Got it.") first.
- Don't add a `## Heading` that repeats the section title (it renders twice).
- `browser_click` needs `target` (not `ref`), and `browser_run_code_unsafe` is the most reliable tool for multi-step form work. Prefer `innerText` evaluates over full snapshots, which are huge.
- Take a screenshot when a step silently does nothing.

## 8. Final verification (report only what you checked)
- CLI: `files`, `settings get`, `solution status`, `hosts`.
- Site: header says `Private · Unlaunched`, Access & Teams shows Private selected, banner says `10 of 10`.
- Give the direct URL `https://www.kaggle.com/competitions/<slug>`, list assumptions (rules text, dataset choice), say it is not launched, and say how to launch (checklist > Launch Competition, or `kaggle competitions launch <slug>`). To grant someone host access: `kaggle competitions host-add <slug> -u <username>`. Inviting participants is done on the site (Access & Teams) and only on request.

See `references/lessons.md` for the error table.
