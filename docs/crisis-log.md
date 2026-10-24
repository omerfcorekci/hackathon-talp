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
- everyone else learns in week 3 that their own card payments are all theirs (`unless` B5, not a
  grievance). Without it, with the less inert engine, E6 disputed and then complained about a charge
  that was never on his card (seed 2, plan and no-decision), and that complaint took goal_3b to 228.7;
- the week-4 update is an `update` on the same file: its text reaches personas by the same reach draw
  from week 4, so some keep the week-3 rumor without hearing the correction.

---

## C0 outcome: the switch ran about four hours late (announced week 7, 16:00)

**Announcement (verbatim, "Known crisis outcome, week 7, 16:00"):** The core banking switch ended on Sunday, December 13 at 16:10 Central Time, about four hours late. Card payments kept working offline. Transfers queued on Saturday went through by Sunday night.

**Our reading:** a moderate overrun. The harm is concrete for anyone whose weekend commitment needed the
system back by Sunday noon: an autopay or payout due on Sunday now lands at 16:00, past some payees'
cutoffs. Offline card payments and queued transfers limit the damage. Customers who were told
"some hours" got roughly what was promised.

**Simulation input:** it is the outcome of the known crisis, so it sits in `code/config/world.json` and
is in all five runs, `plan_nosurprises` included: `migration.overrun_hours` = 4 (the engine states
each persona's weekend facts with the system back at Sunday 16:00) and a week-7 calendar event with the
text word for word.

---

## C2: Government shutdown (announced week 7, 16:00)

**Announcement (verbatim):** **Government shutdown.** Overnight, Congress missed its funding deadline, and parts of the federal government shut down. Some federal workers have been sent home; others, such as air traffic controllers and TSA officers, must keep working without pay. Nobody knows how long it will last.

Known: Social Security payments and the Postal Service continue.
Not known: how long it will last; when federal workers will be paid; which services will slow down.

Some of Cobalt's paycheck customers work for the federal government or its contractors. Their next federal paycheck is due on December 30.

**Update (week 8, 16:30, id `6f2c7320517cab2de1e34c9df9b857b2`, verbatim):** The Senate passed a short-term funding bill; the House plans to vote after Christmas. Federal workers have been told they will get back pay once the government reopens. Their December 30 paycheck may be missed.

**What is known / unknown:** a shutdown of unknown length; federal and contractor pay at risk; the next
federal paycheck is Dec 30 (week 9). Unknown: how many Cobalt customers, how long, back pay.

**Our reading:**
- Size: federal civilians and contractors are a few percent of US workers, so roughly 10–15k of
  Cobalt's 310k paycheck customers. Small for the bank, severe for them: paycheck-to-paycheck people
  with rent and Christmas bills and no pay date.
- How people act: they cut spending, look for short-term credit, ask the bank for help; anger turns
  on the bank only if it charges fees or says nothing. Everyone else mostly hears it as news.
- Earliest answer: a decision in **week 8 (lock before 16:30)**. Matching menu item: the zero-interest
  advance up to $500 (≤ 20k customers, $0.4M), which fits the group's size.
- After the week-8 update: an end is in sight (Senate passed, House votes after Christmas) and federal
  workers are promised back pay, but the Dec 30 paycheck may still be missed. So the gap is a timing
  gap, not lost income: exactly what a zero-interest advance bridges. The update arrives with our
  decision 2 (week 8, locked 16:30), which stays true: it says only that we cannot say how long the
  shutdown lasts. Back pay is promised to federal workers, not contractors; contractor pay for paused
  work is often not made up, so contractors like P2 stay the hardest hit. The earliest decision that
  could answer the update is week 9, but both decisions are locked.

**Simulation input:** `code/config/surprises/c2_week7_government_shutdown.json`, text word for word,
reaching personas by the seeded reach draw. None of our 24 personas is a federal worker; `effects`
make one of them hit: P2 Marcus Bell (HVAC technician at a contractor, paycheck to paycheck) is sent
home without pay from federal jobs in week 7, marked as something that went wrong. P2 stands for
55,000 customers, about four times our estimate of those affected; the follow share brings his
weight in the metrics closer. His pay weeks 8 and 10 (Dec 25, Jan 8) then read "no pay landed" instead
of his usual paycheck (`pay_paused` from week 8; no end week, since nobody knows how long the shutdown
lasts). The week-8 update is an `update` on the same file, text word for word, reaching personas by
the same reach draw from week 8. It carries no effects: the back pay is promised to federal workers,
not to contractors, and P2's pay stays paused, since the House vote and the reopening date are still
unknown. With surprises off, the texts and the effects vanish.

