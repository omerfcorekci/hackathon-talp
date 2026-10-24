# Decision 1: what to lock, why, and how (lock before 15:00)

## 1. What to choose

**Lock now: decision 1 only, week 5, the card-charges answer (D1).** Keep decision 2 open.

| | Decision 1 (now) | Decision 2 (later) |
|---|---|---|
| Week | 5 (lock before **15:00**) | 6 (before 15:30) or 7+ (before 16:00) |
| Actions | Security pack + Instant dispute credit | open |
| Cost | $0.7M | up to $3.3M left |

**Choose by these rules, in this order:**
1. **Inside the red lines.** The message says only what the week-4 update confirmed. Saying "we don't
   know the cause" would now be misleading; promising refunds would claim something not confirmed.
2. **Answer the crisis that is happening.** The charges (week 3–4) hit trust three weeks before the app
   freezes. Instant dispute credit and payment alerts give every customer a concrete step today.
3. **Cheapest plan that is as good as the others.** The budget is a ceiling, not a target. The CEO asked
   not to buy loyalty with money we don't have, and the simulation showed no gain from the dearer plans.
4. **Keep one decision for what we don't know yet.** A migration overrun or a new surprise can arrive;
   decision 2 is our only answer to it.

## 2. Why the simulation says this

Real model (gemini-3.5-flash-lite), 24 personas, 10 weeks, the week-3 charges and their week-4 update
on, two seeds per plan. Sweep `c1_plans` (viewer: Karar önerisi → c1_plans).

| Plan | Active ≥98 | Deposits ≥97 | Rating ≥4.3 | CFPB ≤240 | Cost |
|---|---|---|---|---|---|
| D: charges + migration notice | 99.97 ✓ | 96.98 ✗ | 4.60 ✓ | 120 ✓ | $1.05M |
| E: D + new-money rate boost | 97.34 ✗* | 97.42 ✓ (96.98–97.86) | 4.60 ✓ | 120 ✓ | $1.85M |
| B: early pay + rate boost | 99.97 ✓ | 96.98 ✗ | 4.60 ✓ | 120 ✓ | $2.10M |
| No decision | 99.95 ✓ | 96.98 ✗ | 4.60 ✓ | 120 ✓ | $0 |

- **Deposits hinge on one saver.** S1 Victor holds $350k, above the FDIC limit. In the migration week
  he moves some money "to stay under the FDIC limit". A rate boost applies to balances up to $50k, so
  it does not touch his reason. In E's seed 1 he kept his money, but his own words name his advisor, not
  the rate; in seed 2 he moved as in every other plan.
- \* **E's drop in active customers is a metric artifact.** E2 says "everything works fine" but logged
  no app action in weeks 9–10, so the metric counts him as lost; he stands for 350,000 customers.
- **The charges barely move ratings or complaints** at the real scale (about 9,000 customers).
- **So no plan reliably beats doing nothing**, and the plans are equivalent within the seed spread.
  The viewer's rule (goals met → shortfall → cost; equivalent within noise → cheapest) picks D.
- **Not tested yet:** D1 alone (without D2). Run a short sweep before 15:30 to choose decision 2.

## 3. How to fill the dashboard form (decision 1)

**Effective week:** `Week 5 · Nov 30—Dec 6 · 15:00`

**Who is this for?:** `Everyone`

**Action 1:** `Security pack: a free new card on request and an alert for every card payment` — the
only level ($0.3M)

**+ Add action → Action 2:** `Instant dispute credit: credit disputed card charges at once, up to $100
per customer, for 8 weeks` — the only level ($0.4M)

**Exact customer message** (534 / 600):

```
Update on the card charges from Nov 16-17: our card processor confirmed a fault that charged some payments twice, and a small number of cards had fraud test charges of $0.50 to $2 after card numbers were stolen elsewhere, for example on a fake shopping site. Cobalt's own systems were not breached. About 9,000 customers were affected. Starting today, for 8 weeks: if you dispute a card charge, we credit up to $100 right away while we investigate. In the app you can turn on an alert for every card payment and order a free new card.
```

**Message channels:** ☑ Push · ☑ Email · ☑ In-app · ☐ Text message · ☐ CEO video

**Why?** (exactly three lines):

```
The week-4 facts are far smaller than the 'Cobalt got hacked' rumor, but many customers only heard the rumor.
Instant dispute credit and payment alerts give every customer a concrete way to protect themselves before the migration.
We repeat only what the processor confirmed and promise nothing about refunds we cannot yet confirm.
```

**Before you click lock:** the dashboard total should read **$0.7M**. If an action label reads
differently on the dashboard, note the exact wording: `plan.json` must hold the dashboard text.

## 4. After locking

1. Tell Claude the lock time and any wording that differs; it copies the locked decision word for word
   into `code/config/decisions/plan.json` and fills the lock table in `decisions-log.md`.
2. Before 15:30: sweep "D1 alone + decision 2 in week 6 / week 7 / none" to choose decision 2.

### Decision 2 options

| Option | Lock before | For | Against |
|---|---|---|---|
| Migration notice: $250 offline limit + support staff (D2, $0.35M), week 6 | 15:30 | The $250 limit only matters if it is in place for the Dec 12–13 weekend | Decided before we see how the migration goes |
| Answer to what happened, week 7+ | 16:00 or later | Responds to an overrun or a new surprise | The offline limit is gone; customers get only the BAU migration email |
