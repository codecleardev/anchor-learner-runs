"""Pass/fail table for the job summary. summary.py <runs_dir> <matrix json> -> SUMMARY.md, summary.json; exit 1 if any lesson did not pass."""
import json, os, sys

runs, matrix = sys.argv[1], json.loads(sys.argv[2])
rows, ok = [], True
for item in matrix["include"]:
    i = item["lesson"]
    d = os.path.join(runs, "run-%s" % i)
    try:
        m, r = json.load(open(f"{d}/meta.json")), json.load(open(f"{d}/result.json"))
    except (OSError, ValueError):
        rows.append({"lesson_id": i, "n": item["n"], "pass": False, "note": "no artifact: the job did not record a run"})
        ok = False
        continue
    notes = []
    if not r["setup_ok"]:
        notes.append("setup failed")
    if not r.get("complete", True):
        notes.append("stopped early")
    if not r.get("commands_as_written", True):
        notes.append("%d of %d commands run" % (r["lesson_commands"], r["commands_in_lesson"]))
    bad = [c for c in r["lesson_failed"] if not c.get("expected")]
    if bad:
        notes.append("first failure: `%s` (exit %s)" % (bad[0]["cmd"][:70].replace("|", "\\|").replace("\n", " "), bad[0]["exit"]))
    if r["expected_to_fail_but_passed"]:
        notes.append("expected-to-fail command passed")
    if r["suites_failed_first_try"] and not r["suites_failed_final"]:
        notes.append("suites green only after reinstall")
    if m.get("devcontainer_source") != "repo":
        notes.append("dev container: %s" % m.get("devcontainer_source"))
    rows.append({"lesson_id": i, "n": m["n"], "pass": r["pass"], "setup_ok": r["setup_ok"], "commands": r["lesson_commands"],
                 "failed": len(bad), "expected_failures": len(r["lesson_failed"]) - len(bad),
                 "suites": "fail" if r["suites_failed_final"] else "retry" if r["suites_failed_first_try"] else "ok",
                 "seconds": r["seconds"], "wall_seconds": m["recorder"]["wall_seconds"], "arch": m["arch"],
                 "before_tag": m["before_tag"], "lesson_tag": m["lesson_tag"], "content_id": m["content_id"], "note": "; ".join(notes)})
    ok = ok and r["pass"]
passed = sum(1 for r in rows if r["pass"])
md = ["# Learner-path runs: %d of %d passed" % (passed, len(rows)), "",
      "Anchor repo: `%s`. One artifact per lesson (`run-<lesson_id>`): transcript.jsonl, transcript.txt, transcript.cast, meta.json, result.json, commands.json." % os.environ.get("ANCHOR_REPO", "?"), "",
      "| # | Lesson id | Result | Setup | Commands | Failed | Suites | Seconds (steps / job) | Arch | Note |", "|---|---|---|---|---|---|---|---|---|---|"]
for r in sorted(rows, key=lambda r: r["n"]):
    if "setup_ok" not in r:
        md.append("| %s | %s | FAIL | - | - | - | - | - | - | %s |" % (r["n"], r["lesson_id"], r["note"]))
    else:
        md.append("| %s | %s | %s | %s | %s | %s | %s | %s / %s | %s | %s |" % (
            r["n"], r["lesson_id"], "pass" if r["pass"] else "FAIL", "ok" if r["setup_ok"] else "FAIL", r["commands"], r["failed"],
            r["suites"], r["seconds"], r["wall_seconds"], r["arch"], r["note"]))
open("SUMMARY.md", "w").write("\n".join(md) + "\n")
json.dump({"passed": passed, "total": len(rows), "rows": rows}, open("summary.json", "w"), indent=1)
print("\n".join(md))
sys.exit(0 if ok else 1)
