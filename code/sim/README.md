# Two-round weekly simulation engine

This engine reads externally authored personas and an external relationship graph.
It runs two information rounds inside each week, without creating personas or
inferring relationship ties.

## What happens in a week

1. Load this week's facts, announcements and applicable bank actions. Give each
   targeted persona the locked bank message **word for word**, from its start week
   onwards. Official delivery does not use the peer-message probability or cap.
2. Route last week's round-two messages into first-round inboxes.
3. Call every persona once, concurrently within the configured request limit.
   The model chooses behavior, status, money, memory and up to two short messages.
4. After **all** first-round calls finish, route those new messages. Only recipients
   with new messages get a second model call, with their first response as history.
5. Save each persona's last valid model response as its weekly state. Keep
   round-two outgoing messages for next week; do not run a third round.

The two turns are information steps inside one week. A second turn does not pay a
second salary, grant a second goodwill credit, or start an additional week. Actions,
reviews and complaints already performed in round one cannot be erased in round two.
Phone messages are short one-way reports, rather than a simulated synchronous call.

## Exposure assumptions

| Message / relationship | Probability of seeing each message |
|---|---:|
| Social post from an undeclared stranger | 5% |
| Social post from an account the recipient follows | 35% |
| Social post from a declared close friend | 65% |
| WhatsApp message in the recipient's own group | 80% |
| Direct / phone message to a declared contact | 100% |
| Channel disabled for sender or recipient | 0% |

Close friendship takes precedence over following; probabilities are not added.
These are experimental assumptions, not estimates from observed banking customers.
Configuration lives in `code/config/engine.json`; `Settings` has identical defaults.

Each persona can receive **two peer messages total per week**, shared between both
rounds. Excess eligible messages are dropped, not retried indefinitely. Eligible
messages compete in a seeded random order. A draw depends on run seed, week, round,
message ID and recipient, so async completion order cannot change exposure.
Audit call IDs are excluded from model prompts. Reusing a seed does not guarantee
that the external model service itself returns identical text.

Set `max_peer_messages` to `0` in a settings file for an exposure-off comparison.
The model may still choose to post, but nobody receives peer messages or gets a
second call. All other facts and official delivery remain the same.

## External inputs

Python 3.10+ is required. Install `code/requirements.txt` for actual Vertex calls.
The tests and input validator otherwise use only the standard library.

**Personas JSONL:** each external record requires a unique nonempty string `id`
and a nonempty string `group`. All other fields are passed through unchanged to
the model. An optional `initial_state` object is passed in as prior state; if
absent, prior state is null and the first model response establishes behavior.
Provide a starting balance in your own data if deposit amounts are needed. The
engine does not supply missing customer attributes, distributions or weights.
It does not enforce the final-submission persona minimum on smoke experiments.

**Network JSON:** use IDs from your existing persona file. For example, replace
the placeholder IDs below with those external IDs:

```json
{
  "follows": [["YOUR_ID_2", "YOUR_ID_1"]],
  "close_friends": [["YOUR_ID_1", "YOUR_ID_3"]],
  "groups": {"YOUR_GROUP_ID": ["YOUR_ID_1", "YOUR_ID_2"]},
  "disabled_channels": {"YOUR_ID_3": ["social"]}
}
```

`follows` is `[follower, author]`. Close friendship is symmetric. A persona's private
contacts are the accounts it follows, its close friends and fellow group members.
Omitting the network means no declared ties, groups or disabled channels; public
posts may still reach strangers with 5% probability. No graph is generated.

**Decisions JSON:** use the dashboard's exact locked list. Empty list means BAU;
otherwise exactly two decisions are required. Preserve `week`, `target`, `actions`,
`message`, `channels` and `why`. `everyone` and exact persona-group names resolve
automatically. For a descriptive target, pass a separate `--targets` file:

```json
{"decision-1": ["YOUR_ID_1", "YOUR_ID_3"]}
```

The numbers refer to the decisions' original positions, starting at one. This
mapping does not modify the locked decision. `--print-menu` lists engine action
identifiers and supported level strings. If the dashboard uses a different action
name, supply `--action-aliases` mapping that exact label to an engine identifier,
instead of rewriting the locked action. Level strings must match the printed menu.
Menu costs, action durations, the $4M total and $25k per SMS send are validated.
Capped goodwill/advance audiences require external `weight_customers`. A target
larger than the cap ("up to 100,000 customers" offered to a 310,000-customer group)
is served in part: each targeted persona is drawn as a recipient with probability
cap / weighted target size, seeded by the run seed, so the expected reach equals the
cap and plan runs on one seed agree. The message still goes to the whole target;
word it for "eligible customers". `DecisionPlan.recipients(key, action)` lists who got it.
Security-pack/advance timing follows the menu where stated; an advance or goodwill
credit is offered once in its start week. Security eligibility continues after
activation; the higher offline limit only describes the migration window.
The caller chooses the two decisions and ensures the dashboard lock deadline;
the engine never selects policies or submits dashboard actions.

**Surprises:** `--surprises` accepts a JSON file or a directory of JSON files.
Each event has `id`, `week`, and its exact announcement `text`. An optional `update`
object, or `updates` list, contains later `week` and `text` values. Future events and
updates are excluded from prompts. Earlier announcements remain labelled by week.
`--no-surprises` removes these announcements and their updates while retaining the
known migration. An omitted surprises path means no surprise inputs have been supplied.

An event or update may also carry `effects`: what the announcement means in the world,
applied to every persona's "what happened to you this week" regardless of whether they
heard the text. Because they describe what really happened, an overrun announced in
week 7 still shapes week 6. With `--no-surprises` the effects vanish with the text.

