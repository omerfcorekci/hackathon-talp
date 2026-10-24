# Persona briefs — v0, for approval

24 personas, 4 groups × 6. Short briefs only; the detailed narratives, attribute values and network
edges are generated after approval.

## Groups used and why

| Group (dossier wording) | Why it is in | Weight budget |
|---|---|---|
| `paycheck customers` | The known crisis hits them hardest: paid Friday Dec 11, app read-only 36h from Saturday. Drives goal 1 (active) and the CFPB side of goal 3. | 310k customers · ~$0.74B |
| `savers with large balances` | They *are* goal 2: 5% of customers hold half of the $6.0B. Rate gap (−0.5pt) and FDIC awareness decide whether money moves. | 105k customers · ~$3.0B |
| `small business owners with a Cobalt card reader` | $100 offline limit and no instant transfers on a Saturday in peak season. Loud, review-writing, BBB/regulator-aware. | 42k customers · ~$0.25B |
| `everyday customers` | The bulk. Half of all customers were not active in the last 30 days, so this group carries the "second bank → dormant" risk for goal 1 and the App Store rating. | 1,643k customers · ~$2.0B |

**Left out: `students`.** Small balances (little leverage on goal 2), behavior mostly covered by the
younger everyday personas (P2P-heavy, TikTok, price conscious). First group to add with more time.
No student is labeled as another group; the 24 contain no students.

Totals: 2,100k customers, ≈ $6.0B deposits, top 5% (the savers group) holding ≈ $3.0B — matches the
dossier. Exact `weight_customers` / `weight_deposits` are fixed in the detailed step.

## Attributes every persona carries (the ones that couple to this crisis)

Cobalt role (main / second bank) · paycheck into Cobalt and payday · balance band and above-FDIC flag ·
knows the FDIC limit · number of banks · moves money for a better rate · checks app daily · uses P2P ·
past fraud/phishing · financial literacy · where they hear news · leads or follows opinion (sets the
intra-week wave) · how fast they get angry / patience / forgiveness · reaction to a bank SMS · one
"scar" (a past bad experience) · one fear for this quarter. Plus a narrative paragraph and 2–3
lifestyle details for realism.

---

## Paycheck customers (310k)

| id | Who | Cobalt role & crisis hooks | Info & influence | Weight |
|---|---|---|---|---|
| P1 | **Rosa Delgado**, 29, ER nurse, Phoenix AZ | Main and only bank. Biweekly, **paid Fri Dec 11**; rent autopays Sun Dec 13. Checks app daily. Patience low after night shifts. | Coworkers, family group chat. Follower. | 60k |
| P2 | **Marcus Bell**, 38, HVAC technician, Charlotte NC, two kids | Main bank for pay; mortgage at a credit union (second bank). **Paid Fri Dec 11.** Carries card debt; pays babysitter by P2P. Scar: a 45-day dispute last year. | Facebook, coworkers. Follower. Angry fast, forgives slowly. | 55k |
| P3 | **Jenna Kowalski**, 26, junior accountant, Minneapolis MN | Main bank. Paid semi-monthly (Nov 30 / Dec 15, **not** Dec 11). High financial literacy, knows FDIC, compares rates weekly, already has a rival HYSA. | Reddit r/personalfinance, podcasts. **Leader.** | 50k |
| P4 | **Samuel Okafor**, 45, city bus operator, Houston TX | Main bank 5 years; left a big bank after a fee dispute (scar). **Paid Fri Dec 11.** Union member, values stability, trusts institutions. | Local TV news, union group. Follower. Patient. | 55k |
| P5 | **Ashley Nguyen**, 31, retail store manager, Seattle WA | Main bank. **Paid Fri Dec 11**, Christmas budget tight, lives paycheck to paycheck, high baseline anxiety. Uses P2P with sister. | TikTok, sister. Follower, easily swayed. | 50k |
| P6 | **Greg Halvorsen**, 57, insurance claims adjuster, Des Moines IA | Main bank. Paid monthly on the 1st (not Dec 11). Dislikes change, reads every bank email, calls phone support, **would file a CFPB complaint** if wronged. | Cable news, email. Neither; acts alone. | 40k |

## Savers with large balances (105k · ≈ $3.0B)

| id | Who | Cobalt role & crisis hooks | Info & influence | Weight |
|---|---|---|---|---|
| S1 | **Victor Haines**, 61, retired orthodontist, Naples FL | Second bank. **$350k at Cobalt, above the FDIC limit and knows it.** Three banks + brokerage. Moves money for rates. Trusts big institutions over fintechs. | Financial newsletters, his advisor. Leader in his circle. | 1,000 · $350M |
| S2 | **Elaine Park**, 44, product manager, San Jose CA | Second bank (HYSA). **$150k** bonus + emergency fund. Compares HYSA rates monthly, FDIC aware, has a rival HYSA already. | X/LinkedIn, coworkers. Leader. Decides fast. | 2,500 · $375M |
| S3 | **Robert Yancey**, 55, owns two rental properties, Nashville TN | Main bank for the app. **$55k** operating reserve. Not FDIC aware. Moderately price conscious. Needs transfers to pay contractors. | Local news, neighbors. Follower. | 10,000 · $550M |
| S4 | **Dana Whitfield**, 36, attorney, Chicago IL | Main bank. **$30k** house down payment, buying in spring, needs liquidity. Anxious about access; high need for control. | Reddit, friends. Follower but vocal when wronged. | 20,000 · $600M |
| S5 | **Hank Morrison**, 68, retired electrician, Tucson AZ | Second bank (pension to a big bank). **$20k**. Low tech comfort, calls phone support, trusts people over brands, loyal once trusted. | Local TV, neighbors, his daughter. Follower. | 30,000 · $600M |
| S6 | **Chloe Bennett**, 33, software engineer, Austin TX | Main bank. **$13k** travel fund. Moves money for a 0.5pt difference, posts on Reddit, dark mode, uses spending charts. | Reddit, YouTube. **Leader online.** | 41,500 · $540M |

