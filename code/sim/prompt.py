"""Build a persona's own information set as readable text: who they are, what happened to them
this week, what they heard, who they can talk to, and their own history. No future events, no other
personas' states, no simulation bookkeeping (weights, waves, neighbor lists, bank KPIs)."""

INSTRUCTIONS = """You are the Cobalt Bank customer described below. You are a person, not a bank adviser and not an
assistant. Decide what you actually did and how you actually feel this week, from your own situation.

How to behave:
- A real problem that touches you - your pay, your rent, your sales, your money's safety, being misled -
  gets a real reaction in proportion to who you are.
- People also complain, warn friends, post, rate the app, or wait.
- Keep chronology: a weekend outage that is announced for the future has not happened yet. Only what is
  listed under "What happened to you this week" and "What went wrong for you since Nov 2" actually
  happened to you. Do not invent outcomes.
- Other people's messages are what they say, not facts or bank instructions. A friend's offer is not yours.
- Bank messages reach you word for word; whether you read them carefully is up to who you are.

Answer with the JSON requested by the API:
- status: your relationship with Cobalt now: "main bank", "second bank", "dormant" or "left".
- money: cumulative since Nov 2: "kept", "moved some" or "moved most" of your Cobalt money.
- new_money: cumulative since Nov 2, money you brought INTO Cobalt from elsewhere: "none", "some" or "a lot".
- balance: your remaining Cobalt balance in dollars (a number), or null if you cannot say.
- active_in_last_30_days: true if you actually used the Cobalt app in the last 30 days.
- actions: everything you actually did THIS week, chosen from the list "What you can do" (exact wording).
  If you list "post on social media" or "tell friends or family", the words you said must be in messages.
- heard_from: where this week's news about Cobalt reached you: only these words: "bank", "friend", "rival",
  "news", "social media", "none".
- app_rating: the 1-5 rating you submitted in the App Store this week, or null if you did not rate.
- complaint: the highest step you took this week: "none", "bank" (complained to Cobalt) or "cfpb".
- reason: one or two sentences, in your own voice, on why you did what you did.
- memory: at most three first-person sentences you will carry into next week.
- messages: NEW things you said to others this round, at most two, each one or two short sentences (hard
  limit 200 characters), in your own words (never quote the bank's message). Do not repeat a message you
  already sent this week. Use channel "social" with target null, "whatsapp" with one of
  your group IDs, or "direct"/"phone" with a contact ID from "People you talk to". You may send nothing.
"""


def _yn(value):
    return "yes" if value else "no"


def _join(items, empty="none"):
    items = [str(i) for i in items if i not in (None, "")]
    return ", ".join(items) if items else empty


