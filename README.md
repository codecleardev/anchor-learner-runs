# anchor-learner-runs

Test harness for the CodeClear AI Engineering course. **This is not course material.** The course's
project lives in the `anchor` repository of the same owner; this repository only checks
that each lesson's lab works for a learner who opens it in a cloud sandbox, and records what they would see.

## What a learner-path run is

For one lesson, on a GitHub-hosted x86_64 runner (the architecture of GitHub Codespaces):

1. Fresh `git clone` of the Anchor repo, checked out at the lesson's **before-tag** (the tag of the lesson
   before it; this is what "Open in a cloud sandbox" opens).
2. Build and start that tag's own `.devcontainer` with `@devcontainers/cli`, limited to 2 CPUs and 8 GB
   (the free Codespaces machine), network on. A tag that has no `.devcontainer` uses the pinned copy in
   `fallback/.devcontainer` and the run says so (`devcontainer_source` in `meta.json`).
3. `bash .devcontainer/post-create.sh` (the dev container's postCreate), recorded.
4. A new interactive terminal (`bash -i`, so `.venv` activates as in a codespace):
   - `save_files`: check out the lesson's own tag over the working tree. This stands in for the learner
     saving the lesson's code; it is the only step a learner does not type.
   - `convention_install`: only when the lesson changed `anchor_ai/requirements.txt`.
   - `lesson`: every `$` command of the lesson, in order, exactly as written, in one shell.
   - `suites`: `bin/rails test`, then `python3 -m pytest -q anchor_ai/tests`. If one fails, post-create
     runs again and both are repeated (`suites_after_reinstall`).

No secrets are used: the labs run offline against recorded fixtures.

## Layout

| Path | Content |
|---|---|
| `lessons/index.json` | Every lesson: id, number, before-tag, lesson tag, whether it needs a run. |
| `lessons/<lesson_id>/lesson.json` | Lesson id, content row id and `content_digest`, before-tag, lesson tag. |
| `lessons/<lesson_id>/commands.json` | The lesson's commands in order (`block`, `cmd`, optional `"expect": "fail"` with a `reason`). |
| `fallback/.devcontainer/` | Dev container used only for tags that have none. |
| `scripts/run_lesson.sh` | One run. `rec.py` writes a transcript row, `finalize.py` writes `meta.json` and `result.json`, `cast.py` the asciicast, `plan.py` the job matrix, `summary.py` the table. |
| `.github/workflows/learner-runs.yml` | The workflow. |

`lessons/` is generated from the course's serving content; do not edit it by hand.

## Running it

Actions, "learner-runs", "Run workflow", or:

```
gh workflow run learner-runs.yml -R <owner>/anchor-learner-runs -f lessons=all
gh workflow run learner-runs.yml -R <owner>/anchor-learner-runs -f lessons="3657,3667"
```

Inputs: `lessons` (ids or `all` = every lesson with `needs_run`), `anchor_repo` (empty = the
repository variable `ANCHOR_REPO`, else `<owner of this repository>/anchor`), `devcontainer` (`auto`, `repo` = never use the fallback, `fallback`), `max_parallel`
(default 20).

One job per lesson, at most 20 at a time, 60 minutes per job at most. Each job uploads one artifact,
`run-<lesson_id>`. The `summary` job writes the pass/fail table to the run's summary page and fails when
any lesson did not pass. A lesson job is green when the run was recorded, whether or not it passed.

## What a run records (`run-<lesson_id>`)

| File | Content |
|---|---|
| `transcript.jsonl` | One JSON object per step: `{phase, cmd, stdout, stderr, exit, seconds}`. Nothing trimmed. |
| `transcript.txt` | The same as a readable log. |
| `transcript.cast` | The same as asciicast v2 (made from the JSONL; timing is per step). |
| `meta.json` | `lesson_id`, `content_id`, `content_digest`, `before_tag`, `lesson_tag`, their commits and tree hashes, `repo`, `image_digest`, `arch`, `devcontainer_source`, `date_utc`, the workflow run, and the sha256 of `transcript.jsonl`. |
| `result.json` | `pass`, `setup_ok`, commands that exited non-zero, suite results, seconds. |
| `commands.json`, `setup.sh`, `learner.sh`, `devcontainer_up.log` | Exactly what ran. |

`pass` is strict: setup ok, every command exited 0 (except those marked `"expect": "fail"`, which must
fail), the commands run are the lesson's commands, and both suites were green on the first try.

## Pinned versions

| What | Version |
|---|---|
| `actions/checkout` | v7.0.1 (`3d3c42e5aac5ba805825da76410c181273ba90b1`) |
| `actions/upload-artifact` | v7.0.2 (`cf430e030ddbb5b0abf93d22962f4752f3646cd9`) |
| `actions/download-artifact` | v8.0.2 (`9000827ccba6bdab643e8b6fd33ac0654aef8333`) |
| `@devcontainers/cli` | 0.90.0 |

The workflow has `permissions: contents: read` and runs only on `workflow_dispatch`.
