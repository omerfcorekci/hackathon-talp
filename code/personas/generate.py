#!/usr/bin/env python3
"""Generate personas.jsonl for the Cobalt Bank simulation.

    python3 code/personas/generate.py            # writes code/personas/personas.jsonl
    python3 code/personas/generate.py --check    # validate only

Deterministic (seed 7). The 24 personas are hand-written from the approved briefs; this script adds
weights, the social network and the intra-week wave, validates totals against the dossier, and writes
one JSON object per line. See spec.md for the reasoning.
"""
import argparse
import json
import random
from pathlib import Path

SEED = 7
OUT = Path(__file__).with_name("personas.jsonl")

# Dossier numbers (brief/10-cobalt-bank.md)
TOTAL_CUSTOMERS = 2_100_000
TOTAL_DEPOSITS = 6_000_000_000
GROUP_CUSTOMERS = {
    "paycheck customers": 310_000,
    "savers with large balances": 105_000,          # the 5% that hold half of the deposits
    "small business owners with a Cobalt card reader": 42_000,
    "everyday customers": 1_643_000,                # remainder
}

ACTIONS = ["log in and check balance", "try a transfer or P2P payment", "call or chat with support",
           "complain in the app", "post on social media", "tell friends or family",
           "post a review (App Store / Google / Trustpilot)", "file a complaint with the CFPB or BBB",
           "dispute a card charge", "move some money to another bank", "move most money to another bank",
           "move direct deposit to another bank", "open an account at a rival", "use Cobalt less",
           "wait and see", "recommend Cobalt", "do nothing"]


def P(**kw):
    return kw


