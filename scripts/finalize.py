"""Completes meta.json and writes result.json, in the layout tmp/overnight/signoff/mech.py reads.
   finalize.py <out_dir> <clone_dir> <repo_url> <arch> <image_id> <devcontainer_source> <wall_seconds>"""
import datetime, hashlib, json, os, subprocess, sys

out, clone, url, arch, image_id, dc_source, wall = sys.argv[1:8]
L = json.load(open(f"{out}/lesson.json"))


def git(*a):
    r = subprocess.run(["git", "-C", clone, *a], capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else None


tp = f"{out}/transcript.jsonl"
rows = [json.loads(l) for l in open(tp)] if os.path.exists(tp) else []
env = os.environ.get
meta = {
    "lesson_id": L["lesson_id"], "n": L["n"], "title": L["title"], "phase": L["phase"],
    "content_id": L["content_id"], "contract_digest": L.get("contract_digest"),
    "content_digest": L["content_digest"], "content_digest_how": L["content_digest_how"],
    # what the run is bound to: the lesson's code, lab steps, terminal blocks and demo commands (not its prose)
    "code_digest": L.get("code_digest"), "code_digest_how": L.get("code_digest_how"),
    "before_tag": L["before_tag"], "lesson_tag": L["lesson_tag"],
    "before_commit": git("rev-parse", L["before_tag"] + "^{commit}"), "before_tree": git("rev-parse", L["before_tag"] + "^{tree}"),
    "lesson_commit": git("rev-parse", L["lesson_tag"] + "^{commit}"), "lesson_tree": git("rev-parse", L["lesson_tag"] + "^{tree}"),
    "before_devcontainer_tree": git("rev-parse", "--verify", "--quiet", L["before_tag"] + ":.devcontainer") if dc_source == "repo" else None,
    "tree_note": "tree hashes depend only on file contents, so they stay valid across a rebuild or push that changes commit ids",
    "repo": url,
    "image": "built by @devcontainers/cli from the tag's .devcontainer" if dc_source == "repo" else
             "built by @devcontainers/cli from the harness fallback .devcontainer (the tag has none)" if dc_source == "harness-fallback" else None,
    "devcontainer_source": dc_source,
    "image_digest": image_id or None, "image_arch": {"x86_64": "amd64", "aarch64": "arm64"}.get(arch, arch),
    "arch": arch, "platform": "linux/amd64" if arch == "x86_64" else arch,
    "machine": "GitHub-hosted runner %s; container limited to 2 cpus, 8 GB (docker update --cpus 2 --memory 8g)" % env("ImageOS", "?"),
    "network": "on, as in Codespaces",
    "date_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
    "recorder": {"harness": env("GITHUB_REPOSITORY"), "harness_commit": env("GITHUB_SHA"), "run_id": env("GITHUB_RUN_ID"),
                 "run_attempt": env("GITHUB_RUN_ATTEMPT"),
                 "run_url": "%s/%s/actions/runs/%s" % (env("GITHUB_SERVER_URL", ""), env("GITHUB_REPOSITORY", ""), env("GITHUB_RUN_ID", "")),
                 "runner_image": env("ImageOS"), "runner_image_version": env("ImageVersion"), "wall_seconds": int(wall)},
    "transcripts": {"transcript.jsonl": {"sha256": hashlib.sha256(open(tp, "rb").read()).hexdigest(), "steps": len(rows)}} if rows else {},
}
json.dump(meta, open(f"{out}/meta.json", "w"), indent=1)

# result.json: strict pass, except commands marked "expect": "fail" in commands.json (same rule as the local recorder).
cmds = json.load(open(f"{out}/commands.json"))
expect = {c["cmd"] for c in cmds if c.get("expect") == "fail"}
ph = lambda p: [r for r in rows if r["phase"] == p]
bad = lambda rs: [{"cmd": r["cmd"][:200], "exit": r["exit"]} for r in rs if r["exit"]]
lesson_bad = [{"cmd": r["cmd"][:200], "exit": r["exit"], **({"expected": True} if r["cmd"] in expect else {})} for r in ph("lesson") if r["exit"]]
unexpected_pass = [r["cmd"][:200] for r in ph("lesson") if r["cmd"] in expect and r["exit"] == 0]
final = "suites_after_reinstall" if ph("suites_after_reinstall") else "suites"
same_commands = [r["cmd"] for r in ph("lesson")] == [c["cmd"] for c in cmds]
complete = bool(ph("sizes")) and not ph("timeout")          # the learner terminal ran to its last step
setup_ok = bool(ph("setup")) and not bad(ph("setup")) and bool(ph("terminal"))
res = {"lesson_id": L["lesson_id"], "n": L["n"], "setup_ok": setup_ok, "lesson_commands": len(ph("lesson")),
       "commands_in_lesson": len(cmds), "commands_as_written": same_commands, "complete": complete,
       "lesson_failed": lesson_bad, "expected_to_fail_but_passed": unexpected_pass,
       "suites_failed_first_try": bad(ph("suites")), "suites_failed_final": bad(ph(final)) if ph(final) else [{"cmd": "suites did not run", "exit": None}],
       # the demo's commands on the before-tag files: recorded for the lesson's "before" pane, never part of pass
       "demo_before": [{"cmd": r["cmd"][:200], "exit": r["exit"]} for r in ph("demo_before")],
       "seconds": round(sum(r["seconds"] for r in rows)),
       "pass": setup_ok and complete and same_commands and not [c for c in lesson_bad if not c.get("expected")]
               and not unexpected_pass and bool(ph("suites")) and not bad(ph("suites"))}
json.dump(res, open(f"{out}/result.json", "w"), indent=1)
print(json.dumps(res))
