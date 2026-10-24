#!/usr/bin/env bash
# Regenerate the five official runs in parallel, then build and check the submission ZIP.
#
# Usage: code/scripts/run_all.sh [--weeks N] [--out-root DIR]
#   --weeks N       weeks per run, passed to the engine (default 10; use fewer only for smoke tests)
#   --out-root DIR  parent of the five run folders (default runs). make_submission.sh packages
#                   runs/ only, so packaging is skipped for any other DIR.
#   TEAM=NN         two-digit team number for the ZIP name (default 07)
#
# Run from the repo root (the script also cd's there). Reads TALP_KEY from the environment or
# .env; the key is never written anywhere. Every run uses the same personas, settings and surprises.
set -euo pipefail

usage() { sed -n '4,8p' "$0" | sed 's/^# \{0,1\}//'; }

weeks=10
out_root=runs
while [[ $# -gt 0 ]]; do
  case "$1" in
    --weeks) weeks="${2:?--weeks needs a number}"; shift 2 ;;
    --weeks=*) weeks="${1#*=}"; shift ;;
    --out-root) out_root="${2:?--out-root needs a directory}"; shift 2 ;;
    --out-root=*) out_root="${1#*=}"; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown argument: $1" >&2; usage >&2; exit 2 ;;
  esac
done
if ! [[ "$weeks" =~ ^[0-9]+$ ]] || (( weeks < 1 || weeks > 10 )); then
  echo "--weeks must be a whole number from 1 to 10" >&2; exit 2
fi
out_root="${out_root%/}"

cd "$(dirname "$0")/../.."

if [[ -f .env ]]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi
if [[ -z "${SSL_CERT_FILE:-}" && -f /etc/ssl/cert.pem ]]; then
  export SSL_CERT_FILE=/etc/ssl/cert.pem
fi
if [[ -z "${TALP_KEY:-}" ]]; then
  echo "TALP_KEY is empty: export it or put it in .env (never in code). Nothing was run." >&2
  exit 1
fi

py=python3
[[ -x .venv/bin/python ]] && py=.venv/bin/python
export PYTHONPATH=code
export PYTHONUNBUFFERED=1

personas=code/personas/personas.jsonl
network=code/personas/network.json
plan=code/config/decisions/plan.json
surprises=code/config/surprises
targets=code/config/decisions/targets.json
aliases=code/config/decisions/action-aliases.json
settings=code/config/engine.json

[[ -f "$personas" ]] || { echo "Missing $personas" >&2; exit 1; }
[[ -f "$settings" ]] || { echo "Missing $settings" >&2; exit 1; }
[[ -f "$plan" ]] || { echo "Missing $plan: copy the two locked decisions there word for word" >&2; exit 1; }
[[ -d "$surprises" ]] || { echo "Missing directory $surprises" >&2; exit 1; }

shopt -s nullglob
surprise_files=("$surprises"/*.json)
shopt -u nullglob
if (( ${#surprise_files[@]} == 0 )); then
  echo "############################################################################" >&2
  echo "WARNING: $surprises has no *.json announcements." >&2
  echo "plan_1 and plan_nosurprises will send identical prompts and FAIL the checker." >&2
  echo "Add every dashboard announcement (and update) before the official runs." >&2
  echo "############################################################################" >&2
fi

common=(--personas "$personas" --settings "$settings" --surprises "$surprises" --weeks "$weeks")
if [[ -f "$network" ]]; then
  common+=(--network "$network")
else
  echo "Note: $network not found; running without declared ties." >&2
fi
decide=(--decisions "$plan")
[[ -f "$targets" ]] && decide+=(--targets "$targets")
[[ -f "$aliases" ]] && decide+=(--action-aliases "$aliases")

# Seeds are fixed: plan_1 and nodecision_1 share seed 1, so their difference is the plan.
names=(plan_1 plan_2 nodecision_1 nodecision_2 plan_nosurprises)
build_args() {  # build_args NAME -> sets the global array run_args
  run_args=("${common[@]}")
  case "$1" in
    plan_1)           run_args+=(--seed 1 --probe "${decide[@]}") ;;
    plan_2)           run_args+=(--seed 2 "${decide[@]}") ;;
    nodecision_1)     run_args+=(--seed 1 --probe) ;;
    nodecision_2)     run_args+=(--seed 2) ;;
    plan_nosurprises) run_args+=(--seed 1 --no-surprises "${decide[@]}") ;;
  esac
}

# Preflight every input set without model calls before deleting any earlier run.
for name in "${names[@]}"; do
  build_args "$name"
  if ! "$py" -m sim "${run_args[@]}" --validate-only >/dev/null; then
    echo "Preflight failed for $name; no run folder was touched." >&2
    exit 1
  fi
done

if [[ "$out_root" == runs && "$weeks" != 10 && "${ALLOW_SHORT_RUNS:-0}" != 1 ]]; then
  echo "A $weeks-week run must not replace the official runs; use --out-root experiments/<name> (or ALLOW_SHORT_RUNS=1)." >&2
  exit 2
fi

# New runs are produced in a staging folder; the existing runs/<name> are replaced only after all
# five succeed, and the previous set is kept under experiments/runs-backup/<timestamp>/.
stamp="$(date +%Y%m%d-%H%M%S)"
log_dir="experiments/run_all-logs/$stamp"
stage="$out_root/.staging-$stamp"
mkdir -p "$out_root" "$log_dir" "$stage"
started=$SECONDS
pids=()
for name in "${names[@]}"; do
  build_args "$name"
  (
    begin=$SECONDS
    status=0
    "$py" -m sim "${run_args[@]}" --out "$stage/$name" >"$log_dir/$name.log" 2>&1 || status=$?
    echo "$status $((SECONDS - begin))" >"$log_dir/$name.status"
    exit "$status"
  ) &
  pids+=("$!")
  echo "Started $name (pid $!): $stage/$name, log $log_dir/$name.log"
done

failed=0
for i in "${!names[@]}"; do
  name="${names[$i]}"
  if wait "${pids[$i]}"; then status=0; else status=$?; fi
  elapsed="?"
  [[ -f "$log_dir/$name.status" ]] && elapsed="$(cut -d' ' -f2 "$log_dir/$name.status")"
  if (( status == 0 )); then
    echo "  ok   $name (exit 0, ${elapsed}s)"
  else
    failed=1
    echo " FAIL  $name (exit $status, ${elapsed}s); last lines of $log_dir/$name.log:"
    tail -n 5 "$log_dir/$name.log" | sed 's/^/        /'
  fi
done
echo "Total wall time: $((SECONDS - started))s"
if (( failed )); then
  echo "At least one run failed; previous runs in $out_root/ are untouched. New outputs: $stage/" >&2
  exit 1
fi
backup="experiments/runs-backup/$stamp"
for name in "${names[@]}"; do
  if [[ -d "$out_root/$name" ]]; then
    mkdir -p "$backup"
    mv "$out_root/$name" "$backup/$name"
  fi
  mv "$stage/$name" "$out_root/$name"
done
rmdir "$stage" 2>/dev/null || true
[[ -d "$backup" ]] && echo "Previous runs moved to $backup/"
echo "Runs are in $out_root/"

if [[ "$out_root" != runs ]]; then
  echo "Runs are in $out_root/, not runs/: skipping make_submission.sh (it packages runs/)."
  exit 0
fi
status=0
code/scripts/make_submission.sh "${TEAM:-07}" || status=$?
exit "$status"