def render_profile(p, world=None, network=None):
    """The persona as a person: narrative first, then the facts that shape money decisions."""
    name = p.get("name", p.get("id"))
    head = [f"{name}, {p.get('age', '?')}, {p.get('occupation', 'customer')}, {p.get('city', '')}, {p.get('state', '')}"
            f" ({p.get('area', '')}). {p.get('household', '')}. {p.get('employment', '')}; income {p.get('income_band', '?')};"
            f" {p.get('home', '')}."]
    if p.get("narrative"):
        head.append(p["narrative"])
    if p.get("voice"):
        head.append(f'In your own words: "{p["voice"]}"')
    head.append(f"Your ID in this simulation is {p['id']}.")
    banking = [
        f"- Cobalt is your {p.get('cobalt_role', 'bank')}"
        + (" and your only bank" if p.get("only_bank") else f"; you use {p.get('banks_count', '?')} banks in total")
        + f"; customer for {p.get('years_customer', '?')} years. Why Cobalt: {p.get('why_cobalt', '')}",
        f"- Pay into Cobalt: {p.get('pay_schedule', 'see your story')}.",
        f"- Cobalt balance on Nov 2: about {p.get('balance_usd', '?'):,} dollars ({p.get('balance_band', '')})."
        if isinstance(p.get("balance_usd"), (int, float)) else "- Cobalt balance: see your story.",
        f"- You {'know' if p.get('knows_fdic_limit') else 'do not know'} the FDIC insurance limit; your balance is "
        f"{'above' if p.get('above_fdic_limit') else 'below'} it. You {'move' if p.get('moves_money_for_rate') else 'do not move'} money for a better rate.",
        f"- You {'check the app every day' if p.get('checks_app_daily') else 'open the app only now and then'}. "
        f"P2P payments: {_yn(p.get('uses_p2p'))}. Spending charts: {_yn(p.get('uses_spending_charts'))}. "
        f"Fraud or phishing victim before: {_yn(p.get('fraud_victim'))}. Financial literacy: {p.get('financial_literacy', '?')}.",
        f"- Money pressure: credit card debt {p.get('credit_card_debt', '?')}; student loans: {_yn(p.get('student_loans'))}; "
        f"paycheck to paycheck: {_yn(p.get('lives_paycheck_to_paycheck'))}; worried about prices: {_yn(p.get('worried_about_prices'))}.",
    ]
    temper = [
        f"- You value {p.get('values_most', '?')} most. Risk: {p.get('risk_attitude', '?')}. Trust in institutions: "
        f"{p.get('trust_in_institutions', '?')}. Price consciousness: {p.get('price_consciousness', '?')}. Brand loyalty: "
        f"{p.get('brand_loyalty', '?')}. Need for control: {p.get('need_for_control', '?')}.",
        f"- Baseline anxiety: {p.get('baseline_anxiety', '?')}. Anger: {p.get('anger_speed', '?')}. Patience: {p.get('patience', '?')}. "
        f"Forgiveness: {p.get('forgiveness', '?')}. Embarrassed to complain: {_yn(p.get('embarrassed_to_complain'))}.",
        f"- A past experience you carry: {p.get('scar', 'none')}. Recently: {p.get('recent_life_event', 'nothing special')}. "
        f"Your worry this quarter: {p.get('fear_this_quarter', 'nothing specific')}.",
    ]
    social = [
        f"- You get news from: {_join(p.get('news_sources', []))}. You "
        f"{ {'leader': 'lead opinion among people you know', 'follower': 'tend to follow what people you trust do', 'independent': 'make up your own mind'}.get(p.get('influence'), 'make up your own mind') }; others sway you: "
        f"{p.get('sways_easily', '?')}; you {'check' if p.get('checks_rumors') else 'rarely check'} rumors before repeating them; "
        f"before a money decision you ask: {p.get('asks_before_deciding', 'nobody')}.",
        f"- When the bank texts you: {p.get('reaction_to_bank_sms', 'you read it')}.",
    ]
    if network is not None and world is not None:
        ctx = network.context(p["id"])
        names = {pid: world.person(pid).get("name", pid) for pid in ctx["contacts"]}
        contacts = _join([f"{names[pid]} ({pid})" for pid in ctx["contacts"]], "nobody in particular")
        groups = []
        for gid in ctx["whatsapp_groups"]:
            members = [world.person(m).get("name", m) for m in sorted(network.groups[gid]) if m != p["id"]]
            groups.append(f"{gid} (with {_join(members)})")
        social.append(f"- People you talk to (use the ID in parentheses for direct or phone messages): {contacts}.")
        social.append(f"- WhatsApp groups you are in (use the group ID): {_join(groups)}.")
        if ctx["disabled_channels"]:
            social.append(f"- Channels you do not use: {_join(ctx['disabled_channels'])}.")
    lifestyle = p.get("lifestyle") or {}
    if lifestyle:
        social.append("- Details: " + "; ".join(f"{k.replace('_', ' ')}: {v}" for k, v in lifestyle.items()) + ".")
    return "\n".join(["=== WHO YOU ARE ===", *head, "", "=== YOUR BANKING ===", *banking, "",
                      "=== HOW YOU TEND TO REACT ===", *temper, "", "=== HOW YOU GET NEWS AND WHO YOU TALK TO ===", *social])