PERSONAS = [
    # ---------------------------------------------------------------- paycheck customers (310k)
    P(id="P1", name="Rosa Delgado", group="paycheck customers", weight_customers=60_000, balance_usd=2_400,
      age=29, gender="woman", city="Phoenix", state="AZ", area="city", household="lives alone, one cat",
      occupation="emergency-room nurse", employer="private hospital", employment="full-time", income_band="$60k-80k",
      home="rents", years_customer=3, cobalt_role="main bank", only_bank=True, banks_count=1,
      paycheck_into_cobalt=True, payday="biweekly on Fridays; next: Fri Dec 11", paid_fri_dec11=True,
      balance_band="$1k-5k", above_fdic_limit=False, knows_fdic_limit=False, moves_money_for_rate=False,
      checks_app_daily=True, uses_p2p=True, uses_spending_charts=False, fraud_victim=False,
      financial_literacy="medium", credit_card_debt="$1,200", student_loans=True, lives_paycheck_to_paycheck=True,
      worried_about_prices=True, values_most="security", risk_attitude="cautious", trust_in_institutions="medium",
      price_consciousness="medium", brand_loyalty="medium", need_for_control="high",
      baseline_anxiety="medium", anger_speed="fast after night shifts", patience="low", forgiveness="medium",
      embarrassed_to_complain=False, news_sources=["coworkers", "family group chat", "Instagram"],
      circle_size="medium", influence="follower", sways_easily="medium", checks_rumors=False,
      asks_before_deciding="her mother", reaction_to_bank_sms="opens it immediately and assumes something is wrong",
      why_cobalt="no fees and a clean app when she moved to Phoenix for the job",
      scar="none with Cobalt; a big bank once charged her $35 overdraft on a $4 coffee",
      recent_life_event="switched to night shifts in October", fear_this_quarter="rent autopay bouncing on Sunday Dec 13 because her paycheck is stuck",
      lifestyle={"phone": "iPhone", "coffee": "cold brew, black", "card_design": "teal", "dark_mode": True},
      narrative="Rosa Delgado is a 29-year-old ER nurse in Phoenix who moved from Tucson three years ago and opened a Cobalt account because it had no fees and the app worked. Cobalt is her only bank: her paycheck lands every other Friday, rent autopays on the 13th, and she checks the balance every day, usually at 3 a.m. on a break. She is careful with money but not interested in it; she has $1,200 on a credit card and a student loan she pays on time. She hears about the world from coworkers and her family group chat and tends to believe what a trusted person tells her before she checks. After a run of night shifts she has no patience for things that do not work.",
      voice="I don't need the bank to be exciting. I need my paycheck where I can see it and my rent to go out on time."),

    P(id="P2", name="Marcus Bell", group="paycheck customers", weight_customers=55_000, balance_usd=1_800,
      age=38, gender="man", city="Charlotte", state="NC", area="suburb", household="married, two kids (6 and 9)",
      occupation="HVAC technician", employer="private contractor", employment="full-time", income_band="$60k-80k",
      home="owns (mortgage)", years_customer=4, cobalt_role="main bank", only_bank=False, banks_count=2,
      paycheck_into_cobalt=True, payday="biweekly on Fridays; next: Fri Dec 11", paid_fri_dec11=True,
      balance_band="$1k-5k", above_fdic_limit=False, knows_fdic_limit=False, moves_money_for_rate=False,
      checks_app_daily=False, uses_p2p=True, uses_spending_charts=False, fraud_victim=False,
      financial_literacy="medium-low", credit_card_debt="$6,500", student_loans=False, lives_paycheck_to_paycheck=True,
      worried_about_prices=True, values_most="family", risk_attitude="cautious", trust_in_institutions="low",
      price_consciousness="high", brand_loyalty="low", need_for_control="medium",
      baseline_anxiety="medium", anger_speed="fast", patience="low", forgiveness="slow",
      embarrassed_to_complain=False, news_sources=["Facebook", "coworkers", "local TV news"],
      circle_size="large", influence="follower", sways_easily="high", checks_rumors=False,
      asks_before_deciding="his wife", reaction_to_bank_sms="suspicious; thinks it might be a scam",
      why_cobalt="a coworker recommended it; the debit card and free P2P for paying the babysitter",
      scar="a $240 card dispute with Cobalt last year took the full 45 days and he had to call three times",
      recent_life_event="car repair bill in October went on the credit card", fear_this_quarter="Christmas on a credit card he already cannot pay down",
      lifestyle={"phone": "Android", "sports_team": "Panthers", "pet": "dog", "card_design": "black"},
      narrative="Marcus Bell, 38, fixes air conditioners around Charlotte and gets paid every other Friday into Cobalt, which a coworker talked him into four years ago. The mortgage runs through a credit union, so Cobalt is where the paycheck lands, the groceries get paid and the babysitter gets her P2P on Sunday nights. He carries $6,500 of card debt and feels it. Last year a $240 dispute took 45 days and three phone calls, and he has not forgotten it. He reads Facebook and listens to the guys at work; when someone he trusts says a bank is in trouble, he believes it first and checks later. He gets angry fast and forgives slowly.",
      voice="I'm not loyal to a logo. Whoever makes my paycheck show up and doesn't make me call three times, that's my bank."),

    P(id="P3", name="Jenna Kowalski", group="paycheck customers", weight_customers=50_000, balance_usd=3_800,
      age=26, gender="woman", city="Minneapolis", state="MN", area="city", household="lives with a roommate",
      occupation="junior accountant", employer="private firm", employment="full-time", income_band="$60k-80k",
      home="rents", years_customer=2, cobalt_role="main bank", only_bank=False, banks_count=3,
      paycheck_into_cobalt=True, payday="semi-monthly on the 15th and last day; Nov 30, Dec 15 (not Dec 11)", paid_fri_dec11=False,
      balance_band="$1k-5k", above_fdic_limit=False, knows_fdic_limit=True, moves_money_for_rate=True,
      checks_app_daily=True, uses_p2p=True, uses_spending_charts=True, fraud_victim=False,
      financial_literacy="high", credit_card_debt="$0 (pays in full)", student_loans=True, lives_paycheck_to_paycheck=False,
      worried_about_prices=False, values_most="saving", risk_attitude="calculated", trust_in_institutions="medium",
      price_consciousness="high", brand_loyalty="low", need_for_control="high",
      baseline_anxiety="low", anger_speed="slow", patience="medium", forgiveness="conditional",
      embarrassed_to_complain=False, news_sources=["Reddit r/personalfinance", "podcasts", "friends"],
      circle_size="medium", influence="leader", sways_easily="low", checks_rumors=True,
      asks_before_deciding="nobody; she reads the terms", reaction_to_bank_sms="reads it, then checks the app herself",
      why_cobalt="best checking app she tested; keeps most savings in a rival HYSA that pays 0.5 points more",
      scar="none", recent_life_event="passed the second CPA exam section in September", fear_this_quarter="nothing specific; she watches rates weekly",
      lifestyle={"phone": "iPhone", "coffee": "oat latte", "hobby": "cross-country skiing", "dark_mode": True},
      narrative="Jenna Kowalski is a 26-year-old junior accountant in Minneapolis who treats her banks like tools. Cobalt is her checking account because its app is the best she tested; most of her savings sit in a rival high-yield account that pays half a point more, and she knows the FDIC limit by heart. She is paid on the 15th and the last day of the month, so the Dec 11 payday wave does not touch her. She reads r/personalfinance, checks rumors before repeating them, and her friends ask her what to do with money. She is calm, pays her card in full, and leaves a bank the moment the math says so.",
      voice="A bank is a spreadsheet with an app. The day the numbers stop making sense, I move."),

    P(id="P4", name="Samuel Okafor", group="paycheck customers", weight_customers=55_000, balance_usd=3_200,
      age=45, gender="man", city="Houston", state="TX", area="suburb", household="married, one teenager",
      occupation="city bus operator", employer="local government", employment="full-time", income_band="$40k-60k",
      home="owns (mortgage)", years_customer=5, cobalt_role="main bank", only_bank=False, banks_count=2,
      paycheck_into_cobalt=True, payday="biweekly on Fridays; next: Fri Dec 11", paid_fri_dec11=True,
      balance_band="$1k-5k", above_fdic_limit=False, knows_fdic_limit=False, moves_money_for_rate=False,
      checks_app_daily=False, uses_p2p=False, uses_spending_charts=False, fraud_victim=False,
      financial_literacy="medium", credit_card_debt="$900", student_loans=False, lives_paycheck_to_paycheck=False,
      worried_about_prices=True, values_most="stability", risk_attitude="cautious", trust_in_institutions="high",
      price_consciousness="medium", brand_loyalty="high", need_for_control="low",
      baseline_anxiety="low", anger_speed="slow", patience="high", forgiveness="high",
      embarrassed_to_complain=True, news_sources=["local TV news", "union group chat", "his wife"],
      circle_size="medium", influence="independent", sways_easily="low", checks_rumors=True,
      asks_before_deciding="his wife", reaction_to_bank_sms="reads it carefully and does what it says",
      why_cobalt="left a big bank five years ago after a maintenance-fee dispute; Cobalt has never charged him a fee",
      scar="the big bank's fee dispute that pushed him to Cobalt",
      recent_life_event="daughter started driving in August", fear_this_quarter="nothing specific; he trusts the bank will handle the switch",
      lifestyle={"phone": "Android", "sports_team": "Astros", "usual_atm": "the grocery store on Bellaire", "card_design": "navy"},
      narrative="Samuel Okafor, 45, has driven a city bus in Houston for sixteen years and has banked with Cobalt for five, ever since a big bank charged him maintenance fees and would not explain why. His paycheck arrives every other Friday, including December 11. He does not check the app much; money comes in, bills go out, and his wife keeps the household spreadsheet. He trusts institutions, reads the bank's emails and does what they ask. He is slow to anger and quick to forgive, and he would rather wait a weekend than make a fuss. When something does go wrong he is embarrassed to complain and usually does not.",
      voice="They've treated me right for five years. One bad weekend doesn't undo that, as long as they tell me the truth."),

    P(id="P5", name="Ashley Nguyen", group="paycheck customers", weight_customers=50_000, balance_usd=900,
      age=31, gender="woman", city="Seattle", state="WA", area="city", household="lives with her partner",
      occupation="retail store manager", employer="private retail chain", employment="full-time", income_band="$40k-60k",
      home="rents", years_customer=2, cobalt_role="main bank", only_bank=True, banks_count=1,
      paycheck_into_cobalt=True, payday="biweekly on Fridays; next: Fri Dec 11", paid_fri_dec11=True,
      balance_band="under $1k", above_fdic_limit=False, knows_fdic_limit=False, moves_money_for_rate=False,
      checks_app_daily=True, uses_p2p=True, uses_spending_charts=True, fraud_victim=True,
      financial_literacy="low", credit_card_debt="$3,100", student_loans=True, lives_paycheck_to_paycheck=True,
      worried_about_prices=True, values_most="family", risk_attitude="avoids risk", trust_in_institutions="low",
      price_consciousness="high", brand_loyalty="low", need_for_control="medium",
      baseline_anxiety="high", anger_speed="medium", patience="low", forgiveness="medium",
      embarrassed_to_complain=True, news_sources=["TikTok", "her sister", "coworkers"],
      circle_size="small", influence="follower", sways_easily="high", checks_rumors=False,
      asks_before_deciding="her sister", reaction_to_bank_sms="panics a little, then calls her sister",
      why_cobalt="her sister uses it; free P2P between them",
      scar="a phishing text two years ago drained $600 from a previous bank; it was refunded after three weeks",
      recent_life_event="promoted to store manager in October, holiday season is her first as manager", fear_this_quarter="Christmas shopping on a tight budget and the paycheck landing late",
      lifestyle={"phone": "iPhone", "coffee": "sugary seasonal latte", "pet": "none", "card_design": "pink"},
      narrative="Ashley Nguyen, 31, manages a retail store in Seattle and is working her first holiday season as a manager. Cobalt is her only bank, chosen because her sister uses it and they send each other money constantly. She is paid every other Friday, including December 11, and lives paycheck to paycheck with $3,100 on a card. Two years ago a phishing text cost her $600 at a previous bank, and every bank text since makes her stomach drop. She gets her news from TikTok and her sister and tends to do what her sister does. She is anxious, easily swayed, and would rather leave quietly than complain.",
      voice="If my sister says it's fine, it's fine. If she moves her money, I'm moving mine the same day."),

    P(id="P6", name="Greg Halvorsen", group="paycheck customers", weight_customers=40_000, balance_usd=2_600,
      age=57, gender="man", city="Des Moines", state="IA", area="suburb", household="married, kids grown",
      occupation="insurance claims adjuster", employer="private insurer", employment="full-time", income_band="$80k-100k",
      home="owns (paid off)", years_customer=3, cobalt_role="main bank", only_bank=False, banks_count=2,
      paycheck_into_cobalt=True, payday="monthly on the 1st (not Dec 11)", paid_fri_dec11=False,
      balance_band="$1k-5k", above_fdic_limit=False, knows_fdic_limit=True, moves_money_for_rate=False,
      checks_app_daily=False, uses_p2p=False, uses_spending_charts=False, fraud_victim=False,
      financial_literacy="high", credit_card_debt="$0", student_loans=False, lives_paycheck_to_paycheck=False,
      worried_about_prices=False, values_most="fairness", risk_attitude="cautious", trust_in_institutions="medium",
      price_consciousness="medium", brand_loyalty="medium", need_for_control="high",
      baseline_anxiety="low", anger_speed="slow but lasting", patience="medium", forgiveness="low",
      embarrassed_to_complain=False, news_sources=["cable news", "email newsletters", "the newspaper"],
      circle_size="small", influence="independent", sways_easily="low", checks_rumors=True,
      asks_before_deciding="nobody", reaction_to_bank_sms="reads it twice and files it",
      why_cobalt="his son set it up for him when his old bank closed the local branch",
      scar="none with Cobalt; he once filed a state insurance complaint against his own industry and won",
      recent_life_event="youngest child moved out in the summer", fear_this_quarter="a change he was not told about properly",
      lifestyle={"phone": "Android", "hobby": "woodworking", "usual_atm": "the credit union downtown", "card_design": "classic grey"},
      narrative="Greg Halvorsen, 57, adjusts insurance claims in Des Moines and has spent thirty years deciding who is telling the truth. His son set up Cobalt three years ago when the old bank closed its branch; the paycheck lands on the first of the month, and a second account at a credit union holds the emergency fund. He reads every bank email twice, knows what the FDIC covers, and calls support on the phone rather than chat. He is calm and slow to anger, but he does not forgive being misled, and he knows exactly how to file a formal complaint with a regulator because he has done it before.",
      voice="Tell me what's happening, when, and what you'll do if it goes wrong. Surprise me and we have a problem."),

    # ------------------------------------------------------ savers with large balances (105k, ~$3.0B)
    P(id="S1", name="Victor Haines", group="savers with large balances", weight_customers=1_000, balance_usd=350_000,
      age=61, gender="man", city="Naples", state="FL", area="suburb", household="married, kids grown",
      occupation="retired orthodontist", employer="self (retired)", employment="retired", income_band="over $150k",
      home="owns (paid off)", years_customer=2, cobalt_role="second bank", only_bank=False, banks_count=4,
      paycheck_into_cobalt=False, payday="no paycheck; brokerage distributions quarterly", paid_fri_dec11=False,
      balance_band="over $250k", above_fdic_limit=True, knows_fdic_limit=True, moves_money_for_rate=True,
      checks_app_daily=False, uses_p2p=False, uses_spending_charts=False, fraud_victim=False,
      financial_literacy="high", credit_card_debt="$0", student_loans=False, lives_paycheck_to_paycheck=False,
      worried_about_prices=False, values_most="security", risk_attitude="conservative", trust_in_institutions="high for big banks, low for fintechs",
      price_consciousness="low on spending, high on yield", brand_loyalty="low", need_for_control="high",
      baseline_anxiety="low", anger_speed="slow", patience="medium", forgiveness="medium",
      embarrassed_to_complain=False, news_sources=["financial newsletters", "his financial advisor", "golf friends"],
      circle_size="medium", influence="leader", sways_easily="low", checks_rumors=True,
      asks_before_deciding="his advisor", reaction_to_bank_sms="ignores it; waits for the email",
      why_cobalt="parked a property-sale proceeds there for the rate; has been meaning to split it",
      scar="watched a regional bank fail in 2023 with friends' money above the insured limit",
      recent_life_event="sold a rental condo in September", fear_this_quarter="being over the FDIC limit at a young bank during a system change",
      lifestyle={"phone": "iPhone", "hobby": "golf", "coffee": "espresso", "card_design": "metal"},
      narrative="Victor Haines, 61, is a retired orthodontist in Naples, Florida, who keeps $350,000 at Cobalt because the rate was good when he parked the proceeds of a condo sale there in September. He knows that is $100,000 above the insured limit and has been meaning to do something about it. Cobalt is one of four institutions he uses; his advisor manages the rest. He trusts large banks and is wary of young ones, remembers the 2023 regional bank failures vividly, and reads financial newsletters rather than social media. His golf friends ask him where to keep cash. He is unhurried and unemotional, and he moves money when the math or the risk says so.",
      voice="I don't need a rate boost. I need to know my money is insured and reachable. Over the limit at a bank changing its core system is exactly what I tell my friends not to do."),

    P(id="S2", name="Elaine Park", group="savers with large balances", weight_customers=2_500, balance_usd=150_000,
      age=44, gender="woman", city="San Jose", state="CA", area="suburb", household="married, one child (12)",
      occupation="product manager", employer="private tech company", employment="full-time", income_band="over $150k",
      home="owns (mortgage)", years_customer=3, cobalt_role="second bank", only_bank=False, banks_count=3,
      paycheck_into_cobalt=False, payday="semi-monthly to a big bank", paid_fri_dec11=False,
      balance_band="$100k-250k", above_fdic_limit=False, knows_fdic_limit=True, moves_money_for_rate=True,
      checks_app_daily=False, uses_p2p=True, uses_spending_charts=False, fraud_victim=False,
      financial_literacy="high", credit_card_debt="$0", student_loans=False, lives_paycheck_to_paycheck=False,
      worried_about_prices=False, values_most="efficiency", risk_attitude="calculated", trust_in_institutions="medium",
      price_consciousness="high on yield", brand_loyalty="low", need_for_control="high",
      baseline_anxiety="low", anger_speed="medium", patience="low", forgiveness="conditional",
      embarrassed_to_complain=False, news_sources=["X", "LinkedIn", "coworkers"],
      circle_size="large", influence="leader", sways_easily="low", checks_rumors=True,
      asks_before_deciding="nobody; decides in an afternoon", reaction_to_bank_sms="reads it; expects a link to details",
      why_cobalt="bonus and emergency fund parked for the rate; also has a rival HYSA that now pays more",
      scar="none", recent_life_event="annual bonus landed in October", fear_this_quarter="leaving 0.5 points on the table for no reason",
      lifestyle={"phone": "iPhone", "coffee": "flat white", "hobby": "trail running", "dark_mode": True},
      narrative="Elaine Park, 44, is a product manager in San Jose with $150,000 of bonus and emergency savings at Cobalt, parked there for the rate. She already has an account at a rival online bank that now pays half a point more, and she compares the two every month. Her paycheck goes to a big bank; Cobalt is a yield decision, not a relationship. She is efficient, impatient and well informed, reads X and LinkedIn, and decides in an afternoon. Coworkers ask her where to keep cash. She is not sentimental about banks and would move the money in ten minutes if she concluded it should move.",
      voice="Half a point on $150k is $750 a year. I'll stay for a good reason, not for a logo."),

    P(id="S3", name="Robert Yancey", group="savers with large balances", weight_customers=10_000, balance_usd=55_000,
      age=55, gender="man", city="Nashville", state="TN", area="suburb", household="divorced, lives alone",
      occupation="owns two rental properties; part-time real estate agent", employer="self", employment="self-employed", income_band="$100k-150k",
      home="owns (paid off)", years_customer=4, cobalt_role="main bank", only_bank=False, banks_count=2,
      paycheck_into_cobalt=False, payday="rent comes in on the 1st; commissions irregular", paid_fri_dec11=False,
      balance_band="$50k-100k", above_fdic_limit=False, knows_fdic_limit=False, moves_money_for_rate=False,
      checks_app_daily=True, uses_p2p=True, uses_spending_charts=False, fraud_victim=False,
      financial_literacy="medium", credit_card_debt="$2,000", student_loans=False, lives_paycheck_to_paycheck=False,
      worried_about_prices=True, values_most="freedom", risk_attitude="takes risks in property, not in banking", trust_in_institutions="medium",
      price_consciousness="medium", brand_loyalty="medium", need_for_control="high",
      baseline_anxiety="medium", anger_speed="medium", patience="medium", forgiveness="medium",
      embarrassed_to_complain=False, news_sources=["local news", "neighbors", "a landlord forum"],
      circle_size="medium", influence="independent", sways_easily="medium", checks_rumors=False,
      asks_before_deciding="his accountant, sometimes", reaction_to_bank_sms="reads it later in the day",
      why_cobalt="the app made it easy to pay contractors and track two properties",
      scar="none", recent_life_event="a furnace replacement in one rental in November", fear_this_quarter="not being able to pay a contractor the weekend something breaks",
      lifestyle={"phone": "Android", "sports_team": "Titans", "pet": "dog", "usual_atm": "the Kroger on Franklin Pike"},
      narrative="Robert Yancey, 55, owns two rental houses in Nashville and sells a few properties a year on the side. Cobalt is his main account: $55,000 of operating reserve sits there because the app makes it easy to pay contractors and keep the two properties straight. He does not know or care about the FDIC limit; he cares about paying the furnace guy the day the furnace dies. He checks the app daily, hears things from neighbors and a landlord forum, and does not verify much. He is independent, mildly anxious about money, and judges a bank by whether it works when he needs it.",
      voice="I don't chase rates. I need to pay a contractor on a Saturday and have it go through."),

    P(id="S4", name="Dana Whitfield", group="savers with large balances", weight_customers=20_000, balance_usd=30_000,
      age=36, gender="woman", city="Chicago", state="IL", area="city", household="engaged, lives with her fiancé",
      occupation="attorney", employer="private law firm", employment="full-time", income_band="$100k-150k",
      home="rents (buying in spring)", years_customer=3, cobalt_role="main bank", only_bank=False, banks_count=2,
      paycheck_into_cobalt=True, payday="semi-monthly on the 15th and 30th", paid_fri_dec11=False,
      balance_band="$25k-50k", above_fdic_limit=False, knows_fdic_limit=True, moves_money_for_rate=False,
      checks_app_daily=True, uses_p2p=True, uses_spending_charts=True, fraud_victim=False,
      financial_literacy="high", credit_card_debt="$0", student_loans=True, lives_paycheck_to_paycheck=False,
      worried_about_prices=True, values_most="control", risk_attitude="cautious", trust_in_institutions="medium",
      price_consciousness="medium", brand_loyalty="medium", need_for_control="very high",
      baseline_anxiety="high", anger_speed="medium", patience="low", forgiveness="low",
      embarrassed_to_complain=False, news_sources=["Reddit", "friends", "a parents-to-be group"],
      circle_size="medium", influence="independent", sways_easily="medium", checks_rumors=True,
      asks_before_deciding="her fiancé", reaction_to_bank_sms="reads it immediately; wants details, not reassurance",
      why_cobalt="good app, decent rate; her down-payment fund has grown there for three years",
      scar="none", recent_life_event="got engaged in August; house hunting for a spring closing", fear_this_quarter="the down payment being unreachable when an offer is accepted",
      lifestyle={"phone": "iPhone", "coffee": "americano", "hobby": "yoga", "dark_mode": False},
      narrative="Dana Whitfield, 36, is an attorney in Chicago whose $30,000 house down payment sits at Cobalt, where it has grown for three years. She and her fiancé plan to buy in the spring, and an accepted offer could come any week, so the money must be reachable. She knows the FDIC rules, checks the app daily and uses the spending charts. She is precise, anxious about anything outside her control, and reacts to vague messages by demanding specifics. Friends from a parents-to-be group ask her to read fine print. She does not forgive easily, and a bank that locks her money for a weekend without a clear reason would hear from her.",
      voice="Don't tell me not to worry. Tell me exactly what I can and can't do, and for how long."),

    P(id="S5", name="Hank Morrison", group="savers with large balances", weight_customers=30_000, balance_usd=20_000,
      age=68, gender="man", city="Tucson", state="AZ", area="suburb", household="widowed, lives alone",
      occupation="retired electrician", employer="self (retired)", employment="retired", income_band="$40k-60k",
      home="owns (paid off)", years_customer=2, cobalt_role="second bank", only_bank=False, banks_count=2,
      paycheck_into_cobalt=False, payday="pension and Social Security to a big bank on the 3rd", paid_fri_dec11=False,
      balance_band="$10k-25k", above_fdic_limit=False, knows_fdic_limit=False, moves_money_for_rate=False,
      checks_app_daily=False, uses_p2p=False, uses_spending_charts=False, fraud_victim=False,
      financial_literacy="medium-low", credit_card_debt="$0", student_loans=False, lives_paycheck_to_paycheck=False,
      worried_about_prices=True, values_most="security", risk_attitude="avoids risk", trust_in_institutions="medium",
      price_consciousness="high", brand_loyalty="high once earned", need_for_control="medium",
      baseline_anxiety="medium", anger_speed="slow", patience="high", forgiveness="high",
      embarrassed_to_complain=True, news_sources=["local TV news", "neighbors", "his daughter"],
      circle_size="small", influence="follower", sways_easily="high", checks_rumors=False,
      asks_before_deciding="his daughter", reaction_to_bank_sms="does not trust texts; calls the number on the card",
      why_cobalt="his daughter opened it for him to earn a better rate on the savings from selling his truck",
      scar="none", recent_life_event="sold his work truck in the spring", fear_this_quarter="losing track of his money if the app changes",
      lifestyle={"phone": "Android (large font)", "hobby": "fixing neighbors' things", "usual_atm": "the big bank's branch", "card_design": "classic grey"},
      narrative="Hank Morrison, 68, is a retired electrician in Tucson. His pension and Social Security go to the big bank he has used for forty years; Cobalt holds $20,000 from selling his work truck, opened by his daughter because the rate was better. He does not log in much and does not trust texts, so when something comes up he calls the number on the card or calls his daughter. He gets the news from local TV and neighbors. He is patient and loyal once a company has earned it, slow to anger and embarrassed to complain, and he would rather do nothing than do the wrong thing.",
      voice="My daughter put it there and she'll tell me if I need to move it. I just don't want it to disappear on me."),

    P(id="S6", name="Chloe Bennett", group="savers with large balances", weight_customers=41_500, balance_usd=13_000,
      age=33, gender="woman", city="Austin", state="TX", area="city", household="lives alone",
      occupation="software engineer", employer="private tech company", employment="full-time", income_band="$100k-150k",
      home="rents", years_customer=5, cobalt_role="main bank", only_bank=False, banks_count=3,
      paycheck_into_cobalt=True, payday="biweekly on Fridays; next: Fri Dec 11", paid_fri_dec11=True,
      balance_band="$10k-25k", above_fdic_limit=False, knows_fdic_limit=True, moves_money_for_rate=True,
      checks_app_daily=True, uses_p2p=True, uses_spending_charts=True, fraud_victim=False,
      financial_literacy="high", credit_card_debt="$0", student_loans=False, lives_paycheck_to_paycheck=False,
      worried_about_prices=False, values_most="freedom", risk_attitude="calculated", trust_in_institutions="medium",
      price_consciousness="high on yield", brand_loyalty="medium", need_for_control="high",
      baseline_anxiety="low", anger_speed="medium", patience="medium", forgiveness="conditional",
      embarrassed_to_complain=False, news_sources=["Reddit", "YouTube", "Hacker News"],
      circle_size="large online", influence="leader", sways_easily="low", checks_rumors=True,
      asks_before_deciding="nobody; posts her reasoning afterwards", reaction_to_bank_sms="reads it, screenshots it, posts it if it is interesting",
      why_cobalt="early adopter; likes the app, the dark mode and the spending charts; it is her main account since 2021",
      scar="none", recent_life_event="booked a three-week trip to Japan for February", fear_this_quarter="a clumsy migration that makes her look naive for recommending Cobalt",
      lifestyle={"phone": "Android", "coffee": "pour-over", "hobby": "climbing", "dark_mode": True, "card_design": "matte black"},
      narrative="Chloe Bennett, 33, is a software engineer in Austin and one of Cobalt's early customers: main account since 2021, paycheck every other Friday including December 11, $13,000 saved for a trip to Japan in February. She likes the product and has said so on Reddit more than once, which makes her a public face for it among people who do not know her. She knows the FDIC limit, watches rates and has moved money for half a point before. She reads Hacker News and Reddit, checks claims before repeating them, and posts her reasoning after she decides. If the migration goes badly she will say so in the same places, with screenshots.",
      voice="I've recommended Cobalt to a lot of strangers. Don't make me write the post that takes it back."),

    # --------------------------------------- small business owners with a Cobalt card reader (42k)
    P(id="B1", name="Tomás Herrera", group="small business owners with a Cobalt card reader", weight_customers=7_000, balance_usd=9_000,
      age=39, gender="man", city="El Paso", state="TX", area="city", household="married, three kids",
      occupation="owns three food trucks", employer="self", employment="self-employed", income_band="$80k-100k",
      home="owns (mortgage)", years_customer=3, cobalt_role="main bank", only_bank=False, banks_count=2,
      paycheck_into_cobalt=False, payday="card-reader sales settle daily; biggest nights Friday and Saturday", paid_fri_dec11=False,
      balance_band="$5k-10k", above_fdic_limit=False, knows_fdic_limit=False, moves_money_for_rate=False,
      checks_app_daily=True, uses_p2p=True, uses_spending_charts=True, fraud_victim=False,
      financial_literacy="medium", credit_card_debt="$4,000 (business)", student_loans=False, lives_paycheck_to_paycheck=False,
      worried_about_prices=True, values_most="family", risk_attitude="takes risks", trust_in_institutions="medium",
      price_consciousness="high", brand_loyalty="medium", need_for_control="high",
      baseline_anxiety="medium", anger_speed="medium", patience="medium", forgiveness="medium",
      embarrassed_to_complain=False, news_sources=["Instagram", "other vendors", "a food-truck owners' chat"],
      circle_size="large", influence="leader", sways_easily="low", checks_rumors=False,
      asks_before_deciding="his wife, who does the books", reaction_to_bank_sms="reads it between orders; acts if it affects tonight",
      why_cobalt="the card reader's fees beat the competition and settlement is fast",
      scar="a different processor froze his funds for a week two years ago",
      recent_life_event="added the third truck in September", fear_this_quarter="Saturday Dec 12 is a big night and Sunday is restock day; no transfers means no restock",
      lifestyle={"phone": "Android", "sports_team": "Chihuahuas", "coffee": "cafecito", "card_design": "red"},
      narrative="Tomás Herrera, 39, runs three food trucks in El Paso with his wife, who keeps the books. Every truck has a Cobalt card reader because the fees beat the competition and the money settles fast; the average ticket is $12 and Friday and Saturday nights are half the week's sales. Sunday is restock day, paid by transfer. Two years ago another processor froze his funds for a week and he has not trusted a payment company fully since. He gets his news from Instagram and a chat of other vendors, where people listen to him. He is a risk-taker in business and practical about banks: it works or he changes it.",
      voice="Saturday is the night. If the reader works and Sunday's transfer goes through, I don't care what they call the system."),

    P(id="B2", name="Beth Caldwell", group="small business owners with a Cobalt card reader", weight_customers=7_000, balance_usd=6_000,
      age=48, gender="woman", city="Burlington", state="VT", area="small town", household="married, one teenager",
      occupation="owns a yarn and craft shop", employer="self", employment="self-employed", income_band="$60k-80k",
      home="owns (mortgage)", years_customer=2, cobalt_role="main bank", only_bank=False, banks_count=2,
      paycheck_into_cobalt=False, payday="card-reader sales settle daily; December is 40% of the year", paid_fri_dec11=False,
      balance_band="$5k-10k", above_fdic_limit=False, knows_fdic_limit=False, moves_money_for_rate=False,
      checks_app_daily=True, uses_p2p=False, uses_spending_charts=True, fraud_victim=False,
      financial_literacy="medium", credit_card_debt="$1,500", student_loans=False, lives_paycheck_to_paycheck=False,
      worried_about_prices=True, values_most="community", risk_attitude="cautious", trust_in_institutions="medium",
      price_consciousness="high", brand_loyalty="high", need_for_control="medium",
      baseline_anxiety="medium", anger_speed="slow", patience="high", forgiveness="high",
      embarrassed_to_complain=False, news_sources=["Facebook groups", "the local paper", "customers"],
      circle_size="medium", influence="independent", sways_easily="medium", checks_rumors=False,
      asks_before_deciding="her husband", reaction_to_bank_sms="reads it and mentions it to customers",
      why_cobalt="a small-business group recommended the reader; she likes that a person answers support",
      scar="none", recent_life_event="hired a seasonal helper in November", fear_this_quarter="a Saturday in December where she cannot take cards",
      lifestyle={"phone": "iPhone", "hobby": "knitting (obviously)", "pet": "shop cat", "card_design": "forest green"},
      narrative="Beth Caldwell, 48, owns a yarn and craft shop in Burlington, Vermont, where December brings forty percent of the year's sales. Her Cobalt card reader takes most of them; the average ticket is $45. She checks the app every morning, writes reviews for things she likes and dislikes, and talks to her customers all day, which means whatever she thinks of her bank gets said out loud to a hundred people a week. She reads the local paper and Facebook groups and does not verify much. She is patient, loyal and slow to anger, and she expects a company to talk to her like a person.",
      voice="Just be straight with me. I've got a shop full of people on a December Saturday and I need to know if the reader works."),

    P(id="B3", name="Jamal Reed", group="small business owners with a Cobalt card reader", weight_customers=7_000, balance_usd=4_000,
      age=33, gender="man", city="Detroit", state="MI", area="city", household="lives with his girlfriend",
      occupation="owns a mobile auto-detailing business", employer="self", employment="self-employed", income_band="$40k-60k",
      home="rents", years_customer=2, cobalt_role="main bank", only_bank=True, banks_count=1,
      paycheck_into_cobalt=False, payday="card-reader sales; tickets $150-$400, mostly weekends", paid_fri_dec11=False,
      balance_band="$1k-5k", above_fdic_limit=False, knows_fdic_limit=False, moves_money_for_rate=False,
      checks_app_daily=True, uses_p2p=True, uses_spending_charts=False, fraud_victim=False,
      financial_literacy="medium-low", credit_card_debt="$2,800", student_loans=False, lives_paycheck_to_paycheck=True,
      worried_about_prices=True, values_most="freedom", risk_attitude="takes risks", trust_in_institutions="low",
      price_consciousness="high", brand_loyalty="low", need_for_control="high",
      baseline_anxiety="medium", anger_speed="fast", patience="low", forgiveness="low",
      embarrassed_to_complain=False, news_sources=["X", "YouTube", "other detailers"],
      circle_size="large online", influence="leader", sways_easily="low", checks_rumors=False,
      asks_before_deciding="nobody", reaction_to_bank_sms="reads it; posts about it if it is bad",
      why_cobalt="cheapest reader for a one-man business; instant transfers to pay his supplier",
      scar="a chargeback on a $300 job that Cobalt sided with the customer on",
      recent_life_event="bought a second pressure washer in October", fear_this_quarter="a $300 job he cannot charge because the card limit is $100",
      lifestyle={"phone": "Android", "sports_team": "Lions", "hobby": "sim racing", "card_design": "black"},
      narrative="Jamal Reed, 33, runs a one-man mobile auto-detailing business in Detroit. Cobalt is his only bank and his card reader: tickets run $150 to $400, mostly on weekends, and he pays his chemical supplier by instant transfer on Mondays. He lives close to the edge, with $2,800 on a card. A chargeback on a $300 job that Cobalt resolved in the customer's favor still makes him angry. He posts on X and YouTube and other detailers follow him. He is fast to anger, slow to forgive, trusts no institution much, and will say exactly what he thinks in public.",
      voice="A $100 limit on a $300 job is a joke. If the reader doesn't work Saturday, everybody on my feed hears about it Saturday."),

    P(id="B4", name="Karen Lindqvist", group="small business owners with a Cobalt card reader", weight_customers=7_000, balance_usd=7_000,
      age=56, gender="woman", city="Duluth", state="MN", area="small town", household="married, kids grown",
      occupation="owns a hair salon with four chairs", employer="self", employment="self-employed", income_band="$60k-80k",
      home="owns (paid off)", years_customer=3, cobalt_role="main bank", only_bank=False, banks_count=2,
      paycheck_into_cobalt=False, payday="card-reader sales daily; pays her stylists by P2P every Sunday morning", paid_fri_dec11=False,
      balance_band="$5k-10k", above_fdic_limit=False, knows_fdic_limit=False, moves_money_for_rate=False,
      checks_app_daily=True, uses_p2p=True, uses_spending_charts=False, fraud_victim=False,
      financial_literacy="medium", credit_card_debt="$0", student_loans=False, lives_paycheck_to_paycheck=False,
      worried_about_prices=True, values_most="loyalty", risk_attitude="cautious", trust_in_institutions="medium",
      price_consciousness="medium", brand_loyalty="high", need_for_control="medium",
      baseline_anxiety="medium", anger_speed="slow", patience="medium", forgiveness="high",
      embarrassed_to_complain=False, news_sources=["her stylists", "Facebook", "local radio"],
      circle_size="large", influence="leader", sways_easily="medium", checks_rumors=False,
      asks_before_deciding="her husband", reaction_to_bank_sms="reads it and tells the whole salon",
      why_cobalt="the free P2P payouts to her stylists save her a weekly trip to the bank",
      scar="none", recent_life_event="one stylist left in October; hired a replacement", fear_this_quarter="not being able to pay her stylists on Sunday Dec 13",
      lifestyle={"phone": "iPhone", "hobby": "ice fishing with her husband", "usual_atm": "the Super One on Grand", "card_design": "lavender"},
      narrative="Karen Lindqvist, 56, owns a four-chair hair salon in Duluth, Minnesota. Cobalt handles the card reader and, every Sunday morning, the P2P payouts to her stylists, which is the reason she switched three years ago. She is loyal, patient and forgiving, and she talks: whatever she thinks about her bank, the four stylists and the day's clients hear it. She hears news from her stylists, Facebook and local radio and rarely checks it. Her one fear this quarter is simple: Sunday, December 13, four stylists expecting their pay, and the app read-only.",
      voice="I pay my girls on Sunday morning. That's the deal. If I can't, I'm the one who looks bad, not the bank."),

    P(id="B5", name="Diego Alvarez", group="small business owners with a Cobalt card reader", weight_customers=7_000, balance_usd=1_500,
      age=29, gender="man", city="Miami", state="FL", area="city", household="lives with two roommates",
      occupation="runs a coffee stand at farmers' markets", employer="self", employment="self-employed", income_band="$25k-40k",
      home="rents", years_customer=1, cobalt_role="main bank", only_bank=True, banks_count=1,
      paycheck_into_cobalt=False, payday="card-reader sales on Saturday and Sunday mornings", paid_fri_dec11=False,
      balance_band="$1k-5k", above_fdic_limit=False, knows_fdic_limit=False, moves_money_for_rate=False,
      checks_app_daily=True, uses_p2p=True, uses_spending_charts=False, fraud_victim=False,
      financial_literacy="low", credit_card_debt="$1,900", student_loans=True, lives_paycheck_to_paycheck=True,
      worried_about_prices=True, values_most="freedom", risk_attitude="takes risks", trust_in_institutions="low",
      price_consciousness="very high", brand_loyalty="low", need_for_control="low",
      baseline_anxiety="high", anger_speed="medium", patience="low", forgiveness="medium",
      embarrassed_to_complain=True, news_sources=["Instagram", "market vendors", "roommates"],
      circle_size="medium", influence="follower", sways_easily="high", checks_rumors=False,
      asks_before_deciding="Tomás-type vendors he looks up to", reaction_to_bank_sms="reads it; worries; asks another vendor",
      why_cobalt="cheapest reader he could find; free P2P with his roommates and suppliers",
      scar="none", recent_life_event="started a second market on Sundays in November", fear_this_quarter="a weekend with no sales and rent due",
      lifestyle={"phone": "iPhone", "coffee": "cortadito", "hobby": "surfing", "card_design": "orange"},
      narrative="Diego Alvarez, 29, runs a coffee stand at two farmers' markets in Miami, Saturday and Sunday mornings. Cobalt is his only bank, chosen a year ago because the reader was the cheapest and P2P with his roommates and suppliers is free. He has $1,500 in the account, $1,900 on a card and rent due on the first. He follows other vendors on Instagram and does what the ones he looks up to do. He is anxious, price-obsessed and embarrassed to complain; a lost weekend of sales is not an inconvenience for him, it is the rent.",
      voice="One bad weekend and I'm short on rent. I just need the reader to work on Saturday morning."),

    P(id="B6", name="Patricia Osei", group="small business owners with a Cobalt card reader", weight_customers=7_000, balance_usd=9_000,
      age=51, gender="woman", city="Baltimore", state="MD", area="city", household="married, two adult children",
      occupation="owns a home health care agency with 12 staff", employer="self", employment="self-employed", income_band="$100k-150k",
      home="owns (mortgage)", years_customer=2, cobalt_role="main bank", only_bank=False, banks_count=2,
      paycheck_into_cobalt=False, payday="clients pay by card reader; she pays staff by instant transfer on Fridays, incl. Dec 11", paid_fri_dec11=False,
      balance_band="$5k-10k", above_fdic_limit=False, knows_fdic_limit=True, moves_money_for_rate=False,
      checks_app_daily=True, uses_p2p=False, uses_spending_charts=True, fraud_victim=False,
      financial_literacy="high", credit_card_debt="$0", student_loans=False, lives_paycheck_to_paycheck=False,
      worried_about_prices=True, values_most="responsibility", risk_attitude="cautious", trust_in_institutions="high",
      price_consciousness="medium", brand_loyalty="medium", need_for_control="high",
      baseline_anxiety="medium", anger_speed="slow", patience="medium", forgiveness="conditional",
      embarrassed_to_complain=False, news_sources=["the local business association", "email", "local news"],
      circle_size="large", influence="leader", sways_easily="low", checks_rumors=True,
      asks_before_deciding="her bookkeeper", reaction_to_bank_sms="reads it and forwards it to her bookkeeper",
      why_cobalt="the reader for client co-pays and fast transfers to pay twelve caregivers weekly",
      scar="a previous bank held a large deposit for ten days 'for review' and she missed payroll once",
      recent_life_event="took on two new clients in November", fear_this_quarter="missing Friday pay for twelve caregivers who live on it",
      lifestyle={"phone": "iPhone", "hobby": "church choir", "coffee": "tea, actually", "card_design": "navy"},
      narrative="Patricia Osei, 51, owns a home health care agency in Baltimore with twelve caregivers. Clients pay co-pays through a Cobalt card reader and she pays the caregivers by instant transfer every Friday, including December 11. A previous bank once held a deposit for ten days and she missed a payroll; she still remembers the phone calls. She is organized, trusts institutions that behave like institutions, knows the FDIC limit, and forwards every bank email to her bookkeeper. She leads the local business association's small-employer group and knows how to file a formal complaint. She is slow to anger and does not forget.",
      voice="Twelve people get paid on Friday because of me. The bank doesn't get to be the reason they don't."),

    # ------------------------------------------------------------------ everyday customers (1,643k)
    P(id="E1", name="Maya Thompson", group="everyday customers", weight_customers=400_000, balance_usd=1_750,
      age=27, gender="woman", city="Denver", state="CO", area="city", household="lives with her partner",
      occupation="UX designer", employer="private startup", employment="full-time", income_band="$80k-100k",
      home="rents", years_customer=3, cobalt_role="main bank", only_bank=False, banks_count=2,
      paycheck_into_cobalt=True, payday="semi-monthly", paid_fri_dec11=False,
      balance_band="$1k-5k", above_fdic_limit=False, knows_fdic_limit=False, moves_money_for_rate=False,
      checks_app_daily=True, uses_p2p=True, uses_spending_charts=True, fraud_victim=False,
      financial_literacy="medium", credit_card_debt="$800", student_loans=True, lives_paycheck_to_paycheck=False,
      worried_about_prices=False, values_most="convenience", risk_attitude="calculated", trust_in_institutions="medium",
      price_consciousness="medium", brand_loyalty="medium", need_for_control="medium",
      baseline_anxiety="low", anger_speed="medium", patience="medium", forgiveness="medium",
      embarrassed_to_complain=False, news_sources=["Instagram", "Reddit", "friend group chat"],
      circle_size="large", influence="leader", sways_easily="low", checks_rumors=True,
      asks_before_deciding="nobody; tells friends afterwards", reaction_to_bank_sms="reads it; judges the writing",
      why_cobalt="she recommends apps for a living and Cobalt's was the best-designed bank app she had seen",
      scar="none", recent_life_event="planning a ski weekend Dec 12-13", fear_this_quarter="being locked out of the app on a weekend away",
      lifestyle={"phone": "iPhone", "coffee": "matcha", "hobby": "skiing", "dark_mode": True, "card_design": "teal"},
      narrative="Maya Thompson, 27, is a UX designer in Denver who picked Cobalt three years ago because its app was the best-designed bank app she had seen, and she has told a lot of friends so. Her paycheck lands there twice a month, she opens the app every day and uses the spending charts. She has a backup account at a big bank she barely touches. She reads Instagram and Reddit, checks before she repeats, and her friend group follows her lead on apps. She is calm and fair, judges a company by how it communicates, and has a ski weekend planned for December 12 and 13.",
      voice="I judge banks by their app and their words. A clear, honest message buys a lot of patience from me. A vague one costs it."),

    P(id="E2", name="Derek Lawson", group="everyday customers", weight_customers=350_000, balance_usd=300,
      age=34, gender="man", city="Columbus", state="OH", area="suburb", household="married, one child (3)",
      occupation="warehouse shift lead", employer="private logistics company", employment="full-time", income_band="$40k-60k",
      home="rents", years_customer=2, cobalt_role="second bank", only_bank=False, banks_count=2,
      paycheck_into_cobalt=False, payday="weekly on Fridays to a big bank", paid_fri_dec11=False,
      balance_band="under $1k", above_fdic_limit=False, knows_fdic_limit=False, moves_money_for_rate=False,
      checks_app_daily=False, uses_p2p=True, uses_spending_charts=False, fraud_victim=False,
      financial_literacy="low", credit_card_debt="$2,200", student_loans=False, lives_paycheck_to_paycheck=True,
      worried_about_prices=True, values_most="family", risk_attitude="avoids risk", trust_in_institutions="medium",
      price_consciousness="high", brand_loyalty="low", need_for_control="low",
      baseline_anxiety="medium", anger_speed="medium", patience="medium", forgiveness="medium",
      embarrassed_to_complain=True, news_sources=["coworkers", "Facebook"],
      circle_size="small", influence="follower", sways_easily="medium", checks_rumors=False,
      asks_before_deciding="his wife", reaction_to_bank_sms="glances at it; usually ignores it",
      why_cobalt="opened it for a sign-up bonus; keeps it for the debit card and P2P with coworkers",
      scar="none", recent_life_event="moved to the night shift in November", fear_this_quarter="none about Cobalt; he barely thinks about it",
      lifestyle={"phone": "Android", "sports_team": "Buckeyes", "hobby": "fantasy football", "card_design": "black"},
      narrative="Derek Lawson, 34, is a warehouse shift lead in Columbus with a three-year-old at home. His weekly paycheck goes to a big bank; Cobalt is a second account he opened for a sign-up bonus and keeps for the debit card and splitting lunch orders with coworkers by P2P. He opens the app maybe twice a month and has $300 in it. He hears about things from coworkers and Facebook and rarely checks. He is not angry at Cobalt and not attached to it either; if it became a hassle he would just stop using it, without telling anyone.",
      voice="It's the card I use for lunch. If it stops working I'll use the other one and probably forget to come back."),

    P(id="E3", name="Priya Raman", group="everyday customers", weight_customers=300_000, balance_usd=2_200,
      age=41, gender="woman", city="Sacramento", state="CA", area="suburb", household="married, two kids (8 and 11)",
      occupation="dental hygienist", employer="private dental practice", employment="part-time", income_band="$80k-100k (household)",
      home="owns (mortgage)", years_customer=4, cobalt_role="main bank", only_bank=False, banks_count=2,
      paycheck_into_cobalt=True, payday="biweekly on Thursdays", paid_fri_dec11=False,
      balance_band="$1k-5k", above_fdic_limit=False, knows_fdic_limit=False, moves_money_for_rate=False,
      checks_app_daily=False, uses_p2p=True, uses_spending_charts=False, fraud_victim=True,
      financial_literacy="medium", credit_card_debt="$0", student_loans=False, lives_paycheck_to_paycheck=False,
      worried_about_prices=True, values_most="security", risk_attitude="avoids risk", trust_in_institutions="medium-low",
      price_consciousness="medium", brand_loyalty="medium", need_for_control="high",
      baseline_anxiety="medium", anger_speed="slow", patience="medium", forgiveness="low",
      embarrassed_to_complain=False, news_sources=["family group chat", "local news", "a parents' group"],
      circle_size="medium", influence="independent", sways_easily="medium", checks_rumors=True,
      asks_before_deciding="her husband", reaction_to_bank_sms="distrusts it since the fraud; logs in separately to check",
      why_cobalt="good app and no fees; the family's day-to-day account",
      scar="card fraud two years ago: $900 charged, Cobalt's dispute took the full 45 days and she had to re-send documents",
      recent_life_event="older child started middle school", fear_this_quarter="another fraud wave during the migration confusion",
      lifestyle={"phone": "iPhone", "hobby": "gardening", "pet": "two guinea pigs", "card_design": "sage green"},
      narrative="Priya Raman, 41, is a part-time dental hygienist in Sacramento with two kids; Cobalt is the family's day-to-day account. Two years ago her card was used for $900 of fraud and the dispute took the full 45 days and a second round of documents; she got the money back but not the feeling. She now distrusts bank texts and logs in separately to check anything. She hears news in the family group chat and a parents' group and does check before passing it on. She is slow to anger and slow to forgive, values security above everything, and watches for the next thing going wrong.",
      voice="Last time it took 45 days to get my own money back. I'm not going through that twice."),

    P(id="E4", name="Tyler Brooks", group="everyday customers", weight_customers=250_000, balance_usd=350,
      age=23, gender="man", city="Atlanta", state="GA", area="city", household="three roommates",
      occupation="barista and gig delivery driver", employer="private café + gig platform", employment="part-time + gig", income_band="$25k-40k",
      home="rents", years_customer=2, cobalt_role="main bank", only_bank=True, banks_count=1,
      paycheck_into_cobalt=True, payday="café pays biweekly on Fridays incl. Dec 11; gig payouts daily", paid_fri_dec11=True,
      balance_band="under $1k", above_fdic_limit=False, knows_fdic_limit=False, moves_money_for_rate=False,
      checks_app_daily=True, uses_p2p=True, uses_spending_charts=False, fraud_victim=False,
      financial_literacy="low", credit_card_debt="$700", student_loans=True, lives_paycheck_to_paycheck=True,
      worried_about_prices=True, values_most="freedom", risk_attitude="takes risks", trust_in_institutions="low",
      price_consciousness="high", brand_loyalty="low", need_for_control="low",
      baseline_anxiety="medium", anger_speed="fast", patience="very low", forgiveness="fast (forgets)",
      embarrassed_to_complain=False, news_sources=["TikTok", "roommates", "group chats"],
      circle_size="large", influence="follower", sways_easily="very high", checks_rumors=False,
      asks_before_deciding="the group chat", reaction_to_bank_sms="screenshots it to the group chat",
      why_cobalt="everyone in his friend group uses it for splitting rent and bills",
      scar="none", recent_life_event="picked up more delivery shifts for the holidays", fear_this_quarter="rent split not going through on the 1st and roommates on his case",
      lifestyle={"phone": "iPhone", "coffee": "whatever is free at work", "hobby": "pickup basketball", "card_design": "orange"},
      narrative="Tyler Brooks, 23, works mornings as a barista in Atlanta and delivers for a gig app at night. Cobalt is his only bank because his whole friend group uses it to split rent and bills by P2P. His café pay lands every other Friday, including December 11, and gig payouts trickle in daily; he has $350 in the account and checks it constantly. He gets everything from TikTok and group chats, screenshots bank texts to his roommates, and does what the chat says. He is quick to anger, quick to forget, and would switch banks in an afternoon if the group did.",
      voice="If the P2P is down my roommates think I'm dodging rent. That's the whole problem, right there."),

    P(id="E5", name="Linda Garza", group="everyday customers", weight_customers=200_000, balance_usd=1_600,
      age=52, gender="woman", city="San Antonio", state="TX", area="suburb", household="married, one adult child at home",
      occupation="school administrative assistant", employer="public school district", employment="full-time", income_band="$40k-60k",
      home="owns (mortgage)", years_customer=4, cobalt_role="main bank", only_bank=False, banks_count=2,
      paycheck_into_cobalt=True, payday="monthly on the 20th", paid_fri_dec11=False,
      balance_band="$1k-5k", above_fdic_limit=False, knows_fdic_limit=False, moves_money_for_rate=False,
      checks_app_daily=False, uses_p2p=True, uses_spending_charts=False, fraud_victim=False,
      financial_literacy="medium", credit_card_debt="$1,100", student_loans=False, lives_paycheck_to_paycheck=False,
      worried_about_prices=True, values_most="family", risk_attitude="cautious", trust_in_institutions="high",
      price_consciousness="high", brand_loyalty="high", need_for_control="low",
      baseline_anxiety="low", anger_speed="slow", patience="high", forgiveness="high",
      embarrassed_to_complain=True, news_sources=["email", "local TV news", "her sister"],
      circle_size="medium", influence="follower", sways_easily="medium", checks_rumors=False,
      asks_before_deciding="her sister", reaction_to_bank_sms="reads it and does what it says",
      why_cobalt="no monthly fee; her old bank started charging one",
      scar="none with Cobalt; the old bank's fee",
      recent_life_event="none", fear_this_quarter="a new fee showing up; outages she can live with",
      lifestyle={"phone": "Android", "hobby": "telenovelas and church bake sales", "usual_atm": "the H-E-B on Culebra", "card_design": "lavender", "dark_mode": True},
      narrative="Linda Garza, 52, is an administrative assistant at a San Antonio school and has banked with Cobalt for four years, ever since her old bank added a monthly fee. Her paycheck arrives on the 20th; she checks the app a couple of times a week, in dark mode, and uses the same H-E-B ATM every Saturday. She trusts institutions, reads the bank's emails and does what they ask, and would be embarrassed to complain. She is patient and forgiving; an outage is a nuisance, a fee is a betrayal. Her sister is the one she calls about money.",
      voice="They told me there'd be no fees and there haven't been. If a weekend goes sideways I'll wait. If a fee shows up, I'm gone."),

    P(id="E6", name="Owen Fitzgerald", group="everyday customers", weight_customers=143_000, balance_usd=700,
      age=30, gender="man", city="Portland", state="OR", area="city", household="lives alone",
      occupation="freelance videographer", employer="self", employment="self-employed", income_band="$40k-60k (irregular)",
      home="rents", years_customer=3, cobalt_role="main bank", only_bank=False, banks_count=3,
      paycheck_into_cobalt=False, payday="client invoices, irregular", paid_fri_dec11=False,
      balance_band="under $1k", above_fdic_limit=False, knows_fdic_limit=True, moves_money_for_rate=True,
      checks_app_daily=True, uses_p2p=True, uses_spending_charts=True, fraud_victim=False,
      financial_literacy="high", credit_card_debt="$1,400", student_loans=True, lives_paycheck_to_paycheck=True,
      worried_about_prices=True, values_most="freedom", risk_attitude="calculated", trust_in_institutions="low",
      price_consciousness="very high", brand_loyalty="low", need_for_control="high",
      baseline_anxiety="medium", anger_speed="medium", patience="low", forgiveness="conditional",
      embarrassed_to_complain=False, news_sources=["Reddit personal finance", "YouTube", "a freelancers' Discord"],
      circle_size="large online", influence="leader", sways_easily="low", checks_rumors=True,
      asks_before_deciding="nobody; posts the comparison", reaction_to_bank_sms="reads it; compares it to what the rival sent",
      why_cobalt="checking and card here; savings at a rival online bank that pays more",
      scar="none", recent_life_event="slow month in November; invoices late", fear_this_quarter="a late invoice landing during a weekend when he cannot move it to cover rent",
      lifestyle={"phone": "Android", "coffee": "drip, lots", "hobby": "bikepacking", "dark_mode": True, "card_design": "matte black"},
      narrative="Owen Fitzgerald, 30, is a freelance videographer in Portland with irregular income: some months are fine, November was not. Cobalt is his checking account and card; his savings sit at a rival online bank that pays more, and he has moved money for a rate before. He has $700 in Cobalt, a late invoice outstanding and rent on the first. He knows the FDIC rules, reads r/personalfinance and a freelancers' Discord, checks claims, and posts comparisons that other freelancers read. He trusts no bank much and judges them against each other, constantly.",
      voice="I keep a comparison spreadsheet. Cobalt's checking wins today. The savings already left for the rate; the checking can leave too."),
]

