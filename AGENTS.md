# Rules for AI agents in this repo

Read [`README.md`](README.md) for what the hackathon asks. The rules below are about **how** you
change this repo. They apply to every agent (Claude Code, Codex, Cursor, …) and every subagent.

## 1. Every task gets its own branch — never work on `main`

1. Start from the latest `main`:
   ```bash
   git fetch origin
   git switch -c agent/<area>-<short-task> origin/main
   ```
2. If other agents may be working at the same time, use a separate worktree instead of switching
   branches in the shared checkout:
   ```bash
   git worktree add ../talp-<short-task> -b agent/<area>-<short-task> origin/main
   ```
3. Commit **only** to your branch. Never commit, merge, rebase or force-push onto `main`.
4. One branch = one task. If you discover unrelated work, note it in your final report instead of
   doing it on the same branch.
5. When done, push the branch and open a pull request into `main`:
   ```bash
   git push -u origin agent/<area>-<short-task>
   gh pr create --base main --fill
   ```
   A human reviews and merges. Do not merge your own PR unless the human explicitly tells you to.
6. Finish with a short report: branch name, PR link, what changed, what you ran, what is not verified.

### Branch naming

`agent/<area>-<short-task>`, lowercase, hyphens only. Areas:

| Area | Covers |
|---|---|
| `personas` | persona spec, attributes, distributions, `code/personas/` |
| `world` | weekly loop, information channels, crisis handling, persona actions |
| `llm` | Vertex AI client, prompts, parallelism, retries, logging to `calls.jsonl` |
| `metrics` | persona weights, goal computation, `metrics.json` |
| `decisions` | `code/config/decisions/`, budget math, `docs/decisions-log.md` |
| `crises` | `code/config/surprises/`, `docs/crisis-log.md` |
| `runs` | regenerating the five official runs in `runs/` |
| `docs` | `CLIENT_MEMO.md`, `TEAM_DOC.md`, `docs/` |
| `tools` | scripts, packaging, live persona interview |

Examples: `agent/personas-generate-v1`, `agent/llm-async-client`, `agent/runs-final-1745`.

## 2. Commits and a clean git history

The history of `main` must read like a changelog of the project. Keep it clean:

- **One logical change per commit.** Don't mix a refactor, a feature and a config change.
- **Commit message format:** `<area>: <imperative summary>` (subject ≤ 72 characters), a blank line,
  then a short body saying *why* when it isn't obvious. Example:
  `personas: add weight table for savers with large balances`.
- **No noise commits** ("wip", "fix", "typo", "asdf") in a PR. Tidy your own branch before you open
  the PR (`git commit --amend`, `git commit --fixup` + autosquash).
- **Linear history:** update your branch with `git rebase origin/main`, never by merging `main` into
  it. Rewrite only your own branch; never rewrite or force-push `main` or someone else's branch.
- **PRs are squash-merged** into `main`, so each task becomes one well-described commit. The PR title
  follows the same `<area>: <summary>` format and becomes that commit's subject.
- **Delete the branch** (and its worktree) after it is merged.
- **Never commit** secrets (`.env`, the key), generated scratch output (experiments go to
  `experiments/`, which is git-ignored), virtualenvs, caches, or ZIP files.
- `runs/` is changed **only** on an `agent/runs-...` branch, by running the pipeline — never by hand.

## 3. Hard rules

- **Never write the Vertex key (`TALP_KEY`) into any file.** Read it from the environment. `.env` is
  git-ignored; `.env.example` holds only the placeholder.
- **Do not edit `brief/`.** It is the organizers' material and our source of truth.
- **The LLM must produce persona behavior.** Never hard-code or post-edit a persona's status, answer
  or score. Every weekly status and probe score must trace to a logged call in `calls.jsonl`.
- **Decisions are copied word for word** from the dashboard into `code/config/decisions/plan.json`.
  Do not paraphrase a locked message.
- **Keep runs fast.** Persona calls run in parallel; a full five-run regeneration must fit in the
  17:30–18:00 window.
- **Stay inside the brief:** decision menu levels, $4M budget, red lines in
  [`brief/10-cobalt-bank.md`](brief/10-cobalt-bank.md).
- If you touch anything under `runs/`, build and check the ZIP with
  `code/scripts/make_submission.sh NN` and include the checker output in your report. (Run the
  checker on the ZIP, not on the repo folder: it would also scan `.env` and flag the key.)
