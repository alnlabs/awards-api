#!/usr/bin/env bash

set -e

# Max depth (default 5)
MAX_DEPTH=${1:-5}

# Directories to ignore
IGNORE_DIRS=(
  ".git"
  "__pycache__"
  "venv"
  ".venv"
  "env"
  ".env"
  "node_modules"
  ".mypy_cache"
  ".pytest_cache"
)

# Build prune expression for find
PRUNE_EXPR=""
for dir in "${IGNORE_DIRS[@]}"; do
  PRUNE_EXPR="$PRUNE_EXPR -name $dir -o"
done
PRUNE_EXPR="${PRUNE_EXPR% -o}"

# Detect project root (pyproject.toml or setup.py or requirements.txt)
PROJECT_ROOT=$(pwd)
while [[ "$PROJECT_ROOT" != "/" ]]; do
  if [[ -f "$PROJECT_ROOT/pyproject.toml" || \
        -f "$PROJECT_ROOT/setup.py" || \
        -f "$PROJECT_ROOT/requirements.txt" ]]; then
    break
  fi
  PROJECT_ROOT=$(dirname "$PROJECT_ROOT")
done

echo "📦 Python Project Root: $PROJECT_ROOT"
echo "📂 Folder Structure (depth=$MAX_DEPTH)"
echo "-------------------------------------"

cd "$PROJECT_ROOT"

# If tree is available, use it
if command -v tree >/dev/null 2>&1; then
  tree -L "$MAX_DEPTH" \
    -I ".git|__pycache__|venv|.venv|env|.env|node_modules|.mypy_cache|.pytest_cache"
else
  # Fallback using find
  find . \
    \( $PRUNE_EXPR \) -prune -o \
    -type d -print |
    awk -F/ '{
      indent = length($0) - length($NF);
      printf "%*s📁 %s\n", indent, "", $NF
    }'
fi