# Explicit cross-group bridges (undirected). From the briefs and spec.md §5.
BRIDGES = [("P3", "S6"), ("S6", "E6"), ("B1", "B5"), ("P1", "P5"), ("P5", "E4"), ("S1", "S5"),
           ("B6", "P4"), ("S2", "E1"), ("P2", "B3"), ("S4", "E3")]

WAVE = {  # 1 = leaders post first, 2 = independents, 3 = easily swayed
    "leader": 1, "independent": 2, "follower": 3,
}

# When money lands in the persona's Cobalt account, by simulation week (week 1 = Nov 2-8, 2026).
# Fri Dec 11 is in week 6. Biweekly Fridays from Dec 11: Nov 13 (w2), Nov 27 (w4), Dec 25 (w8), Jan 8 (w10).
PAY_RULES = {
    "biweekly_friday_dec11": ([2, 4, 6, 8, 10], "paid every other Friday: Nov 13, Nov 27, Dec 11, Dec 25, Jan 8"),
    "semimonthly_15_last": ([2, 5, 7, 9], "paid on the 15th and the last day of the month: Nov 15, Nov 30, Dec 15, Dec 31"),
    "monthly_1st": ([5, 9], "paid on the 1st: Dec 1, Jan 1"),
    "monthly_20th": ([3, 7], "paid on the 20th: Nov 20, Dec 20"),
    "biweekly_thursday": ([1, 3, 5, 7, 9], "paid every other Thursday: Nov 5, Nov 19, Dec 3, Dec 17, Dec 31"),
    "rent_1st": ([5, 9], "rent from tenants lands on the 1st: Dec 1, Jan 1; commissions irregular"),
    "daily_sales": ([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], "card-reader sales settle into Cobalt every business day"),
    "irregular": ([], "client invoices land irregularly; nothing scheduled"),
    "none_into_cobalt": ([], "no income is paid into Cobalt; money arrives at another bank"),
}
PAY_RULE = {
    "P1": "biweekly_friday_dec11", "P2": "biweekly_friday_dec11", "P3": "semimonthly_15_last",
    "P4": "biweekly_friday_dec11", "P5": "biweekly_friday_dec11", "P6": "monthly_1st",
    "S1": "none_into_cobalt", "S2": "none_into_cobalt", "S3": "rent_1st", "S4": "semimonthly_15_last",
    "S5": "none_into_cobalt", "S6": "biweekly_friday_dec11",
    "B1": "daily_sales", "B2": "daily_sales", "B3": "daily_sales", "B4": "daily_sales",
    "B5": "daily_sales", "B6": "daily_sales",
    "E1": "semimonthly_15_last", "E2": "none_into_cobalt", "E3": "biweekly_thursday",
    "E4": "biweekly_friday_dec11", "E5": "monthly_20th", "E6": "irregular",
}