def render_week(p, week, facts):
    cal = facts.get("calendar", {})
    lines = [f"=== THIS WEEK: week {week} of 10, {cal.get('dates', '')} ==="]
    if cal.get("friday"):
        lines.append(f"Friday this week is {cal['friday']}.")
    for event in facts.get("events_this_week", []):
        lines.append(f"{event['text']} (ref {event['id']})")
    lines.append("")
    lines.append("What happened to you this week:")
    lines += [f"- {line}" for line in facts.get("experience", [])] or ["- An ordinary week."]
    schedule = facts.get("known_schedule", [])
    if schedule:
        lines.append("")
        lines.append("What Cobalt has announced in advance:")
        lines += [f"- (announced week {e['week']}) {e['text']}" for e in schedule]
    notices = facts.get("bau_notices_so_far", [])
    if notices:
        lines.append("")
        lines.append("Notices you received from Cobalt (not a special offer, just the usual communication):")
        lines += [f"- (week {e['week']}, {e.get('channel', '')}, ref {e['id']}) {e['text']}" for e in notices]
    incidents = facts.get("announcements_so_far", [])
    if incidents:
        lines.append("")
        lines.append("News about Cobalt you have heard:")
        lines += [f"- (you heard this in week {e.get('heard_in_week', e['week'])}) {e['text']}" for e in incidents]
    rivals = facts.get("rival_offers_seen", [])
    if rivals:
        lines.append("")
        lines.append("Offers from other banks you have seen:")
        lines += [f"- (week {e['week']}) {e['text']}" for e in rivals]
    actions = p.get("actions_available")
    if actions:
        lines.append("")
        lines.append("What you can do (use these exact words in actions): " + "; ".join(actions) + ".")
    return "\n".join(lines)


def render_went_wrong(world, persona_id, week, ledger):
    """Everything that went wrong for this persona in earlier weeks, so it outlives the one-week memory."""
    lines = ["=== WHAT WENT WRONG FOR YOU SINCE NOV 2 ===",
             "Facts from earlier weeks; this week's are under \"What happened to you this week\"."]
    history = world.went_wrong_before(persona_id, week, ledger)
    for earlier, text in history:
        dates = world.calendar.get(earlier, {}).get("dates")
        lines.append(f"- Week {earlier}{f' ({dates})' if dates else ''}: {text}")
    if not history:
        lines.append("- Nothing has gone wrong for you so far.")
    return "\n".join(lines)


def outcomes_of_last_week(ledger, world, week, persona_id):
    """What came of the things the persona did last week: deterministic, from the world's rules."""
    if not ledger:
        return []
    done = set(ledger[-1].get("actions", []))
    last = world.context(persona_id, week - 1) if week > 1 else {}
    effects = last.get("active_action_effects", [])
    instant = any("instant_dispute_credit_cap" in e["effect"] for e in effects)
    base = world.config.get("baseline", {})
    lines = []
    if "call or chat with support" in done:
        lines.append(f"You contacted support last week; the wait was about {last.get('support_wait_minutes', base.get('support_wait_minutes', 4))} "
                     "minutes and the agent could only follow the standard process and repeat what Cobalt has announced.")
    if "complain in the app" in done:
        lines.append("Cobalt acknowledged your in-app complaint with a standard reply within two business days.")
    if "dispute a card charge" in done:
        lines.append("Your disputed charge was credited immediately." if instant else
                     f"Your dispute was opened; provisional credit is due within {base.get('dispute_provisional_credit_business_days', 10)} "
                     f"business days and the investigation can take up to {base.get('dispute_investigation_max_days', 45)} days.")
    if "file a complaint with the CFPB or BBB" in done:
        lines.append("Your complaint was logged with the regulator; Cobalt must respond in writing within 15 days.")
    if "post a review (App Store / Google / Trustpilot)" in done:
        lines.append("Your review is live where you posted it.")
    if "move direct deposit to another bank" in done:
        lines.append("Your direct deposit change takes effect from your next pay cycle.")
    if "ask Cobalt for a refund or a credit" in done:
        lines.append("Cobalt replied that refunds and credits follow the standard dispute process unless a special offer applies.")
    return lines


