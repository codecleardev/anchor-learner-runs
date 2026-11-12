#!/bin/bash
# One learner-path run on a GitHub-hosted runner.
#   run_lesson.sh <lesson_id> <owner/name of the Anchor repo> <auto|repo|fallback>
# Fresh clone at the lesson's before-tag, the repo's own dev container (the fallback one only for a tag that
# has none), post-create, then a new interactive terminal that saves the lesson's files (checkout of the
# lesson's tag), reinstalls requirements when the lesson changed them, runs the lesson's `$` commands exactly
# as written, then both suites. Every step is one row of out/<id>/transcript.jsonl.
# Always exits 0 once the run is recorded: pass or fail is in result.json, not in the exit code.
set -u
ID=$1; ANCHOR_REPO=$2; DC_MODE=${3:-auto}
HERE="$(cd "$(dirname "$0")/.." && pwd)"
L="$HERE/lessons/$ID"; OUT="$HERE/out/$ID"; WORK="$HERE/work"
[ -f "$L/lesson.json" ] || { echo "no lessons/$ID/lesson.json"; exit 2; }
case "$ANCHOR_REPO" in *[!A-Za-z0-9._/-]*|*/*/*|/*|*/|"") echo "bad repo name"; exit 2;; esac
rm -rf "$OUT" "$WORK"; mkdir -p "$OUT" "$WORK"
cp "$L/commands.json" "$L/lesson.json" "$HERE/scripts/rec.py" "$OUT/"
START=$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))["before_tag"])' "$L/lesson.json")
FINISH=$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))["lesson_tag"])' "$L/lesson.json")
URL="https://github.com/$ANCHOR_REPO"
T_START=$(date +%s)
git config --global --add safe.directory '*'   # the clone is handed to uid 1000 below; git on the runner still reads it

# host-side recorder: same row format as the in-container one
hrec() { local t0; t0=$(date +%s.%N); ( cd "$WORK" && eval "$2" ) >/tmp/o 2>/tmp/e </dev/null; local rc=$?; python3 "$HERE/scripts/rec.py" "$1" "$2" $rc "$t0" "$OUT"; return $rc; }

DC_SOURCE=none; CID=""; ARCH=$(uname -m); IMAGE_ID=""
finish() {
  sudo chown -R "$(id -u)" "$OUT"
  python3 "$HERE/scripts/finalize.py" "$OUT" "$WORK/anchor" "$URL" "$ARCH" "$IMAGE_ID" "$DC_SOURCE" "$(( $(date +%s) - T_START ))"
  python3 "$HERE/scripts/cast.py" "$OUT" || true
  [ -n "$CID" ] && docker rm -f "$CID" >/dev/null 2>&1
  rm -f "$OUT/rec.py" "$OUT/lesson.json"
  exit 0
}

hrec setup "git clone -q $URL anchor && cd anchor && git checkout -q $START && git rev-parse HEAD" || finish
( cd "$WORK/anchor" && git rev-parse -q --verify "refs/tags/$FINISH^{commit}" >/dev/null ) \
  || { hrec setup "cd anchor && git rev-parse --verify 'refs/tags/$FINISH^{commit}'"; finish; }

if [ "$DC_MODE" != fallback ] && [ -f "$WORK/anchor/.devcontainer/devcontainer.json" ]; then
  DC_SOURCE=repo
elif [ "$DC_MODE" = repo ]; then
  hrec setup "test -f anchor/.devcontainer/devcontainer.json  # the tag has no dev container and the fallback is switched off"; finish
else
  DC_SOURCE=harness-fallback
  rm -rf "$WORK/anchor/.devcontainer"; cp -R "$HERE/fallback/.devcontainer" "$WORK/anchor/.devcontainer"
fi

cat > "$OUT/setup.sh" <<DRV
rec() { local t0=\$(date +%s.%N); eval "\$2" >/tmp/o 2>/tmp/e </dev/null; local rc=\$?; /usr/bin/python3 /run_out/rec.py "\$1" "\$2" \$rc \$t0 /run_out; return \$rc; }
rec setup "bash .devcontainer/post-create.sh"
rec setup "git status --short"
DRV
cat > "$OUT/learner.sh" <<DRV
rec() { local t0=\$(date +%s.%N); eval "\$2" >/tmp/o 2>/tmp/e </dev/null; local rc=\$?; /usr/bin/python3 /run_out/rec.py "\$1" "\$2" \$rc \$t0 /run_out; return \$rc; }
rec terminal 'echo "VIRTUAL_ENV=\$VIRTUAL_ENV"; which python3 ruby; ruby -v; python3 --version'
rec save_files "git checkout -q $FINISH -- . && git rev-parse $FINISH"
if ! git diff --quiet $START $FINISH -- anchor_ai/requirements.txt; then rec convention_install "python3 -m pip install -q -r anchor_ai/requirements.txt"; fi
n=\$(/usr/bin/python3 -c 'import json;print(len(json.load(open("/run_out/commands.json"))))')
for i in \$(seq 0 \$((n-1))); do
  c=\$(/usr/bin/python3 -c 'import json,sys;print(json.load(open("/run_out/commands.json"))[int(sys.argv[1])]["cmd"])' \$i)
  rec lesson "\$c"
done
suites() {
  rec "\$1" "bin/rails test"
  if [ -d anchor_ai/tests ]; then rec "\$1" "python3 -m pytest -q anchor_ai/tests"; fi
}
suites suites
if /usr/bin/python3 -c 'import json,sys;sys.exit(0 if any(r["phase"]=="suites" and r["exit"] for r in map(json.loads,open("/run_out/transcript.jsonl"))) else 1)'; then
  rec reinstall "bash .devcontainer/post-create.sh"; suites suites_after_reinstall
fi
rec sizes "du -sh .venv /usr/local/bundle | cat"
DRV

# The image's user is uid 1000 (as in Codespaces); the runner's is not. Keep the image as built and hand the
# clone and the output folder to uid 1000 instead of letting the CLI rewrite the user.
sudo chown -R 1000:1000 "$WORK/anchor" "$OUT"; sudo chmod -R a+rwX "$OUT"
hrec setup "devcontainer up --workspace-folder anchor --skip-post-create --update-remote-user-uid-default off --mount type=bind,source=$OUT,target=/run_out 2>$OUT/devcontainer_up.log | tail -1" || finish
CID=$(python3 -c 'import json,sys;print(json.loads(open("/tmp/o").read().strip().splitlines()[-1]).get("containerId",""))' 2>/dev/null)
[ -n "$CID" ] || { hrec setup "false  # devcontainer up gave no container id (devcontainer_up.log)"; finish; }
IMAGE_ID=$(docker inspect --format '{{.Image}}' "$CID")
ARCH=$(docker exec "$CID" uname -m)
docker update --cpus 2 --memory 8g --memory-swap 8g "$CID" >/dev/null   # the free Codespaces machine

cd "$WORK"
devcontainer exec --workspace-folder anchor bash /run_out/setup.sh
timeout "${LESSON_TIMEOUT:-2400}" devcontainer exec --workspace-folder anchor bash -i /run_out/learner.sh 2>/dev/null
rc=$?
sudo chown -R "$(id -u)" "$OUT"
[ $rc -eq 124 ] && hrec timeout "false  # the learner terminal was stopped after ${LESSON_TIMEOUT:-2400} s"
finish