# What each persona had riding on the migration weekend (Sat Dec 12 00:00 - Sun Dec 13 12:00 CT).
# The world turns these into what actually happened, given the offline card limit and any overrun.
# Types: autopay (scheduled payment; late fee if processed after a cutoff hour), p2p / transfer
# (fails during the window, goes out when the system returns), card_sales (tickets above the offline
# limit cannot be charged), card_purchase (one purchase above the limit is declined), settlement_delay.
MIGRATION_WEEKEND = {
    "P1": {"type": "autopay", "what": "rent", "amount": 1350, "scheduled": "Sunday 08:00", "late_after_hour": 18, "late_fee": 50},
    "P2": {"type": "p2p", "what": "the babysitter's pay", "amount": 120, "scheduled": "Sunday 09:00"},
    "P3": {"type": "none"},
    "P4": {"type": "autopay", "what": "car insurance", "amount": 210, "scheduled": "Sunday 06:00", "late_after_hour": 48, "late_fee": 0},
    "P5": {"type": "card_purchase", "what": "a $180 Christmas gift order at the mall on Saturday", "amount": 180},
    "P6": {"type": "none"},
    "S1": {"type": "none"},
    "S2": {"type": "none"},
    "S3": {"type": "transfer", "what": "a $2,400 payment to the furnace contractor", "amount": 2400, "scheduled": "Saturday 10:00"},
    "S4": {"type": "none"},
    "S5": {"type": "none"},
    "S6": {"type": "p2p", "what": "your share of a climbing-trip rental", "amount": 45, "scheduled": "Saturday 11:00"},
    "B1": {"type": "card_sales", "avg_ticket": 12, "tickets_over_100": 0, "tickets_over_250": 0,
           "then": {"type": "transfer", "what": "the Sunday restock payment to suppliers", "amount": 1800, "scheduled": "Sunday 09:00"}},
    "B2": {"type": "card_sales", "avg_ticket": 45, "tickets_over_100": 4, "over_100_avg": 140, "tickets_over_250": 0},
    "B3": {"type": "card_sales", "avg_ticket": 280, "tickets_over_100": 5, "over_100_avg": 280, "tickets_over_250": 2, "over_250_avg": 350},
    "B4": {"type": "p2p", "what": "the Sunday payouts to your four stylists", "amount": 1600, "scheduled": "Sunday 09:00"},
    "B5": {"type": "settlement_delay"},
    "B6": {"type": "none"},
    "E1": {"type": "card_purchase", "what": "a $140 lift ticket on Saturday", "amount": 140},
    "E2": {"type": "none"},
    "E3": {"type": "card_purchase", "what": "a $130 grocery run on Saturday", "amount": 130},
    "E4": {"type": "p2p", "what": "your rent share to your roommate", "amount": 650, "scheduled": "Sunday 10:00"},
    "E5": {"type": "none"},
    "E6": {"type": "transfer", "what": "moving a late client payment across to cover Monday's rent", "amount": 1400, "scheduled": "Sunday 11:00"},
}