```json
{"id": "overrun", "week": 7, "text": "<exact dashboard text>",
 "effects": {"migration_overrun_hours": 8,
             "support_wait_by_week": {"7": 30},
             "experience": [{"week": 6, "text": "Your Sunday payment attempts failed until the evening.",
                             "if": {"uses_p2p": true}}]}}
```

Supported keys: `migration_overrun_hours` (integer; the migration-week and following-week
lines use it), `support_wait_by_week` (week → minutes, before the extra-staff factor), and
`experience` (lines added to that week; an optional `if` requires persona attributes to equal
the given values). Transcribe the organizers' text verbatim; the effects are our reading of
it and belong in `docs/crisis-log.md`.

**World:** `code/config/world.json` contains dossier facts, the known migration,
calendar events and BAU notices. BAU notices are simulation wording, not dashboard
decisions. BAU includes the week-five email and normal holding statements. No actual
overrun, rival promotion or service-recovery outcome is invented by the engine.
The detailed migration schedule becomes customer-visible in week five, alongside
the BAU email; an earlier targeted bank message may communicate its own details.
You can pass a different `--world` file to make explicit experimental assumptions.

## Run

From the repository root, validate your inputs without a key or model calls:

```bash
PYTHONPATH=code python3 -m sim \
  --personas /path/to/your/personas.jsonl \
  --network /path/to/your/network.json \
  --settings code/config/engine.json \
  --validate-only
```

After exporting `TALP_KEY` in the environment, run an experiment:

```bash
PYTHONPATH=code python3 -m sim \
  --personas /path/to/your/personas.jsonl \
  --network /path/to/your/network.json \
  --settings code/config/engine.json \
  --decisions /path/to/locked-plan.json \
  --targets /path/to/decision-targets.json \
  --surprises code/config/surprises \
  --seed 42 \
  --out experiments/engine-seed-42
```

Use a new empty output directory each time. `--weeks 2` enables a short smoke run.
Omit `--decisions` for a no-decision run; use another seed for the second replication.
The only production transport is Vertex, using the SDK's async API, JSON schema,
positive temperature and the run seed on every request. It does not read `.env`.
See the [SDK documentation](https://googleapis.github.io/python-genai/) for the
underlying client API.

## Outputs and integration

- `run.json`: exact decisions, settings, seed, run type and completion status.
- `personas.jsonl`: byte-for-byte copy of the supplied file when run through CLI.
- `calls.jsonl`: full prompt and raw response for every request attempt, including
  invalid/failed attempts, with unique ID, persona, week, round, model and seed.
- `weekly.jsonl`: one final row per persona/week, linked to the actual final call;
  includes both round call references and received message IDs.
- `messages.jsonl`: every model-generated outgoing message, preserved verbatim.
- `exposures.jsonl`: each possible delivery's draw, probability and result:
  delivered, not seen, inbox limit or blocked bank quote.
- `state.json`: latest completed week, each persona's model-owned state, and
  pending messages. This is an inspection snapshot, not an automatic resume cache.
- `network.json`, `world.json`, `announcements.json`, `decision_targets.json`:
  the inputs used by this run, with no generated relationships or personas.

The weekly response fields are defined in `sim/schema.py`: `status`, `money`,
`balance`, `active_in_last_30_days`, `actions`, `heard_from`, `app_rating`,
`complaint`, `reason`, `memory`, `messages`. Status and money use dossier wording.
Two bookkeeping fields are derived by the engine and added to each weekly row, because
the model cannot be trusted to track them: `active_derived` (an app action in that week
or the three before it, status not `left`) and `balance_derived` (the persona's Nov 2
balance times the money factor). Metrics use the derived fields; the ledger shown to the
persona carries `balance_derived`, so model arithmetic cannot drift it.

Each persona may carry a `migration_weekend` commitment (rent autopay, Sunday payouts,
weekend card tickets above the offline limit, a single large purchase, settlement delay).
The world resolves it against the offline card limit and any overrun into plain facts:
"your rent autopay ran at Sunday 20:00, after the payee's cutoff, so a $50 late fee was
charged"; "5 of your weekend tickets were above $100: about $1,400 you could not charge".
`sim/metrics.py` turns the weekly rows and the personas' weights into `metrics.json`
(`goal_1`–`goal_3b`, `units`, stated assumptions, a by-group breakdown); `sim/probe.py`
asks the eight check-in questions at week 0 and week 11 when `--probe` is set and writes
`probe.jsonl`. `code/scripts/run_all.sh` runs the five official runs with fixed seeds and
then the organizers' checker.

For library integration, construct `SimulationEngine` with your external records,
`Network`, `World`, `Settings` and an async `Transport`, then await `run(output)`.
The supplied records are deep-copied for runtime isolation and never modified.

Invalid model JSON is retried within the configured attempt limit, with the fallback
model used on the final attempt when enabled. Exhaustion aborts the run, marks it
incomplete and cancels other requests in the current barrier. No scripted status,
score or persona answer is substituted. SDK internal retries are disabled so
requests are individually logged. Nothing is cached across runs. Bank-message
quotes are retained in raw responses but refused by the delivery router, preventing
verbatim decision messages from spreading to other audiences. Prompt guards also
reject an official message outside its permitted week or target.

## Tests

```bash
PYTHONPATH=code python3 -m unittest discover -s code/tests -v
```

Tests use minimal identity fixtures and a transport double only inside `code/tests`.
They create no production personas, call no live models and write no official runs.
With dependencies installed, the SDK contract test serializes a real SDK request
through an in-memory HTTP transport; it never contacts Vertex.
