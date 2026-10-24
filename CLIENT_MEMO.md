# Cobalt Bank: memo to the board

_One page. Written for the board, not for engineers. Numbers marked ⟨…⟩ are filled from the five
official runs at 17:30._

## What we decided and why

_The exact wording is in `code/config/decisions/plan.json`. Decision 2 is not locked yet._

1. **Week 5 (Nov 30), everyone: answer the card charges with the facts.** Security pack (free new
   card on request + an alert on every card payment, $0.3M), instant dispute credit up to $100 per
   customer for 8 weeks ($0.4M), +50 support staff for 4 weeks ($0.25M); push, email and in-app.
   **Cost: $0.95M.** Locked at 15:00. Why: the week-4 facts (a processor fault that charged some
   payments twice on Nov 16–17, fraud test charges on cards stolen elsewhere, Cobalt not breached,
   about 9,000 customers) are far smaller than the "Cobalt got hacked" rumor, but many customers only
   heard the rumor. The message repeats only what the processor confirmed, promises nothing about
   refunds, and gives every customer a concrete way to protect themselves before the migration.
2. **Week 8 (Dec 21): held back on purpose.** ⟨Target, actions, cost.⟩ The simulation found no
   step before the migration that moves a board goal, so we keep our second decision to answer what
   the migration and the week-7 announcement actually show. It will be locked for week 8, before
   16:30 on the day.

**Total cost: $0.95M + ⟨decision 2⟩ of $4.0M.** Inside the menu and the red lines: no misleading
statement, the date does not move, no layoffs, no product closed.

## What the simulation says

24 customers built as AI personas (paycheck customers, savers with large balances, small businesses
with a card reader, everyday customers), each standing for a share of the 2.1M customers, lived the
ten weeks twice with our plan and twice without it.

| Board goal (Jan 10) | Target | With our plan | Without decisions |
|---|---|---|---|
| Active customers | ≥ 98% | ⟨…⟩ | ⟨…⟩ |
| Deposits | ≥ 97% | ⟨…⟩ | ⟨…⟩ |
| App Store rating | ≥ 4.3 | ⟨…⟩ | ⟨…⟩ |
| CFPB complaints / month | ≤ 240 | ⟨…⟩ | ⟨…⟩ |

What we see so far (real model, two seeds per option, card charges on, decision 1 in place; read it
as direction, not size):
- An on-time migration with an honest notice is mild: ratings and complaints barely move, and the
  card charges at their real scale barely move them either.
- **Deposits are the goal at risk**, and they hinge on one large saver whose worry is the FDIC
  limit, not the rate. A rate boost (balances up to $50k) does not answer that, and no option we
  tested, in any week, reliably beat doing nothing on deposits.
- That saver keeps saying he will move "after the holidays", so the deposit risk lands just after
  January 10.
- In an earlier single-seed test, a reassuring message that reality then contradicted (an overrun)
  made things worse than saying nothing.

## What it cannot tell

- **Size.** 24 personas and two seeds show direction, not precise percentages; one large saver's
  choice moves deposits by about a point.
- **How long the switch overruns.** We tested on time and an 8-hour overrun; the real overrun is
  unknown.
- **Who exactly was hit by the charges.** The bank says about 9,000 customers; we give one of our
  24 personas a double charge; the rest hear of it, if at all, through social media and our messages.
- **Rivals' real moves** and press coverage beyond one rate offer.
- The rating and complaint numbers rest on our conversion assumptions, not on Cobalt's history.

## What Cobalt should watch next

- Week-by-week deposit outflows from customers above $50k, and rival rate moves before Dec 12.
- Card disputes and support waits after the charges scare; a spike is the earliest sign of CFPB risk.
- The migration clock on Dec 13: if it runs past 12:00, update customers every few hours with facts.
- App Store reviews mentioning "hacked" or "frozen" in the week after the switch.