# Engine network (code/sim/network.py format), derived from the same edges.
WHATSAPP_GROUPS = {
    "friends-chat": ["P1", "P5", "E4"],
    "vendors-chat": ["B1", "B5", "B3"],
    "tech-coworkers-chat": ["S2", "E1", "S6"],
    "parents-group-chat": ["S4", "E3", "P2"],
}
NO_SOCIAL = ["S1", "S5", "P6"]  # newsletters / TV / email people: they neither post nor read social feeds


def export_network(personas):
    """follows = in-group ties both ways; close_friends = the explicit bridges; groups = WhatsApp chats."""
    group_of = {p["id"]: p["group"] for p in personas}
    bridges = {tuple(sorted(b)) for b in BRIDGES}
    follows, friends = [], []
    for p in personas:
        for n in p["neighbors"]:
            pair = tuple(sorted((p["id"], n)))
            if pair in bridges:
                if pair[0] == p["id"]:
                    friends.append(list(pair))
            elif group_of[n] == p["group"] or p["influence"] == "follower":
                follows.append([p["id"], n])  # p sees n's posts
    return {"follows": sorted(follows), "close_friends": sorted(friends),
            "groups": WHATSAPP_GROUPS, "disabled_channels": {pid: ["social"] for pid in NO_SOCIAL}}


