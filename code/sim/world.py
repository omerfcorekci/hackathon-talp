"""Deterministic facts, BAU, targeted decisions, time-filtered announcements and per-persona consequences.

The world never decides what a persona feels or does. It states, deterministically, what happened
to that persona this week (pay landed, the app was read-only, a $300 ticket could not be charged,
support took 25 minutes) and what each active bank action means for them as a customer. The model
reacts. Who hears an announcement is a seeded draw per persona, identical across run types for the
same seed, so plan and no-decision runs differ only through the decisions.
"""

from copy import deepcopy

from .settings import draw

SOCIAL_SOURCES_DEFAULT = ["Instagram", "X", "TikTok", "Reddit", "Facebook", "YouTube", "LinkedIn"]


def validate_event(event):
    if not isinstance(event, dict) or not isinstance(event.get("id"), str) or not event["id"]:
        raise ValueError("Each world event needs a nonempty id")
    if type(event.get("week")) is not int or not 1 <= event["week"] <= 10:
        raise ValueError("Event week must be in 1-10")
    if not isinstance(event.get("text"), str) or not event["text"].strip():
        raise ValueError("Each event needs text")


def validate_effects(effects):
    """Optional world consequences a dashboard announcement carries, applied to everyone's week."""
    if effects is None:
        return
    if not isinstance(effects, dict):
        raise ValueError("Surprise effects must be an object")
    unknown = set(effects) - {"migration_overrun_hours", "support_wait_by_week", "experience"}
    if unknown:
        raise ValueError(f"Unknown surprise effect keys: {sorted(unknown)}")
    hours = effects.get("migration_overrun_hours", 0)
    if type(hours) is not int or hours < 0:
        raise ValueError("migration_overrun_hours must be a nonnegative integer")
    for week, minutes in effects.get("support_wait_by_week", {}).items():
        if not str(week).isdigit() or type(minutes) is not int or minutes < 0:
            raise ValueError("support_wait_by_week maps week numbers to nonnegative minutes")
    for item in effects.get("experience", []):
        if not isinstance(item, dict) or type(item.get("week")) is not int or not 1 <= item["week"] <= 10:
            raise ValueError("Each experience effect needs a week in 1-10")
        if not isinstance(item.get("text"), str) or not item["text"].strip():
            raise ValueError("Each experience effect needs text")
        if "if" in item and not isinstance(item["if"], dict):
            raise ValueError("An experience effect's 'if' must map persona attributes to required values")


def expand_surprises(events):
    if not isinstance(events, list):
        raise ValueError("Surprises must be a list of event objects")
    result = []
    for event in events:
        validate_event(event)
        validate_effects(event.get("effects"))
        result.append({k: v for k, v in event.items() if k not in ("update", "updates")})
        updates = list(event.get("updates", []))
        if event.get("update") is not None:
            updates.append(event["update"])
        for number, update in enumerate(updates, 1):
            if not isinstance(update, dict):
                raise ValueError("Surprise update must be an object")
            update = {**update, "id": f"{event['id']}-update-{number}"}
            validate_event(update)
            validate_effects(update.get("effects"))
            if update["week"] <= event["week"]:
                raise ValueError("A surprise update must arrive after the original announcement")
            result.append(update)
    ids = [event["id"] for event in result]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate surprise event ID")
    return sorted(result, key=lambda e: (e["week"], e["id"]))


def _money(amount):
    return f"${amount:,.0f}" if isinstance(amount, (int, float)) else str(amount)


