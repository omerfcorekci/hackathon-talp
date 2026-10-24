# Team doc: how we built the Cobalt Bank simulation

Cobalt Bank lives through ten weeks (Nov 2 – Jan 10) with 24 LLM personas. Each week every persona
reads what happened to it and what it heard; the model then decides what it does, its status and what
happens to its money. We make two decisions on the bank's behalf and compare the outcome with business
as usual. Code: `code/sim/` (engine), `code/personas/` (personas), `code/config/` (world, decisions,
announcements), `code/scripts/` (runs, sweeps, viewer, live interview).

## Personas and why those attributes

Full spec: [`code/personas/spec.md`](code/personas/spec.md); one-paragraph briefs:
[`code/personas/personas-brief.md`](code/personas/personas-brief.md). `generate.py` writes
`personas.jsonl` deterministically; the same file is used in all five runs.

**Groups (4 of 5, six personas each):** paycheck customers (P1–P6), savers with large balances
(S1–S6), small business owners with a Cobalt card reader (B1–B6), everyday customers (E1–E6).
Students are left out: small balances, no lever on goal 2, and behavior close to the young everyday
personas. They are the first group we would add.

**Attributes used, and in which form**
- *Fixed fields that couple to the crisis* (dossier sector list): pay into Cobalt and payday (4 of 6
  paycheck personas are paid Fri Dec 11), balance band, above/knows the FDIC limit, number of banks,
  Cobalt as main or second bank, moves money for rate, checks the app daily, uses P2P, past fraud
  victim, financial literacy, reaction to a bank SMS.
- *Temperament* (catalog C, E, G): values, risk attitude, trust in institutions, price consciousness,
  loyalty, need for control, anxiety, anger speed, patience, forgiveness, embarrassed to complain,
  debt, living paycheck to paycheck.
- *Information* (catalog F): news sources, circle size, leader/follower/independent, sways easily,
  checks rumors, who they ask before deciding. These feed the network (`network.json`).
- *Narrative lines* (catalog A, B, I): a life (age, place, job, household), why they chose Cobalt, one
  scar, a recent life event, this quarter's fear, two or three lifestyle details. They fight sameness
  and make the live Q&A credible.
- *A concrete commitment for the migration weekend* (`migration_weekend`): rent autopay, Sunday
  payouts, weekend card tickets above $100, one big purchase, a settlement delay. The world turns it
  into plain facts ("5 of your weekend tickets were above $100: about $1,400 you could not charge").
- *Changing state*: status, money, memory, rating and complaint come only from the model's weekly
  answer and carry over to the next week.

**Left out:** race/ethnicity, religion, health, politics, immigration (not needed for the client's
question, and a stereotype risk); catalog items with no mechanism linking them to a migration or a
rate (zodiac, military service, first in family to college); more than three lifestyle details.

**Grounding:** group sizes and deposits come from the dossier (310k paycheck, 42k card readers, 105k
savers = the top 5% holding half of $6.0B, 1.643M everyday). Age and balance skews follow the general
ACS / Survey of Consumer Finances pattern (older households hold larger balances); stated as an
assumption, not fitted to microdata.

**Weights:** each persona carries `weight_customers` (2.1M in total) and `weight_deposits_usd`
(≈ $6.0B in total), uneven within a group so deposits stay heavy-tailed (S1 Victor: 1,000 customers
at $350k; S6 Chloe: 41,500 at $13k). A persona does not move its whole audience: only a share
f = 0.05–0.5 makes the same move (higher for second-bank and rate-sensitive personas, lower when pay
lands at Cobalt). Complaints and App Store reviews are rare, deliberate acts, so f is not used for
them: when a persona complains or writes a review, 1% of the customers it stands for do the same that
month, roughly TSB's complaint rate after its failed 2018 migration (95,613 complaints in about six
weeks from about 5 million customers). Formulas: [`code/sim/metrics.py`](code/sim/metrics.py) and
`assumptions` in every `metrics.json`.

## The world

**What personas see each week** (prompt built in `code/sim/prompt.py`):
- the calendar (Thanksgiving, migration weekend, Christmas, New Year) and business-as-usual notices
  (migration email in week 5, holding statements on social media);
- dashboard announcements, word for word, from their week on, reaching a persona by a seeded draw
  (90% if it checks the app daily, 60% if it follows social media, 35% otherwise);