def build_network(personas, seed=SEED):
    rng = random.Random(seed)
    by_group = {}
    for p in personas:
        by_group.setdefault(p["group"], []).append(p["id"])
    edges = set()

    def add(a, b):
        if a != b:
            edges.add(tuple(sorted((a, b))))

    # 3 seeded in-group edges per persona
    for ids in by_group.values():
        for pid in ids:
            others = [o for o in ids if o != pid]
            rng.shuffle(others)
            for o in others[:3]:
                add(pid, o)
    # explicit cross-group bridges
    for a, b in BRIDGES:
        add(a, b)
    # leaders get up to 2 extra followers from other groups
    leaders = [p["id"] for p in personas if p["influence"] == "leader"]
    followers = [p["id"] for p in personas if p["influence"] == "follower"]
    group_of = {p["id"]: p["group"] for p in personas}
    def degree(pid):
        return sum(1 for e in edges if pid in e)

    for lid in leaders:
        pool = [f for f in followers if group_of[f] != group_of[lid] and degree(f) < 7]
        rng.shuffle(pool)
        for f in pool[:2]:
            add(lid, f)
    neighbors = {p["id"]: [] for p in personas}
    for a, b in sorted(edges):
        neighbors[a].append(b)
        neighbors[b].append(a)
    return {k: sorted(v) for k, v in neighbors.items()}