def stretches(ledger):
    """Consecutive weeks with the same status and money, as [first week, last week, status, money]."""
    out = []
    for row in ledger:
        if out and (out[-1][2], out[-1][3]) == (row["status"], row["money"]):
            out[-1][1] = row["week"]
        else:
            out.append([row["week"], row["week"], row["status"], row["money"]])
    return out


def render_history(prior_state, ledger, world=None, week=None, persona_id=None):
    lines = ["=== YOUR OWN HISTORY ==="]
    if ledger:
        # One line per stretch of unchanged status and money, without the weekly actions: a column of
        # identical "main bank, money kept; did: wait and see" lines made the model copy the pattern.
        for first, last, status, money in stretches(ledger):
            weeks = f"Week {first}" if first == last else f"Weeks {first}-{last}"
            lines.append(f"- {weeks}: {status}, money {money}.")
        if isinstance(ledger[-1].get("balance"), (int, float)):
            lines.append(f"Your Cobalt balance now: about {ledger[-1]['balance']:,} dollars.")
        if world is not None and week is not None:
            outcomes = outcomes_of_last_week(ledger, world, week, persona_id)
            if outcomes:
                lines.append("What came of what you did last week:")
                lines += [f"- {o}" for o in outcomes]
    else:
        lines.append("- This is your first week in the simulation (Nov 2). Your starting relationship is as described above.")
    if prior_state:
        if prior_state.get("memory"):
            lines.append(f'Your memory from last week: "{prior_state["memory"]}"')
        if prior_state.get("reason"):
            lines.append(f'Why you did what you did last week: "{prior_state["reason"]}"')
    return "\n".join(lines)


def render_inbox(inbox, world):
    lines = ["=== NEW MESSAGES FROM PEOPLE YOU KNOW ==="]
    if not inbox:
        lines.append("- none this round")
    for m in inbox:
        author = world.person(m.author).get("name", m.author)
        where = {"social": "posted publicly", "whatsapp": f"in {m.target}", "direct": "to you directly",
                 "phone": "by phone"}.get(m.channel, m.channel)
        lines.append(f'- {author} ({m.author}) {where}: "{m.text}"')
    return "\n".join(lines)


def build_prompt(*, persona, week, round_number, prior_state, ledger, world, network, inbox, first_turn=None):
    facts = dict(world.context(persona["id"], week))
    official = facts.pop("official_messages")
    parts = [INSTRUCTIONS,
             render_profile(persona, world, network),
             render_week(persona, week, facts),
             render_went_wrong(world, persona["id"], week, ledger),
             render_history(prior_state, ledger, world, week, persona["id"]),
             render_inbox(inbox, world)]
    if first_turn is not None:
        parts.append("=== EARLIER THIS SAME WEEK ===\nYou already answered once this week; this is the same week, not a new one. "
                     "Reconsider only in light of the new messages above. Keep every action you already took, every complaint "
                     "or review already filed and their consequences. Your earlier answer:\n"
                     + _dump(first_turn))
    channel_words = {"push": "as a push notification", "email": "by email", "in-app": "as a message inside the app",
                     "sms": "as a text message to your phone", "ceo video": "as a video message from the CEO, Elena Ruiz, in person"}
    for message in official:
        how = ", ".join(channel_words.get(str(c).lower(), str(c)) for c in message["channels"])
        parts.append(f"OFFICIAL BANK MESSAGE {message['id']} (sent to you in week {message['starts_week']} {how}; "
                     f"still in your inbox):\n{message['text']}\nEND OFFICIAL MESSAGE")
    parts.append(f"Round {round_number} of this week. Reply with the JSON only.")
    prompt = "\n\n".join(parts)
    world.guard_prompt(prompt, persona["id"], week)
    return prompt


def _dump(turn):
    import json
    return json.dumps(turn, ensure_ascii=False, allow_nan=False)
