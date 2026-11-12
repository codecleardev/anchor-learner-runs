"""Turns the workflow input into the job matrix. plan.py "<all | ids>" -> prints matrix=<json> for $GITHUB_OUTPUT."""
import json, re, sys

index = json.load(open("lessons/index.json"))
want = sys.argv[1].strip() if len(sys.argv) > 1 else "all"
if want.lower() in ("", "all"):
    chosen = [L for L in index if L["needs_run"]]
else:
    ids = [int(x) for x in re.split(r"[,\s]+", want) if x]
    known = {L["lesson_id"]: L for L in index}
    missing = [i for i in ids if i not in known]
    if missing:
        sys.exit("unknown lesson ids: %s" % missing)
    chosen = [known[i] for i in dict.fromkeys(ids)]
if not chosen:
    sys.exit("no lessons selected")
if len(chosen) > 256:
    sys.exit("a matrix holds at most 256 jobs")
print("matrix=" + json.dumps({"include": [{"lesson": L["lesson_id"], "n": L["n"]} for L in chosen]}))