- our decision message, word for word, only if the persona is in the target and only from its week;
- what happened to *it* this week: pay landed, the app was read-only, a ticket above the offline
  limit was declined, an autopay ran late with a fee, a transfer was queued until the system came back,
  support took N minutes. The world follows the persona's own choices: once it has left or moved its
  direct deposit, its pay no longer lands at Cobalt; a surprise can stop its pay (P2 in the shutdown);
- **"What went wrong for you since Nov 2"**: every earlier fact that actually went wrong for it (a
  declined card, a late or queued payment, lost sales, a long support wait it reported), recomputed by
  the same rules each week, so a grievance outlives the persona's three-sentence memory;
- its own history as stretches of unchanged status and money ("Weeks 1-5: main bank, money kept"),
  plus last week's memory and reason;
- **"Your open business with Cobalt"**: where its own cases stand by the bank's rules: a dispute's
  provisional credit (10 business days, or at once under the instant dispute credit) and its close
  after about 45 days, a regulator complaint's answer within 15 days, and an advance it asked for,
  paid the next week and outstanding until pay lands. Before this, P2 said he asked for the shutdown
  advance but nothing could happen; now it lands, and his trust and rating in weeks 8–10 are 3 instead
  of 2 in both plan runs;
- a rival's rate offer in week 5 (certain for rate-chasers and people with three or more banks);
- messages from other personas: posts, group chats, direct messages.

**What they can do:** check the app, try a transfer, call support, complain in the app, post, tell
friends, review the app, complain to the CFPB/BBB, dispute a charge, move some or most money, move
direct deposit, open a rival account, use Cobalt less, recommend Cobalt, wait and see. The model
picks; the engine only validates the answer against a JSON schema and retries invalid answers with
the reason.

**How an answer is built:** the persona writes its reason first (Gemini follows `propertyOrdering`,
not the order of the schema's properties), then its status, money (cumulative since Nov 2: an answer
that goes back from "moved some" to "kept" is rejected), actions, complaint, messages, its trust in
Cobalt (1–5) and mood that week, and `app_rating`: the stars it would give if the app asked it now.

**How a week runs (two rounds):** every persona is called once in parallel; their messages are routed
over the network (5% stranger post, 35% followed account, 65% close friend, 80% group chat, 100%
direct), at most three group-chat or public messages per persona per week (direct and phone messages
always arrive); only recipients get a second call, which may keep a round-one post without a new
message. A persona's quote of the bank's message is never forwarded, so the decision text cannot leak
outside its target. Status, money and memory carry over to the next week.

**Board goals from behavior** (`code/sim/metrics.py`): goal 1 counts personas that stop being active
(f × customers); goal 2 counts money moved (f × deposits); goal 3 adds new App Store ratings to the
existing 210,000 at 4.6: the app asks about 2,500 customers a month to rate it (the pace at which the
210,000 built up since 2019), and each gives its persona's current stars; a persona that writes a
review adds 1% of its customers at its stars. The cumulative average barely moves, so for the board we
also show the weekly average of the prompted ratings. Goal 3b: complaints to Cobalt reach the CFPB at
the dossier's 120 of 1,800, on top of the usual 120 a month.

**Check-ins:** both check-ins (week 0 and week 11) see the same frame: the persona's story, how it
started with Cobalt, its record, what it did beyond routine, what went wrong and its latest memory,
empty at the start. Before, the end check-in simply showed more, and trust rose in every run.

**Speed:** a five-run set takes 1–2.5 minutes in parallel (149 s in the 16:36 rehearsal with the
final decisions; `check.py`: "Nothing to fix.").

## How we read each crisis

Details and the verbatim texts: [`docs/crisis-log.md`](docs/crisis-log.md).
- **C0, the known migration (week 6).** The freeze itself is mild; harm comes from money that must
  move that weekend and from any gap between what we promised and what happened. Modelled through each
  persona's own weekend commitment, longer support waits (25 min in week 6, 12 in week 7) and a rival
  rate offer that targets the date.
- **C1, small unrecognized charges (week 3, update in week 4).** Little money, big trust hit, three
  weeks before the freeze. The week-4 update gave the facts: a processor fault that double-charged,
  plus fraud test charges on cards stolen elsewhere; Cobalt not breached; about 9,000 customers. Both
  texts reach people by the reach draw, so some hear the rumor but not the correction; the business-
  as-usual holding statement reaches only those who hear it. Our reading of what really happened sits
  in `effects`: support waits of 9 and 7 minutes in weeks 3–4, one persona (B5, standing for 7,000
  customers) who finds a double charge, and everyone else learning that their own card payments are
  all theirs (without that, E6 disputed a charge that was never on his card, which alone took goal 3b
  to 228.7). We first had three personas hit; they stood for about 307,000 customers, so we cut them
  to match the 9,000 in the update. With surprises off, texts and effects vanish together.