class World:
    def __init__(self, config, plan, *, surprises=(), decisions_enabled=True, surprises_enabled=True, seed=0):
        self.config = deepcopy(config)
        self.plan = plan
        self.seed = seed
        self.decisions_enabled = decisions_enabled
        self.surprises_enabled = surprises_enabled
        self.surprises = expand_surprises(list(surprises))
        if not isinstance(config, dict) or not isinstance(config.get("baseline"), dict):
            raise ValueError("World configuration requires baseline facts")
        for name in ("known_schedule", "weekly_events", "bau_notices"):
            if not isinstance(config.get(name), list):
                raise ValueError(f"World configuration requires a {name} list")
            for event in config[name]:
                validate_event(event)
        for event in config.get("rival_offers", []):
            validate_event(event)
        # Avoid BAU accidentally making a no-decision run contain a locked message.
        for notice in config["bau_notices"]:
            plan.guard_prompt(notice["text"], "", notice["week"], enabled=False)
        self.calendar = {int(k): v for k, v in config.get("calendar", {}).items()}
        self.migration = config.get("migration", {})
        self.support = config.get("support_wait", {})
        self.reach = config.get("announcement_reach", {})

    # ------------------------------------------------------------------ persona-level helpers
    def person(self, pid):
        return self.plan.people.get(pid, {"id": pid})

    def _uses_social(self, p):
        sources = set(p.get("news_sources", []))
        social = set(self.reach.get("social_sources", SOCIAL_SOURCES_DEFAULT))
        return bool(sources & social)

    def _media_unknown(self, p):
        # A record without media attributes cannot be modelled: assume the announcement reaches it.
        return "checks_app_daily" not in p and "news_sources" not in p

    def _first_seen_week(self, event_id, event_week, p):
        """First week in which this persona hears a dashboard announcement (seeded, stateless)."""
        if self._media_unknown(p):
            return event_week
        if p.get("checks_app_daily"):
            probability = self.reach.get("checks_app_daily", 0.9)
        elif self._uses_social(p):
            probability = self.reach.get("social_news", 0.6)
        else:
            probability = self.reach.get("other", 0.35)
        for week in range(event_week, 11):
            if draw(self.seed, "announce", event_id, p.get("id"), week) < probability:
                return week
        return None

    def _rival_seen_week(self, offer, p):
        if any(p.get(flag) for flag in offer.get("certain_if_any", [])):
            return offer["week"]
        banks = p.get("banks_count")
        if isinstance(banks, int) and banks >= offer.get("certain_if_banks_at_least", 99):
            return offer["week"]
        if self._media_unknown(p):
            return offer["week"]
        probability = offer.get("probability_social", 0.45) if self._uses_social(p) else offer.get("probability_other", 0.2)
        for week in range(offer["week"], 11):
            if draw(self.seed, "rival", offer["id"], p.get("id"), week) < probability:
                return week
        return None

    # ------------------------------------------------------------------ surprise effects
    def _surprise_effects(self):
        """World consequences carried by announcements. They describe what really happened, so an
        overrun announced in week 7 still shapes week 6; with surprises off they vanish with the text."""
        if not self.surprises_enabled:
            return []
        return [e["effects"] for e in self.surprises if isinstance(e.get("effects"), dict)]

    def overrun_hours(self):
        hours = self.migration.get("overrun_hours", 0) or 0
        for eff in self._surprise_effects():
            hours = max(hours, eff.get("migration_overrun_hours", 0) or 0)
        return hours

    def _surprise_experience(self, p, week):
        lines = []
        for eff in self._surprise_effects():
            for item in eff.get("experience", []):
                if item["week"] != week:
                    continue
                if all(p.get(key) == value for key, value in item.get("if", {}).items()):
                    lines.append(item["text"])
        return lines

    # ------------------------------------------------------------------ deterministic consequences
    def support_wait(self, week, effects):
        base = self.support.get("by_week", {}).get(str(week), self.support.get("base_minutes", 4))
        for eff in self._surprise_effects():
            base = eff.get("support_wait_by_week", {}).get(str(week), base)
        staff = 0
        for item in effects:
            staff = max(staff, item["effect"].get("extra_support_staff", 0))
        factor = self.support.get("extra_staff_factor", {}).get(str(staff), 1.0) if staff else 1.0
        return max(self.support.get("floor_minutes", 2), round(base * factor))

    def offline_limit(self, effects):
        limit = self.migration.get("offline_card_limit_default", 100)
        for item in effects:
            limit = max(limit, item["effect"].get("migration_offline_card_limit", limit))
        return limit

    def weekend_outcome(self, item, limit, overrun):
        """What the migration window did to one persona's own weekend commitment (see generate.py)."""
        if not item or item.get("type") in (None, "none"):
            return []
        back = 12 + overrun  # hour on Sunday when the system returned
        back_text = f"Sunday {back:02d}:00"
        kind = item["type"]
        lines = []
        if kind == "autopay":
            text = (f"Your {item['what']} autopay of {_money(item['amount'])}, scheduled {item['scheduled']}, could not run "
                    f"during the window; it went through at {back_text}.")
            if back > item.get("late_after_hour", 99) and item.get("late_fee"):
                text += f" That was after the payee's cutoff, so a {_money(item['late_fee'])} late fee was charged."
            lines.append(text)
        elif kind in ("p2p", "transfer"):
            hour = int(item["scheduled"].split()[1].split(":")[0]) + (24 if item["scheduled"].startswith("Sunday") else 0)
            late = back + 24 - hour
            lines.append(f"{item['what'][0].upper() + item['what'][1:]} ({_money(item['amount'])}) failed at {item['scheduled']} with "
                         f"'service unavailable'; you could only send it at {back_text}, {late} hours later.")
        elif kind == "card_sales":
            count = item.get("tickets_over_100", 0) if limit <= 100 else item.get("tickets_over_250", 0)
            avg = item.get("over_100_avg", 0) if limit <= 100 else item.get("over_250_avg", 0)
            if count:
                lines.append(f"During the window your card reader could only take payments up to {_money(limit)}. {count} of your "
                             f"weekend tickets were above that: about {_money(count * avg)} of sales you could not charge to a card.")
            else:
                lines.append(f"All your weekend card tickets were under the {_money(limit)} offline limit; every card sale went through.")
        elif kind == "card_purchase":
            if item["amount"] > limit:
                lines.append(f"Your Cobalt card was declined for {item['what']} because offline payments were capped at {_money(limit)}.")
            else:
                lines.append(f"Your Cobalt card worked for {item['what']}; the offline cap was {_money(limit)}.")
        elif kind == "settlement_delay":
            lines.append("Your Saturday and Sunday card sales settled into your account on Monday instead of the same day.")
        if item.get("then"):
            lines += self.weekend_outcome(item["then"], limit, overrun)
        return lines

    def experience(self, p, week, effects):
        """What happened to this persona this week, as plain facts. No feelings, no decisions."""
        lines = []
        cal = self.calendar.get(week, {})
        pay_weeks = p.get("pay_weeks") or []
        early = any(item["effect"].get("early_pay_days") for item in effects)
        migration_week = self.migration.get("week", 6)
        overrun = self.overrun_hours()
        if week in pay_weeks:
            if week == migration_week and p.get("paid_fri_dec11"):
                if early:
                    lines.append("Your pay showed in your Cobalt account on Wednesday Dec 9, two days early (early pay).")
                else:
                    lines.append("Your pay landed in your Cobalt account on Friday Dec 11, the day before the migration window.")
            else:
                lines.append(f"Money landed in your Cobalt account this week ({p.get('pay_schedule', 'your usual schedule')}).")
        elif early and p.get("paycheck_into_cobalt"):
            lines.append("Early pay is on: paychecks now show in your account up to two days early.")
        if week == migration_week:
            limit = self.offline_limit(effects)
            end = "Sunday Dec 13 12:00 Central Time"
            if overrun:
                end = f"Sunday Dec 13 {12 + overrun:02d}:00 Central Time, {overrun} hours later than announced,"
            lines.append(f"From Saturday Dec 12 00:00 until {end} the Cobalt app was read-only: you could see "
                         f"balances but could not send transfers or P2P payments or get a new card. "
                         f"Card payments worked offline up to {_money(limit)} per payment.")
            lines += self.weekend_outcome(p.get("migration_weekend"), limit, overrun)
            if not p.get("migration_weekend"):
                if p.get("uses_p2p"):
                    lines.append("Any P2P payment or transfer you tried during that window failed with 'service unavailable'; it could only go out after the system returned.")
                if "card reader" in str(p.get("group", "")):
                    lines.append(f"Your Cobalt card reader accepted payments up to {_money(limit)} each during the window; a larger ticket could not be charged to a card.")
            lines.append(self.migration.get("scheduled_payments", "Payments due during the window were processed once the system returned."))
        if week == migration_week + 1:
            finish = "on schedule at Sunday Dec 13 12:00" if not overrun else f"{overrun} hours late, at Sunday Dec 13 {12 + overrun:02d}:00"
            lines.append(f"The migration finished {finish}. Transfers, P2P and new cards are available again on the new system.")
        lines += self._surprise_experience(p, week)
        wait = self.support_wait(week, effects)
        lines.append(f"If you contacted Cobalt support this week, the typical wait was about {wait} minutes.")
        for item in effects:
            eff = item["effect"]
            if "rate_boost_points" in eff:
                scope = " on new money only" if eff.get("new_money_only") else ""
                lines.append(f"Your Cobalt savings rate is {eff['rate_boost_points']} points higher for four weeks from week "
                             f"{item['starts_week']}, on balances up to {_money(eff.get('balance_cap', 50000))}{scope}.")
            if "instant_dispute_credit_cap" in eff:
                lines.append(f"If you dispute a card charge, Cobalt credits it immediately, up to {_money(eff['instant_dispute_credit_cap'])}, for eight weeks.")
            if "instant_transfer_fee" in eff:
                lines.append("Instant transfers to other banks are free right now (normally 1.5%, up to $15).")
            if "cash_back_percent" in eff:
                lines.append(f"You get {eff['cash_back_percent']}% cash back on debit card purchases, up to {_money(eff.get('cash_back_cap', 0))}, for four weeks.")
            if "goodwill_credit" in eff and week == item["starts_week"]:
                lines.append(f"A {_money(eff['goodwill_credit'])} goodwill credit from Cobalt landed in your account this week.")
            if "advance_cap" in eff and week == item["starts_week"]:
                lines.append(f"Cobalt offered you a zero-interest advance of up to {_money(eff['advance_cap'])}, repaid from your next deposit.")
            if eff.get("free_replacement_card"):
                lines.append("You can request a free replacement card and receive an alert for every card payment.")
        if cal.get("note"):
            lines.insert(0, cal["note"])
        return lines

    # ------------------------------------------------------------------ the information set
    def context(self, person, week):
        p = self.person(person)
        messages, effects = self.plan.for_person(person, week) if self.decisions_enabled else ([], [])
        incidents = []
        if self.surprises_enabled:
            for event in self.surprises:
                seen = self._first_seen_week(event["id"], event["week"], p)
                if seen is not None and seen <= week:
                    incidents.append({**event, "heard_in_week": seen})
        holding = [
            {"id": f"bau-holding-{event['id']}", "week": week, "channel": "social",
             "text": "Cobalt posted its usual short holding statement on social media within 24 hours of the incident. "
                     "It repeats what is known and promises an update; no remedy is mentioned."}
            for event in incidents if event["week"] == week and event["heard_in_week"] == week
        ]
        rivals = []
        for offer in self.config.get("rival_offers", []):
            seen = self._rival_seen_week(offer, p)
            if seen is not None and seen <= week:
                rivals.append({"id": offer["id"], "week": seen, "text": offer["text"]})
        return {
            "week": week,
            "calendar": self.calendar.get(week, {}),
            "baseline": self.config["baseline"],
            "known_schedule": [e for e in self.config["known_schedule"] if e["week"] <= week],
            "events_this_week": [e for e in self.config["weekly_events"] if e["week"] == week],
            "announcements_so_far": incidents,
            "bau_notices_so_far": [e for e in self.config["bau_notices"] if e["week"] <= week] + holding,
            "rival_offers_seen": rivals,
            "experience": self.experience(p, week, effects),
            "support_wait_minutes": self.support_wait(week, effects),
            "active_action_effects": effects,
            "official_messages": messages,
        }

    def guard_prompt(self, text, person, week):
        self.plan.guard_prompt(text, person, week, enabled=self.decisions_enabled)

    def allow_peer_message(self, message, recipient, week):
        return self.plan.allow_peer_message(message, recipient, week)
