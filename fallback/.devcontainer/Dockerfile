# Anchor's cloud sandbox (GitHub Codespaces, or any dev container host).
#
# The course's versions, the same ones its labs are checked against: the Ruby
# in .ruby-version (3.4.12) on Debian 13, whose Python 3 is 3.13. Only system
# packages live here, so the image builds in about a minute on a 2-core
# machine. Gems and Python packages are installed by post-create.sh from the
# checked-out lesson's own Gemfile and anchor_ai/requirements.txt, so every
# lesson tag gets exactly what that lesson needs.
ARG RUBY_VERSION=3.4.12
FROM ruby:${RUBY_VERSION}-slim-trixie

# build-essential, pkg-config, libyaml-dev, libsqlite3-dev: native gems (psych, sqlite3, bootsnap).
# python3-venv: the lessons' `python3 -m venv .venv`.
# poppler-utils, tesseract-ocr(-eng): the local OCR path of the multimodal lessons.
RUN apt-get update -qq \
 && apt-get install -y --no-install-recommends \
      git curl ca-certificates sudo less procps \
      build-essential pkg-config libyaml-dev \
      sqlite3 libsqlite3-dev \
      python3 python3-venv python3-dev \
      poppler-utils tesseract-ocr tesseract-ocr-eng \
 && rm -rf /var/lib/apt/lists/*

# A normal user, as on a learner's laptop. Gems go to the image's gem home.
ARG USERNAME=vscode
RUN useradd --create-home --shell /bin/bash --uid 1000 "$USERNAME" \
 && echo "$USERNAME ALL=(root) NOPASSWD:ALL" > /etc/sudoers.d/$USERNAME \
 && chmod 0440 /etc/sudoers.d/$USERNAME \
 && chown -R "$USERNAME:$USERNAME" /usr/local/bundle

# Every new terminal activates the project's Python virtual environment
# (.venv, created by post-create.sh), so `python3` and `pip` are the lesson's
# and the prompt starts with (.venv). Appended to the user's ~/.bashrc, after
# the lines that set the prompt.
RUN printf '%s\n' \
      '# Anchor: activate the project virtual environment in every new terminal.' \
      'if [ -z "${VIRTUAL_ENV:-}" ] && [ -f "$PWD/.venv/bin/activate" ]; then . "$PWD/.venv/bin/activate"; fi' \
      >> "/home/$USERNAME/.bashrc" \
 && chown "$USERNAME:$USERNAME" "/home/$USERNAME/.bashrc"

ENV PIP_DISABLE_PIP_VERSION_CHECK=1

USER $USERNAME