- **C0 outcome (week 7).** The switch ended at 16:10, about four hours late; offline card payments
  worked and queued transfers went through by Sunday night. As the known crisis's outcome it is in all
  five runs: `overrun_hours` 4 and `overrun_minutes` 10 in `world.json` plus the text as a week-7
  event. Each persona's weekend reads the same way: its window ended at 16:10 and its transfers were
  queued, not failed.
- **C2, government shutdown (week 7).** Small for the bank (roughly 10–15k paycheck customers), severe
  for those hit: no pay date before Christmas bills. None of our personas is federal, so the effects
  send P2 (a contractor's technician) home without pay, and his paydays in weeks 8 and 10 say no pay
  landed. Earliest answer: week 8. The week-8 update (Senate bill passed, House after Christmas, back
  pay promised, the Dec 30 paycheck may be missed) adds no new effect: P2's pay stays stopped.
- _Later announcements: add here as they arrive._

## Experiments

Every row: [`docs/experiments.md`](docs/experiments.md). Candidates and budget math:
[`docs/decisions-log.md`](docs/decisions-log.md). Tool: `code/scripts/sweep.py` (variants × seeds,
with the no-decision baseline).

| Plan | Idea | Cost | First result (2 seeds, before C1) |
|---|---|---|---|
| A: inform, cheap | early honest notice, $250 offline, security pack; instant dispute credit after | $0.8M | Everyone stays active; deposits 96.4%, below baseline |
| B: protect paycheck | early pay + $250 offline + 150 staff; new-money rate boost after | $2.1M | Best deposits (97.9% in both seeds) |
| C: defend deposits | +0.5 pt rate boost; goodwill + dispute credit after | $3.0M | Same deposits as B for $0.9M more |
| D: fraud first | answer C1 in week 4 (security pack + instant dispute credit); migration notice + 50 staff in week 5 | $1.05M | _to run with C1 on_ |
| none | business as usual | $0 | Deposits 97.0%; only goal 2 at risk |

**Locked:** decision 1, week 5, everyone: security pack + instant dispute credit + 50 support staff,
with the facts of the week-4 update ($0.95M). Decision 2, week 8, federal and contractor paycheck
customers: zero-interest advance up to $500 ($0.4M), mapped to P2 with about 12,000 affected
customers. Total $1.35M of $4M.

**Engine experiments (Oct 24 afternoon), same seeds before and after each change:**

| Question | Set-up | Result |
|---|---|---|
| Why do personas barely react? | logged week-6/7 prompts re-asked with variants, 576 calls (`experiments/inertia-ablation-1532`) | as is: 2 ratings, 2 non-routine actions in 96 answers; without the "most weeks little changes" lines 5 / 9; without the weekly status list 6 / 5; reason first 6 / 8; all three 14 / 12 and the first status changes |
| Does the fix change the plan comparison? | five runs before / after | plan vs no-decision differences 5–6 → 41–60 fields (seed noise 63–81) |
| Where does a decision show? | prompted rating by week, placeholder D2 with the $250 offline limit | plan above no decision in every week 5–10 in both seeds (week 6: 3.64 vs 3.34, 3.58 vs 3.13) |
| Same with the final decisions | 16:36 rehearsal, final D2 (advance) | mixed (week 6: 3.46 vs 3.24; week 7, seed 2: 3.61 vs 3.90); deposits a little better in both seeds (95.3 vs 95.1, 96.3 vs 95.9); trust at the end 3.12 vs 3.04 |
| Does the network matter? | no decision, network on vs off (`experiments/network-onoff-1643`) | personas who never heard of the charges talk about them 7/13 vs 3/13 and 6/10 vs 1/10; deposits 95.0 vs 97.0 and 95.9 vs 96.9; about a third more calls |

What we learned so far:
1. With an on-time migration and an honest notice, reactions are mild; a plan's value shows when
   something goes wrong (overrun, fraud scare).
2. A reassuring message that reality contradicts can make things worse: in one overrun run a persona
   escalated to the CFPB because "no surprises" was followed by a late fee.
3. Goal 2 moves through two savers; differences between plans are one persona's choice, so we read
   them as direction, never as size, and require two seeds before any claim.
4. Most of the "nobody reacts" came from our own prompt and schema, not from the personas: a decision
   written before its reason, an instruction that most weeks nothing changes and a history the model
   copied.
5. The lever that protected the migration week was the $250 offline limit; the final decisions answer
   the charges and the shutdown instead, and their effect on the weekly rating is mixed.
6. The network spreads what happened (rumors reach people who never saw the announcement) and costs
   1–2 points of deposits; within a week, a friend's message rarely changes a decision.

## Problems we hit and how we solved them

- **Inert simulation.** First runs: plan and no-decision identical, nobody posted, nobody reacted to
  the migration. Cause: the network was not loaded and the world never told a persona what happened
  to it, so the model invented "it went fine". Fix: load the network, add per-persona weekend
  commitments and deterministic consequences ([`docs/engine-review.md`](docs/engine-review.md)).
- **One persona = a whole audience** made results jump by tens of points. Fix: the follow share f.
- **Quiet users counted as lost.** Personas that stay but only "wait and see" were counted inactive.
  Fix: only a persona that used the app before and then stopped counts as lost.
- **Model arithmetic drifted balances.** Fix: the engine derives balance and 30-day activity from the
  model's reported money move and actions; the model never edits numbers.
- **Decision text leaking** through personas quoting it to friends outside the target. Fix: the
  router blocks quotes of the bank message.
- **Two engines in parallel.** We merged the two-round engine with our personas, metrics and tools;
  earlier experiment rows are kept but marked as not comparable.
- **Personas forgot.** A declined card in week 6 was "everything back to normal" in week 7. Fix: the
  "what went wrong since Nov 2" list in every week and in the end check-in.
- **Inertia from our prompt** (see the experiments): reason first, the two inertia lines removed, the
  history as stretches. Side effect: the model read money as "this week" and went back to "kept";
  money is now cumulative and such an answer is rejected.
- **Goals 3 and 3b could not fail:** even with every persona filing with the CFPB, goal 3b reached
  199.6. Fix: the 1% act share and the dossier's escalation rate. Ratings then came from the model
  rating its mood every week; requiring the review action made them vanish; the rating is now the
  persona's current opinion, counted at the app's prompting pace.
- **The world contradicted the announcements:** 16:00 instead of 16:10, failed instead of queued
  transfers, pay landing after a persona left or while P2 was sent home without pay, a holding
  statement telling all 24 about C1. All fixed so the facts a persona reads agree with the texts.
- **Invented events:** E6 disputed a charge that was never on his card. Fix: C1 bystanders learn that
  their own payments are all theirs.
- **Peer mechanics:** the weekly cap dropped 20% of group-chat and 14% of direct messages, and round
  two rejected a kept post without a new message (all its invalid answers). Fix: direct messages always
  arrive, cap three; a kept post needs no new message.
- **A test broke silently:** the offline end-to-end test failed after the money rule. Fix: the fake
  model follows the rule, and every change now runs that test before it is merged.

## Our own ideas

- **Commitments, not moods:** each persona has a concrete thing that must happen on the migration
  weekend, so the crisis bites in dollars and the model reacts to facts, not to an adjective.
- **Words versus reality:** an announcement's text and what actually happened are separate inputs, so
  the same message can be tested against an on-time and an overrun weekend.
- **Follow share:** a persona's move counts for only part of its audience, set by its traits.
- **Live interview:** `code/scripts/interview.py` lets the board question any persona about its own
  ten weeks, built only from that persona's logged record.
- **Grievances outlive memory:** the world recomputes what went wrong for each persona, so its
  history is a fact, not something the model has to remember.
- **Diagnose before tuning:** we re-asked logged prompts with one change at a time to find what made
  the model inert, and switched the network off to measure what it adds.
- **A rating is an opinion every week**, counted at the pace the app asks for ratings, so a single
  persona's mood does not swing the board number and the weekly curve shows the crisis.

## What we would do with more time

- More seeds per plan (five or more) and intervals instead of min–max.
- Add students; more personas per group so one saver does not decide goal 2.
- Calibrate f, the 1% act share and the prompted rating pace against real churn, CFPB and App Store
  data, and report goals with their sensitivity to them.
- Make round two weigh what a friend said (today it shows the persona its first answer and the model
  mostly keeps it), and check `heard_from` against what the persona actually received.
- Model channels (push, email, SMS, a CEO video) as different reach and credibility, support waits
  that grow with the number of callers, and personas with different 30-day activity.
- Test message wording variants, not only actions.
- Model rivals as agents instead of one fixed offer.
