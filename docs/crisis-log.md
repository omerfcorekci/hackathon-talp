# Crisis log

One entry per crisis: the known one from the dossier, and every dashboard announcement (and its
update) as it arrives. Copy the announcement text word for word, then write how we read it. This
feeds the "how we read each crisis" section of `TEAM_DOC.md`.

A crisis announced at the start of week N is already happening in week N; the earliest decision that
can answer it is in week N+1.

Template:

```
## C<n>: <short name> (announced week N, HH:MM)
**Announcement (verbatim):** ...
**Update (week N+1, verbatim):** ...
**What is known / unknown:** ...
**Our reading:** size, who hears about it, how people feel, what they do, which groups are hit
**Simulation input:** file in code/config/surprises/ with the verbatim text, plus `effects` = our reading
of what really happened (`migration_overrun_hours`, `support_wait_by_week`, per-week `experience` lines
with an optional persona condition). Who hears the text is decided by the engine's reach rules.
```

---

## C0: Core banking migration (known, week 6)

**Dashboard reminder (15:30, id `31babc699d2107749b3810e55662bd60`):** "Known crisis reminder — already
included in your company dossier. Include this event in every simulation run, including
plan_nosurprises." The text repeats the dossier facts below word for word. It is not a surprise, so it
has no file in `code/config/surprises/` (that folder is switched off in `plan_nosurprises`); the
migration lives in `code/config/world.json` and is in all five runs. Checked at 15:31 with a fake
`plan_nosurprises` run: the week-5/6 prompts carry the date, the read-only app, the $100 offline limit,
the Friday Dec 11 payday and the rival offer, and no C1 text.

**From the dossier:** Saturday, December 12, 00:00 to Sunday, December 13, 12:00 (Central Time).
- For 36 hours the app is read-only: balances visible, no transfers, no peer-to-peer payments, no new cards.
- Card payments work offline up to $100 per payment.
- If something goes wrong, the switch can run "some hours" longer; nobody can say how many.
- Many customers are paid on Friday, December 11, the day before.
- Rivals know the date too.
- Business as usual: migration email notice 7 days before.

**Our reading:**
- Size: 36 hours of a read-only app is an inconvenience for most people, but it is concrete harm for
  anyone with money that must move that weekend: rent or bill autopays, a weekend purchase above the
  $100 offline limit, P2P payments to family, card-reader sales for small businesses.
- Timing: paycheck customers are paid on Fri Dec 11 and cannot move that money on Saturday. Rivals know
  the date, so rate offers aimed at "switch before December 12" are likely in week 5.
- Who is hit: paycheck-to-paycheck customers (autopay timing, late fees), small business owners (sales
  over $100 and payouts), savers above the FDIC limit (rumor-driven moves, rival rates). Students and
  everyday customers mostly feel the P2P freeze.
- How people react: on-time completion with an honest notice is mild; an overrun turns "some hours"
  into missed payments, angry posts, low ratings and complaints. The risk is the gap between what we
  promised and what happened, not the freeze itself.
- Earliest answer: a decision in week 5 (lock before 15:00) reaches people before the weekend; week 7
  is the first week to answer what actually happened.

**Simulation input:** `code/config/world.json`: `migration` (window, `overrun_hours` = 0, offline limit
$100), the week-6 calendar event, the business-as-usual email in week 5 and social statement in week 6
(`bau_notices`), support waits of 25 minutes in week 6 and 12 in week 7 (`support_wait.by_week`) and a
rival rate offer in week 5 (`rival_offers`). Each persona has its own weekend commitment
(`migration_weekend` in `personas.jsonl`); the engine states what the window did to it (paid late, card
declined above the limit, autopay delayed) and the model reacts. An overrun is tested by setting
`overrun_hours` or by an announcement carrying `migration_overrun_hours`.

---

## C1: Small charges nobody recognizes (announced week 3, 14:00)

**Announcement (verbatim):** **Small charges nobody recognizes.** Since Monday, some customers have seen small card charges they do not recognize, mostly between $0.50 and $5. Screenshots are on X and Reddit; one post with many shares says "Cobalt got hacked".

Known: the charges are real; the security team is investigating with the card processor.
Not known: how many customers; what caused it; whether customer data was exposed.

**Update (week 4, 14:30, verbatim):** The card processor confirmed a fault that charged some payments twice on November 16 and 17. Separately, a small number of cards were used for test charges of $0.50 to $2 by fraudsters, a common pattern after card numbers are stolen elsewhere, for example on a fake shopping site. Cobalt's own systems were not breached. About 9,000 customers were affected in total.

**What is known / unknown:** week 3: charges are real and small ($0.50–$5); cause, scale and data
exposure unknown; a viral "Cobalt got hacked" post is already out. Week 4: two causes (a processor
fault that double-charged on Nov 16–17, and fraud test charges on cards stolen elsewhere), Cobalt not
breached, about 9,000 customers affected (0.4% of 2.1M). Still unknown: whether duplicates are already
refunded, and whether the stolen cards get replaced.

**Our reading:**
- Size: small money per customer, big trust hit. The rumor ("hacked") is worse than the facts, and it
  lands three weeks before a migration that freezes the app, so the two can merge into "Cobalt is
  broken".
- Who hears: everyone who uses X, Reddit or TikTok first, then family chats; customers who check the
  app daily find charges themselves.
- How people feel and act: past fraud/phishing victims and anxious customers check statements, call
  support, dispute charges (top complaint type already) and ask for a new card; some move money "to be
  safe". Disputes and CFPB complaints are the main risk (goal 3b), plus App Store reviews.
- Groups hit: everyday customers (many small card payments, social media), small businesses (card
  readers, fear for their customers' cards), paycheck customers who live close to zero; savers less on
  money, more on trust.
- Earliest answer: a decision in **week 4** (lock before 14:30). Matching menu items: Security pack
  (free new card + alert on every card payment), Instant dispute credit, Extra support staff.
- After the week-4 update: the facts are far smaller than the rumor. The risk shifts from "hacked" to
  "will they fix my double charge": people who were hit and those who heard the rumor but not the
  correction. "Not breached" and "about 9,000" calm many; "cards stolen elsewhere" still worries
  fraud-wary customers before the freeze. The earliest decision is now week 5 (lock before 15:00), and
  any message must use the new facts: saying the cause is unknown would now be misleading.

**Simulation input:** `code/config/surprises/c1_week3_unrecognized_charges.json`, text word for word.
Who hears the text is the engine's seeded reach draw (app-daily users, social-media users, others).
`effects` hold our reading of what really happened, and vanish in `plan_nosurprises`:
- no holding statement of our own: the engine's business-as-usual holding statement on social media
  reaches the personas who hear the announcement in week 3, by the same reach draw. An earlier version
  of this file put a holding statement into every persona's week-3 experience, which told all 24 about
  the charges although the reach draw had only 15 of them hearing about it (seed 1);
- support waits of 9 minutes in week 3 and 7 in week 4 (dispute calls; BAU is 4);
- one persona finds a charge himself in week 3: B5 Diego Alvarez, a $4.50 payment on his business
  card shows up twice, and a market customer asks whether his card reader is safe. Before the update we
  had three (P5, E4, B5), but together they stand for about 307,000 customers; the update says about
  9,000 were hit, so we kept only B5 (7,000 customers);
- the week-4 update is an `update` on the same file: its text reaches personas by the same reach draw
  from week 4, so some keep the week-3 rumor without hearing the correction.

