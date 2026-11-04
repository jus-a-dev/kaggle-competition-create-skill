# Kaggle competition creation: error table and notes

| Symptom | Cause | Fix |
|---|---|---|
| `ModuleNotFoundError: six` after `uv tool install kaggle` | undeclared dependency | `uv tool install --reinstall kaggle --with six` |
| `invalid choice: 'settings get'` | subcommand passed as one quoted word | pass separate words |
| `unrecognized arguments: --debug` | global flag | `kaggle --debug competitions ...` |
| `400 FAILED_PRECONDITION: Phone verification required` on create | host account unverified | user verifies phone at kaggle.com/settings (human step) |
| `400 ... Scoring metric must be set to upload a solution` | metric not chosen yet | choose metric on the site first, then `solution create` |
| solution uploads but `Ready: false` | missing metric or missing `Usage` column | set metric; add `Usage` (Public/Private/Ignored) |
| `403` on `settings update` (deadline etc.) | those fields are admin-only via API | use the website Key Dates form |
| `403` on `submissions` | not entered as participant | not needed; use `submit --sandbox` and the site |
| Default deadline already past | template default | set a future deadline (max 1 year after launch) |
| Generic 400 with no message | CLI hides body | call the Python API (`KaggleApi().competition_create_new(dir)`) from the tool's venv and print `e.response.text` |

## Checklist items (10) and the tool that completes each
1. Create Competition (CLI)
2. Set Deadline (site)
3. Edit Rules (site)
4. Edit Overview Tab (site: abstract plus Description and Evaluation sections)
5. Upload Dataset (CLI `data update`)
6. Add Dataset Description (site)
7. Select Dataset License (site)
8. Select Scoring Metric (site)
9. Setup Solution (CLI `solution create`, needs `Usage` column)
10. Make Sandbox Submission (CLI `submit --sandbox`)
The Launch step is separate and needs explicit user approval.

## Useful facts
- Slug must be globally unique; `<topic>-<username>` works.
- Time fields are shown in the browser's timezone (IST in this setup); the CLI shows UTC.
- Private competitions: dataset and leaderboard are visible only to invited people and hosts; the invitation link works only after launch.
- Metric hyperparameters for F1: `average="binary"`, `pos_label=1`; leaderboard sort: higher is better.
- Original run: UCI WDBC (id 17, CC BY 4.0, DOI 10.24432/C5DW2B), 569 rows, stratified 70/30 split, F1 metric.
