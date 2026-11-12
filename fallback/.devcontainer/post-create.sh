#!/usr/bin/env bash
# Runs once when the sandbox is created. Safe to run again by hand:
#   bash .devcontainer/post-create.sh
# Every lesson tag carries this file, so it copes with each stage of Anchor:
# a Rails app only (the first lessons), or Rails plus the Python anchor_ai
# service. A step that fails is reported at the end; the others still run.
set -uo pipefail
cd "$(dirname "$0")/.."

failed=()
step() { # step "label" command...
  echo "==> $1"; shift
  "$@" || failed+=("$*")
}

if [ -f Gemfile ]; then
  step "bundle install" bundle install --jobs 4 --retry 2
fi

# The lessons' Python convention: one virtual environment, .venv, in the
# project root. New terminals activate it on their own (see Dockerfile).
if [ ! -x .venv/bin/python3 ]; then
  step "python3 -m venv .venv" python3 -m venv .venv
fi
if [ -f anchor_ai/requirements.txt ]; then
  step "pip install -r anchor_ai/requirements.txt" .venv/bin/python3 -m pip install --quiet -r anchor_ai/requirements.txt
fi

if [ -f bin/rails ] && [ -f config/database.yml ]; then
  step "bin/rails db:prepare (development)" bin/rails db:prepare
  step "bin/rails db:prepare (test)" env RAILS_ENV=test bin/rails db:prepare
fi

echo
if [ ${#failed[@]} -gt 0 ]; then
  echo "==> Setup finished with ${#failed[@]} failed step(s):"
  printf '    %s\n' "${failed[@]}"
  echo "    Fix the cause, then run: bash .devcontainer/post-create.sh"
else
  echo "==> Ready: Ruby $(ruby -e 'print RUBY_VERSION'), Python $(.venv/bin/python3 -c 'import platform; print(platform.python_version())')."
fi
echo "    Open a new terminal (its prompt starts with (.venv)) and follow the lesson's Build steps."
echo "    After a lesson changes anchor_ai/requirements.txt or the Gemfile, run"
echo "    pip install -r anchor_ai/requirements.txt or bundle install again."
echo "    When you are done, stop this codespace (README: Run it in a Codespace) so it stops using your free hours."
[ ${#failed[@]} -eq 0 ]