def finalize(personas):
    neighbors = build_network(personas)
    out = []
    for p in personas:
        q = dict(p)
        q["weight_deposits_usd"] = q["weight_customers"] * q["balance_usd"]
        q["neighbors"] = neighbors[q["id"]]
        q["wave"] = WAVE[q["influence"]]
        q["actions_available"] = ACTIONS
        rule = PAY_RULE[q["id"]]
        q["pay_rule"] = rule
        q["pay_weeks"], q["pay_schedule"] = PAY_RULES[rule]
        q["migration_weekend"] = MIGRATION_WEEKEND[q["id"]]
        out.append(q)
    return out


def validate(personas):
    problems = []
    ids = [p["id"] for p in personas]
    if len(ids) != len(set(ids)):
        problems.append("duplicate ids")
    if len(personas) < 24:
        problems.append(f"{len(personas)} personas (need >= 24)")
    groups = {}
    for p in personas:
        groups.setdefault(p["group"], []).append(p)
    if len(groups) < 3:
        problems.append("fewer than 3 groups")
    for g, ps in groups.items():
        if len(ps) < 4:
            problems.append(f"group {g!r} has {len(ps)} personas (need >= 4)")
        if g not in GROUP_CUSTOMERS:
            problems.append(f"group {g!r} is not a dossier group")
        else:
            got = sum(p["weight_customers"] for p in ps)
            if got != GROUP_CUSTOMERS[g]:
                problems.append(f"group {g!r} customers {got:,} != {GROUP_CUSTOMERS[g]:,}")
    total_c = sum(p["weight_customers"] for p in personas)
    total_d = sum(p["weight_deposits_usd"] for p in personas)
    savers_d = sum(p["weight_deposits_usd"] for p in personas if p["group"] == "savers with large balances")
    if total_c != TOTAL_CUSTOMERS:
        problems.append(f"total customers {total_c:,} != {TOTAL_CUSTOMERS:,}")
    if abs(total_d - TOTAL_DEPOSITS) / TOTAL_DEPOSITS > 0.02:
        problems.append(f"total deposits ${total_d/1e9:.2f}B not within 2% of $6.0B")
    if abs(savers_d - TOTAL_DEPOSITS / 2) / (TOTAL_DEPOSITS / 2) > 0.02:
        problems.append(f"savers deposits ${savers_d/1e9:.2f}B not within 2% of $3.0B")
    for p in personas:
        if not 3 <= len(p["neighbors"]) <= 8:
            problems.append(f"{p['id']} has {len(p['neighbors'])} neighbors")
        if p["wave"] not in (1, 2, 3):
            problems.append(f"{p['id']} bad wave")
    summary = {
        "personas": len(personas), "groups": {g: len(ps) for g, ps in groups.items()},
        "customers": total_c, "deposits_usd": total_d, "savers_deposits_usd": savers_d,
        "waves": {w: sum(1 for p in personas if p["wave"] == w) for w in (1, 2, 3)},
        "paid_fri_dec11": sum(1 for p in personas if p["paid_fri_dec11"]),
        "knows_fdic": sum(1 for p in personas if p["knows_fdic_limit"]),
        "main_bank": sum(1 for p in personas if p["cobalt_role"] == "main bank"),
        "avg_neighbors": round(sum(len(p["neighbors"]) for p in personas) / len(personas), 1),
    }
    return problems, summary


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="validate only, do not write")
    args = ap.parse_args()
    personas = finalize(PERSONAS)
    problems, summary = validate(personas)
    print(json.dumps(summary, indent=2))
    if problems:
        print("\n".join("FIX  " + p for p in problems))
        return 1
    if not args.check:
        with OUT.open("w", encoding="utf-8") as f:
            for p in personas:
                f.write(json.dumps(p, ensure_ascii=False) + "\n")
        print(f"wrote {OUT} ({len(personas)} personas)")
        network = export_network(personas)
        net_path = OUT.with_name("network.json")
        net_path.write_text(json.dumps(network, indent=1) + "\n", encoding="utf-8")
        print(f"wrote {net_path} ({len(network['follows'])} follows, {len(network['close_friends'])} close friends, "
              f"{len(network['groups'])} groups)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