## Small business owners with a Cobalt card reader (42k)

| id | Who | Cobalt role & crisis hooks | Info & influence | Weight |
|---|---|---|---|---|
| B1 | **Tomás Herrera**, 39, three food trucks, El Paso TX | Main bank. Avg ticket $12 (under the $100 offline limit). **Saturday night is his biggest shift**; needs Sunday transfers to restock. | Instagram, other vendors. Leader among vendors. | 7k |
| B2 | **Beth Caldwell**, 48, yarn & craft shop, Burlington VT | Main bank. Avg ticket $45. **Holiday season = 40% of annual sales**; Dec 12 is a peak Saturday. Writes reviews. | Facebook groups, local paper. Follower. Patient. | 7k |
| B3 | **Jamal Reed**, 33, mobile auto detailing, Detroit MI | Main bank. **Tickets $150–$400, above the $100 offline limit.** Pays suppliers by instant transfer. Angry fast, posts publicly. | X, YouTube. Leader. | 7k |
| B4 | **Karen Lindqvist**, 56, hair salon with 4 chairs, Duluth MN | Main bank. **Pays stylists by P2P every Sunday morning** — blocked Dec 13. Loyal, forgiving, but tells everyone. | Her stylists, Facebook. Leader locally. | 7k |
| B5 | **Diego Alvarez**, 29, farmers-market coffee stand, Miami FL | Main and only bank. Low cash reserve, every weekend matters. Price conscious; uses the free P2P a lot. | Instagram, market vendors. Follower. | 7k |
| B6 | **Patricia Osei**, 51, home health care agency (12 staff), Baltimore MD | Main bank. **Pays staff by instant transfer on Fridays**, incl. Dec 11. Trusts institutions; member of the local business association; BBB-aware, would complain formally. | Business association, email. Leader. | 7k |

## Everyday customers (1,643k)

| id | Who | Cobalt role & crisis hooks | Info & influence | Weight |
|---|---|---|---|---|
| E1 | **Maya Thompson**, 27, UX designer, Denver CO | Main bank. Checks app daily, uses spending charts. Weekend trip planned Dec 12. Moderately price conscious. | Instagram, Reddit, friend group. Leader. | 400k |
| E2 | **Derek Lawson**, 34, warehouse shift lead, Columbus OH | **Second bank** (main is a big bank): Cobalt debit card + P2P only, opens the app twice a month. Starts closest to "dormant". | Coworkers, Facebook. Follower. | 350k |
| E3 | **Priya Raman**, 41, dental hygienist, Sacramento CA, two kids | Main bank. Values security. **Card fraud victim two years ago, dispute dragged on (scar).** Checks app weekly. Not FDIC aware. | Family group chat, local news. Follower. Slow to forgive. | 300k |
| E4 | **Tyler Brooks**, 23, barista + gig delivery, Atlanta GA | Main and only bank. **Heavy P2P** (rent split with roommates). Low financial literacy, FOMO, angry fast, forgets fast. | TikTok, roommates. Follower, easily swayed. | 250k |
| E5 | **Linda Garza**, 52, school administrative assistant, San Antonio TX | Main bank 4 years. Brand loyal, forgiving, reads emails, fears fees more than outages. Dark mode, same ATM every week. | Email, local TV, sister. Follower. | 200k |
| E6 | **Owen Fitzgerald**, 30, freelance videographer, Portland OR | Main bank; savings at a rival online bank. Irregular income, moves money for rates, price conscious. | Reddit personal finance, YouTube. **Leader online.** | 143k |

## Network sketch (built in the detailed step)

- k≈4 in-group edges + 1 cross-group edge each; leaders have 2 extra followers.
- Bridges: Jenna (P3) ↔ Chloe (S6) ↔ Owen (E6) on Reddit; Tomás (B1) ↔ Diego (B5) on Instagram;
  Rosa (P1) ↔ Ashley (P5) ↔ Tyler (E4) family/TikTok; Victor (S1) ↔ Hank (S5) retirees.
- Waves: leaders (P3, S1, S2, S6, B1, B3, B4, B6, E1, E6) → middle → followers.

## Where each number comes from

- Group sizes and deposits: dossier (310k paycheck, 42k card readers, 5% hold half of $6.0B).
- Ages 22–40 for most, with older savers/retirees: dossier ("mostly 22 to 40") plus the natural
  skew of large balances to older customers (ACS household wealth by age; stated as an assumption).
- Cities: spread across states and city/suburb/small town as the dossier describes; no sensitive
  traits used.
