#!/usr/bin/env bash
# Build team-NN_submission.zip from the repo root and run the organizers' checker on it.
# Usage: code/scripts/make_submission.sh NN
set -euo pipefail

team="${1:?usage: $0 NN (two-digit team number)}"
root="$(cd "$(dirname "$0")/../.." && pwd)"
zip_name="team-${team}_submission.zip"

cd "$root"
rm -f "$zip_name"
zip -rq "$zip_name" CLIENT_MEMO.md TEAM_DOC.md code runs \
  -x '*__pycache__*' '*.pyc' '*.DS_Store' '*.gitkeep' '*.env'
echo "Built $root/$zip_name"
python3 brief/check.py "$zip_name"
