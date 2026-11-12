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
   - `demo_before`: only for a lesson with a demo block. The commands in `demo.json` (the `$` lines of the
     demo's "before" pane, then the demo's own command) run on the before-tag files, each in its own shell
     with a 10 minute limit. The exit code is recorded (124 = stopped at the limit); it never decides pass or
     fail. `demo_before_state` is `git status --short` afterwards. The demo's "after" is the lab's own run of
     the same command in `lesson`.
   - `save_files`: check out the lesson's own tag over the working tree. This stands in for the learner
     saving the lesson's code; it is the only step a learner does not type.
   - `convention_install`: only when the lesson changed `anchor_ai/requirements.txt`.
   - `lesson`: every `$` command of the lesson, in order, exactly as written, in one shell.
     A command marked `saved_later` in `commands.json` is a red step: the lesson has the learner run it
     before saving the listed files. For that one command those files are put back to the before-tag state
     (`not_yet_saved`), then saved again from the lesson's tag (`save_files`).
   - `suites`: `bin/rails test`, then `python3 -m pytest -q anchor_ai/tests`. If one fails, post-create
     runs again and both are repeated (`suites_after_reinstall`).

No secrets are used: the labs run offline against recorded fixtures.

## Layout

| Path | Content |
|---|---|
| `lessons/index.json` | Every lesson: id, number, before-tag, lesson tag, whether it needs a run. |
| `lessons/<lesson_id>/lesson.json` | Lesson id, `code_digest`, content row id and `content_digest`, before-tag, lesson tag. |
| `lessons/<lesson_id>/commands.json` | The lesson's commands in order (`block`, `cmd`, optional `"expect": "fail"` with a `reason`, optional `saved_later` file list with `saved_later_reason`). |
| `lessons/<lesson_id>/demo.json` | The demo block's commands for `demo_before` (`block`, `pane`: `before` or `command`, `cmd`). |
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
| `meta.json` | `lesson_id`, `code_digest` (what the run is a run of: the lesson's code, terminal and lab-step blocks and its demo commands, in order; the lesson's prose is not in it, so a wording fix does not make the run stale), `content_id` and `content_digest` (the exact row, for the record), `before_tag`, `lesson_tag`, their commits and tree hashes, `before_devcontainer_tree` (the hash of the before-tag's `.devcontainer/`, which defines the image), `repo`, `image_digest` (of the image this job built: every job builds its own, so it is a record, not something two runs share), `arch`, `devcontainer_source`, `date_utc`, the workflow run, and the sha256 of `transcript.jsonl`. |
| `result.json` | `pass`, `setup_ok`, commands that exited non-zero, suite results, `demo_before` (command and exit code), seconds. |
| `commands.json`, `demo.json`, `setup.sh`, `learner.sh`, `devcontainer_up.log` | Exactly what ran. |

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
