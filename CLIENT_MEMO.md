# Cobalt Bank: memo to the board

_One page. Written for the board, not for engineers. Numbers marked ⟨…⟩ are filled from the five
official runs at 17:30._

## What we decided and why

_Draft until both decisions are locked on the dashboard; the exact wording is in
`code/config/decisions/plan.json`._

1. **Week ⟨4⟩ — ⟨answer the unrecognized charges⟩.** ⟨Actions, target, cost.⟩ Why: the charges are
   small, but "Cobalt got hacked" lands three weeks before a weekend when the app is read-only. Say
   what we know and what we don't, and give every customer a concrete way to protect themselves.
2. **Week ⟨5⟩ — ⟨tell everyone plainly what the migration weekend means⟩.** ⟨Actions, target, cost.⟩
   Why: people are paid on Friday and frozen on Saturday; the harm is in payments that must happen
   that weekend, not in the freeze itself.

**Total cost: ⟨$x.xM⟩ of $4.0M.** Inside the menu and the red lines: no misleading statement, the date
does not move, no layoffs, no product closed.

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

What we saw so far (before the week-3 charges):
- An on-time migration with an honest notice is survivable: ratings and complaints barely move.
- **Deposits are the goal at risk**, and they move through a few large savers who chase rates; a
  rival offers more just before the weekend.
- A reassuring message that reality later contradicts makes things worse than saying nothing.

## What it cannot tell

- **Size.** 24 personas and two seeds show direction, not precise percentages; one large saver's
  choice moves deposits by about a point.
- **How long the switch overruns.** We tested on time and an 8-hour overrun; the real overrun is
  unknown.
- **How many customers were hit by the charges**, and whether data was exposed: unknown to the bank,
  so unknown to us. We assumed a handful.
- **Rivals' real moves** and press coverage beyond one rate offer.
- The rating and complaint numbers rest on our conversion assumptions, not on Cobalt's history.

## What Cobalt should watch next

- Week-by-week deposit outflows from customers above $50k, and rival rate moves before Dec 12.
- Card disputes and support waits after the charges scare; a spike is the earliest sign of CFPB risk.
- The migration clock on Dec 13: if it runs past 12:00, update customers every few hours with facts.
- App Store reviews mentioning "hacked" or "frozen" in the week after the switch.
