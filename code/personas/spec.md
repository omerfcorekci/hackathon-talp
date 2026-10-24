# Persona specification

How the 24 personas in `personas.jsonl` were built, which attributes they carry and why, how they are
weighted, and how they are connected. `generate.py` produces the file deterministically (seed 7);
the short briefs that were approved first are in `personas-brief.md`.

## 1. Groups

Four of the five dossier groups, six personas each (dossier rule: ≥24 personas, ≥3 groups, ≥4 each).

| `group` (dossier wording) | Personas | Why |
|---|---|---|
| `paycheck customers` | P1–P6 | The known crisis lands on them: paid Friday Dec 11, app read-only from Saturday 00:00 |
| `savers with large balances` | S1–S6 | They are goal 2: the top 5% hold half of $6.0B; rate gap and FDIC awareness decide whether money moves |
| `small business owners with a Cobalt card reader` | B1–B6 | $100 offline limit, no instant transfers on a peak-season Saturday; loud, review-writing, regulator-aware |
| `everyday customers` | E1–E6 | The bulk; half of all customers were not active in the last 30 days, so "second bank → dormant" lives here |

`students` is left out: small balances (no leverage on goal 2), behavior largely covered by the young
everyday personas. It is the first group to add with more time. No student is relabeled as another
group.

## 2. Weights: how many real customers each persona stands for

Two weights per persona, both integers:

- `weight_customers` — customers this persona represents. Group totals come straight from the dossier:
  310,000 paycheck · 42,000 card readers · 105,000 savers (= the 5% that hold half the deposits) ·
  1,643,000 everyday (the remainder of 2.1M).
- `weight_deposits_usd` = `weight_customers × balance_usd`, the deposits this persona stands for.
  Savers sum to ≈ $3.0B (dossier: half of $6.0B in 5% of customers); everyone else to ≈ $3.0B.

Within a group, weights are uneven on purpose: Victor (S1, $350k balance) represents 1,000 customers,
Chloe (S6, $13k) represents 41,500; Maya (E1, daily user) represents 400k, Derek (E2, twice-a-month
user) 350k. This keeps the deposit distribution heavy-tailed, as the dossier describes.

Metrics use the weights: goal 1 counts `weight_customers` of personas whose status is `main bank` or
`second bank` and who were active; goal 2 sums `weight_deposits_usd × money factor`.

## 3. Attributes used, and why

Catalog letters refer to `brief/03-audience-attributes.md`; "sector" means the dossier's extra list.

**Couple directly to the known crisis (always filled, and the prompt leans on them)**
- sector: `paycheck_into_cobalt`, `payday` (whether the next pay lands Fri Dec 11), `balance_band`,
  `above_fdic_limit`, `knows_fdic_limit`, `banks_count`, `cobalt_role` (main / second bank),
  `moves_money_for_rate`, `checks_app_daily`, `uses_p2p`, `fraud_victim`, `financial_literacy`,
  `reaction_to_bank_sms`
- H (what they can do): all personas share the same action menu; who actually does what is the LLM's call

**Shape how information reaches them (drive the network and the intra-week waves)**
- F: `news_sources`, `circle_size`, `influence` (leader / follower / independent), `sways_easily`,
  `checks_rumors`, `asks_before_deciding`

**Shape the reaction (temperament)**
- C: `values_most`, `risk_attitude`, `trust_in_institutions`, `price_consciousness`, `brand_loyalty`,
  `need_for_control`
- E: `baseline_anxiety`, `anger_speed`, `patience`, `forgiveness`, `embarrassed_to_complain`
- G: `credit_card_debt`, `student_loans`, `lives_paycheck_to_paycheck`, `worried_about_prices`

**Give the persona a life (fight homogenization; make the live Q&A credible)**
- A: age, gender, city/state, area type, household, occupation, employer type, employment,
  income band, owns/rents
- B: `years_customer`, `why_cobalt`, `scar` (one past bad experience), `recent_life_event`,
  `fear_this_quarter`
- I (lifestyle): 2–3 details each (phone, coffee, pet, hobby, card design, dark mode, usual ATM)

**Left out, and why**
- Catalog I items beyond 2–3 per persona (zodiac, shoe size…): add words, not behavior.
- Sensitive traits (race/ethnicity, religion, health, politics, immigration): not in the catalog, not
  needed by the client's question, excluded.
- `environmental_concern`, `served_in_military`, `first_in_family_to_college`: no mechanism links
  them to a bank migration or a rate decision.

## 4. Distributions and where they come from

- **Age:** most 23–45 (dossier: "mostly 22 to 40"); savers skew older (36–68) because large balances
  concentrate in older households (ACS / SCF pattern, stated as an assumption, not fitted).
- **Place:** 20 states, mix of city / suburb / small town as the dossier describes; no region
  dominates.
- **Payday:** 4 of 6 paycheck personas are paid Fri Dec 11 (dossier: "many customers are paid on
  Friday, December 11"); 2 are not, so the sim can show the difference.
- **Cobalt role:** 20 main bank, 4 second bank (S1, S2, S5, E2). The dossier says most customers also
  have a big-bank account; `banks_count` ≥ 2 for 19 of 24, but Cobalt is still "main" where pay or
  daily spending runs through it.
- **Activity:** two everyday personas (E2, E4-style low engagement) start near dormant, reflecting
  that only 1.0M of 2.1M were active in the last 30 days.
- **FDIC awareness:** 8 of 24 know the limit; only S1 is above it. Both bank-run papers in
  `docs/prior-art.md` find insured-vs-uninsured the biggest behavioral split, so this is explicit.
- **Influence:** 10 leaders, 6 independents, 8 easily-swayed followers (sets the waves below).
- **Scars:** 8 of 24 carry a past bad experience with Cobalt or a rival (disputes, fees, fraud);
  the rest have none, so trust does not start uniformly low.

Nothing here is fitted to data we do not have; every distribution is a stated choice.

## 5. Network and waves

- `neighbors`: 3 seeded in-group edges per persona plus the explicit cross-group bridges below;
  leaders get up to 2 extra followers (skipping anyone already at 7). Undirected; 4–8 neighbors each. Identical in every run (it is
  inside `personas.jsonl`).
- Bridges (from the briefs): Jenna P3 – Chloe S6 – Owen E6 (Reddit personal finance); Tomás B1 –
  Diego B5 (Instagram, market vendors); Rosa P1 – Ashley P5 – Tyler E4 (family / TikTok); Victor S1 –
  Hank S5 (retirees); Patricia B6 – Samuel P4 (local association); Elaine S2 – Maya E1 (tech
  coworkers); Marcus P2 – Jamal B3 (trade contacts); Dana S4 – Priya E3 (parents' group).
- `wave` orders the week: wave 1 = leaders (post first), wave 2 = independents, wave 3 = easily
  swayed. A persona sees neighbors' posts from earlier waves of the same week and from last week.
  Posts are the persona's own words, ≤140 chars; the bank's message is never quoted.

## 6. What the file does not contain

No weekly state, no memory, no run-specific data — those live in each run's `weekly.jsonl`. The
persona file is the same in all five runs, as the checker requires.
