"""Business logic for nonprofit dashboards with RBAC."""
import re
from datetime import date, datetime, timedelta

from auth import get_auth_context
from repositories.donor_repo import DonorRepo
from repositories.metrics_repo import MetricsRepo
from repositories.nonprofit_repo import NonprofitRepo
from repositories.program_repo import ProgramRepo
from repositories.user_repo import UserRepo

nonprofit_repo = NonprofitRepo()
program_repo = ProgramRepo()
metrics_repo = MetricsRepo()
donor_repo = DonorRepo()
user_repo = UserRepo()

VALID_PROGRAM_STATUSES = ("active", "paused")


def _ctx():
    ctx = get_auth_context()
    if not ctx:
        raise ValueError("Authentication required")
    return ctx


def _is_platform_admin(ctx):
    return ctx["role"] == "platform_admin"


def _require_platform_admin():
    ctx = _ctx()
    if not _is_platform_admin(ctx):
        raise ValueError("Forbidden")
    return ctx


def _is_org_member_role(ctx):
    return ctx["role"] in ("nonprofit_user", "nonprofit_owner")


def _require_nonprofit_access(nonprofit_id):
    ctx = _ctx()
    if _is_platform_admin(ctx):
        return ctx
    if not _is_org_member_role(ctx):
        raise ValueError("Forbidden")
    if ctx.get("nonprofit_id") != nonprofit_id:
        raise ValueError("Forbidden")
    return ctx


def _can_manage_org_members(ctx, nonprofit_id):
    if _is_platform_admin(ctx):
        return True
    return ctx["role"] == "nonprofit_owner" and ctx.get("nonprofit_id") == nonprofit_id


def _require_manage_org_members(nonprofit_id):
    ctx = _ctx()
    if not _can_manage_org_members(ctx, nonprofit_id):
        raise ValueError("Forbidden")
    return ctx


ORG_MEMBER_ROLES = ("nonprofit_owner", "nonprofit_user")


def _nonprofit_ids_for_ctx(ctx):
    if _is_platform_admin(ctx):
        return [n["nonprofit_id"] for n in nonprofit_repo.list_all(include_inactive=True)]
    if ctx.get("nonprofit_id"):
        return [ctx["nonprofit_id"]]
    return []


def _slugify(name):
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return slug or "nonprofit"


def _serialize_nonprofit(doc):
    return {
        "nonprofitId": doc["nonprofit_id"],
        "name": doc["name"],
        "slug": doc["slug"],
        "mission": doc.get("mission", ""),
        "location": doc.get("location", ""),
        "referenceCode": doc.get("reference_code", ""),
        "sourceCode": doc.get("source_code", ""),
        "isActive": doc.get("is_active", True),
        "createdAt": doc.get("created_at").isoformat() if doc.get("created_at") else None,
    }


def _serialize_program(doc):
    return {
        "programId": doc["program_id"],
        "nonprofitId": doc["nonprofit_id"],
        "name": doc["name"],
        "status": doc["status"],
        "participants": doc.get("participants", 0),
        "budget": doc.get("budget", 0),
    }


def _serialize_donor(doc):
    return {
        "donorId": doc["donor_id"],
        "name": doc["name"],
        "email": doc.get("email", ""),
        "donationAmount": float(doc.get("donation_amount") or 0),
    }


def _email_trend(change):
    if change > 0:
        return "up"
    if change < 0:
        return "down"
    return "flat"


def _serialize_insights(metrics):
    change = int(metrics.get("email_opens_change") or 0)
    return {
        "highestDonation": float(metrics.get("highest_donation") or 0),
        "biggestDonorName": metrics.get("biggest_donor_name") or "",
        "emailOpensCurrent": int(metrics.get("email_opens_current") or 0),
        "emailOpensPrevious": int(metrics.get("email_opens_previous") or 0),
        "emailOpensChange": change,
        "emailOpensChangePct": float(metrics.get("email_opens_change_pct") or 0),
        "emailOpensTrend": _email_trend(change),
    }


def _serialize_metrics(doc):
    goal = float(doc.get("funding_goal") or 0)
    raised = float(doc.get("funding_raised") or 0)
    progress = round((raised / goal) * 100, 1) if goal > 0 else 0.0
    return {
        "donorCount": int(doc.get("donor_count") or 0),
        "totalDonations": float(doc.get("total_donations") or 0),
        "activeVolunteers": int(doc.get("active_volunteers") or 0),
        "volunteerHours": int(doc.get("volunteer_hours") or 0),
        "fundingGoal": goal,
        "fundingRaised": raised,
        "grantsReceived": float(doc.get("grants_received") or 0),
        "fundingProgress": progress,
        "emailOpensCurrent": int(doc.get("email_opens_current") or 0),
        "emailOpensPrevious": int(doc.get("email_opens_previous") or 0),
        "highestDonation": float(doc.get("highest_donation") or 0),
        "biggestDonorName": doc.get("biggest_donor_name") or "",
        "emailOpensChange": int(doc.get("email_opens_change") or 0),
        "emailOpensChangePct": float(doc.get("email_opens_change_pct") or 0),
        "p2pMessagesSent": int(doc.get("p2p_messages_sent") or 0),
        "p2pResponses": int(doc.get("p2p_responses") or 0),
        "p2pOptOuts": int(doc.get("p2p_opt_outs") or 0),
        "p2pResponseRate": float(doc.get("p2p_response_rate") or 0),
        "callHours": float(doc.get("call_hours") or 0),
        "callsMade": int(doc.get("calls_made") or 0),
        "contactsReached": int(doc.get("contacts_reached") or 0),
        "callAvgDurationMinutes": float(doc.get("call_avg_duration_minutes") or 0),
        "updatedAt": doc.get("updated_at").isoformat() if doc.get("updated_at") else None,
    }


def _channel_donation_stats(raised, count, total):
    raised = float(raised or 0)
    count = int(count or 0)
    total = float(total or 0)
    avg_gift = round(raised / count, 2) if count > 0 else 0.0
    share = round((raised / total) * 100, 1) if total > 0 else 0.0
    return {
        "donationsRaised": raised,
        "donationCount": count,
        "avgGift": avg_gift,
        "shareOfTotal": share,
    }


def _serialize_donation_channels(metrics):
    total = float(metrics.get("total_donations") or 0)
    email = float(metrics.get("email_donations") or 0)
    p2p = float(metrics.get("p2p_donations") or 0)
    call = float(metrics.get("call_donations") or 0)
    other = max(total - email - p2p - call, 0.0)
    return {
        "email": email,
        "p2pTexting": p2p,
        "callTime": call,
        "other": other,
        "total": total,
    }


def _serialize_categories(metrics, donors):
    change = int(metrics.get("email_opens_change") or 0)
    total = float(metrics.get("total_donations") or 0)
    email_donations = _channel_donation_stats(
        metrics.get("email_donations"),
        metrics.get("email_donation_count"),
        total,
    )
    p2p_donations = _channel_donation_stats(
        metrics.get("p2p_donations"),
        metrics.get("p2p_donation_count"),
        total,
    )
    call_donations = _channel_donation_stats(
        metrics.get("call_donations"),
        metrics.get("call_donation_count"),
        total,
    )
    channel_breakdown = _serialize_donation_channels(metrics)
    return {
        "email": {
            "opensCurrent": int(metrics.get("email_opens_current") or 0),
            "opensPrevious": int(metrics.get("email_opens_previous") or 0),
            "opensChange": change,
            "opensChangePct": float(metrics.get("email_opens_change_pct") or 0),
            "trend": _email_trend(change),
            **email_donations,
        },
        "p2pTexting": {
            "messagesSent": int(metrics.get("p2p_messages_sent") or 0),
            "responses": int(metrics.get("p2p_responses") or 0),
            "optOuts": int(metrics.get("p2p_opt_outs") or 0),
            "responseRate": float(metrics.get("p2p_response_rate") or 0),
            **p2p_donations,
        },
        "callTime": {
            "totalHours": float(metrics.get("call_hours") or 0),
            "callsMade": int(metrics.get("calls_made") or 0),
            "contactsReached": int(metrics.get("contacts_reached") or 0),
            "avgDurationMinutes": float(metrics.get("call_avg_duration_minutes") or 0),
            **call_donations,
        },
        "donors": {
            "donorCount": int(metrics.get("donor_count") or 0),
            "totalDonations": total,
            "highestDonation": float(metrics.get("highest_donation") or 0),
            "biggestDonorName": metrics.get("biggest_donor_name") or "",
            "donors": [_serialize_donor(d) for d in donors],
            "channelBreakdown": channel_breakdown,
        },
    }


def _wow_change(current, previous):
    current_val = float(current or 0)
    previous_val = float(previous or 0)
    change = current_val - previous_val
    if previous_val > 0:
        change_pct = round((change / previous_val) * 100, 1)
    elif current_val > 0:
        change_pct = 100.0
    else:
        change_pct = 0.0
    if change > 0:
        trend = "up"
    elif change < 0:
        trend = "down"
    else:
        trend = "flat"
    return {
        "current": current_val,
        "previous": previous_val,
        "change": change,
        "changePct": change_pct,
        "trend": trend,
    }


def _format_week_label(week_start_iso):
    start = date.fromisoformat(week_start_iso)
    end = start + timedelta(days=6)
    if start.month == end.month:
        return f"{start.strftime('%b %d')} – {end.strftime('%d, %Y')}"
    return f"{start.strftime('%b %d')} – {end.strftime('%b %d, %Y')}"


def _format_week_report_label(week_start_iso):
    start = date.fromisoformat(week_start_iso)
    end = start + timedelta(days=6)
    if start.month == end.month:
        return f"Week of {start.strftime('%b %d')} – {end.strftime('%d, %Y')}"
    return f"Week of {start.strftime('%b %d')} – {end.strftime('%b %d, %Y')}"


def _parse_week_start(week_start):
    if not week_start:
        return None
    try:
        parsed = date.fromisoformat(str(week_start)[:10])
    except ValueError as exc:
        raise ValueError("Invalid weekStart") from exc
    if parsed.weekday() != 0:
        raise ValueError("Invalid weekStart; must be a Monday (ISO date)")
    return parsed.isoformat()


def _week_info(snapshot):
    return {
        "weekStart": snapshot["weekStart"],
        "weekEnd": snapshot["weekEnd"],
        "label": snapshot["label"],
        "reportLabel": _format_week_report_label(snapshot["weekStart"]),
    }


def _serialize_weekly_snapshot(doc):
    week_start = doc.get("week_start", "")
    if isinstance(week_start, datetime):
        week_start = week_start.date().isoformat()
    elif hasattr(week_start, "isoformat"):
        week_start = week_start.isoformat()
    start = date.fromisoformat(str(week_start)[:10])
    end = start + timedelta(days=6)
    return {
        "weekStart": str(week_start)[:10],
        "weekEnd": end.isoformat(),
        "label": _format_week_label(str(week_start)[:10]),
        "emailOpens": int(doc.get("email_opens") or 0),
        "p2pMessagesSent": int(doc.get("p2p_messages_sent") or 0),
        "p2pResponses": int(doc.get("p2p_responses") or 0),
        "p2pOptOuts": int(doc.get("p2p_opt_outs") or 0),
        "callHours": float(doc.get("call_hours") or 0),
        "callsMade": int(doc.get("calls_made") or 0),
        "contactsReached": int(doc.get("contacts_reached") or 0),
        "donationsTotal": float(doc.get("donations_total") or 0),
        "emailDonations": float(doc.get("email_donations") or 0),
        "p2pDonations": float(doc.get("p2p_donations") or 0),
        "callDonations": float(doc.get("call_donations") or 0),
        "donorCount": int(doc.get("donor_count") or 0),
        "activeVolunteers": int(doc.get("active_volunteers") or 0),
        "volunteerHours": int(doc.get("volunteer_hours") or 0),
        "fundingRaised": float(doc.get("funding_raised") or 0),
    }


def _build_weekly_comparisons(latest, prior):
    if not latest or not prior:
        return {}
    pairs = (
        ("emailOpens", "emailOpens"),
        ("p2pMessagesSent", "p2pMessagesSent"),
        ("p2pResponses", "p2pResponses"),
        ("p2pOptOuts", "p2pOptOuts"),
        ("callHours", "callHours"),
        ("callsMade", "callsMade"),
        ("contactsReached", "contactsReached"),
        ("donationsTotal", "donationsTotal"),
        ("emailDonations", "emailDonations"),
        ("p2pDonations", "p2pDonations"),
        ("callDonations", "callDonations"),
        ("donorCount", "donorCount"),
        ("activeVolunteers", "activeVolunteers"),
        ("volunteerHours", "volunteerHours"),
        ("fundingRaised", "fundingRaised"),
    )
    return {
        key: _wow_change(latest.get(field), prior.get(field))
        for key, field in pairs
    }


def _wow_phrase(label, comparison, *, unit="", is_money=False, is_int=True):
    trend = comparison.get("trend", "flat")
    current = comparison.get("current", 0)
    previous = comparison.get("previous", 0)
    change_pct = comparison.get("changePct", 0)
    sign = "+" if comparison.get("change", 0) > 0 else ""

    def fmt(val):
        if is_money:
            return f"${val:,.2f}"
        if is_int:
            return f"{int(val):,}"
        return f"{val:,.1f}"

    cur_s = fmt(current)
    prev_s = fmt(previous)
    suffix = f" {unit}".strip()

    if trend == "up":
        verb = "increased"
    elif trend == "down":
        verb = "decreased"
    else:
        return f"{label} held steady week-over-week at {cur_s}{suffix} (prior week: {prev_s}{suffix})."

    return (
        f"{label} {verb} {abs(change_pct)}% week-over-week "
        f"({prev_s}{suffix} -> {cur_s}{suffix}, {sign}{comparison.get('change', 0):,.0f}{suffix})."
    )


def _build_weekly_narratives(comparisons, categories):
    if not comparisons:
        return []

    summaries = []
    if "emailOpens" in comparisons:
        summaries.append(_wow_phrase("Email opens", comparisons["emailOpens"]))

    email_cat = categories.get("email") or {}
    if email_cat.get("donationsRaised", 0) > 0:
        summaries.append(
            f"Email-channel fundraising raised ${email_cat['donationsRaised']:,.2f} this week "
            f"across {email_cat.get('donationCount', 0):,} gifts "
            f"({email_cat.get('shareOfTotal', 0)}% of weekly donations)."
        )

    if "p2pMessagesSent" in comparisons:
        summaries.append(_wow_phrase("P2P messages sent", comparisons["p2pMessagesSent"]))
    p2p = categories.get("p2pTexting") or {}
    if p2p.get("responseRate", 0) > 0:
        summaries.append(
            f"P2P texting response rate is {p2p['responseRate']}% "
            f"({p2p.get('responses', 0):,} responses, {p2p.get('optOuts', 0):,} opt-outs)."
        )

    if "callHours" in comparisons:
        summaries.append(_wow_phrase("Call-time hours", comparisons["callHours"], is_int=False))
    call = categories.get("callTime") or {}
    if call.get("callsMade", 0) > 0:
        summaries.append(
            f"Call program reached {call.get('contactsReached', 0):,} contacts "
            f"from {call.get('callsMade', 0):,} calls (avg {call.get('avgDurationMinutes', 0)} min)."
        )

    if "donationsTotal" in comparisons:
        summaries.append(_wow_phrase("Weekly donations", comparisons["donationsTotal"], is_money=True, is_int=False))
    if "fundingRaised" in comparisons:
        summaries.append(_wow_phrase("Funding raised", comparisons["fundingRaised"], is_money=True, is_int=False))
    if "activeVolunteers" in comparisons:
        summaries.append(_wow_phrase("Active volunteers", comparisons["activeVolunteers"]))

    return summaries


def _weekly_donation_count(weekly_amount, aggregate_amount, aggregate_count):
    weekly_amount = float(weekly_amount or 0)
    aggregate_amount = float(aggregate_amount or 0)
    aggregate_count = int(aggregate_count or 0)
    if aggregate_amount <= 0 or weekly_amount <= 0:
        return 0
    return max(1, int(round(aggregate_count * weekly_amount / aggregate_amount)))


def _categories_from_weekly_snapshot(selected, prior, donors, aggregate_metrics):
    opens_current = int(selected.get("emailOpens") or 0)
    opens_previous = int(prior.get("emailOpens") or 0) if prior else 0
    change = opens_current - opens_previous
    change_pct = round((change / opens_previous) * 100, 1) if opens_previous > 0 else 0.0

    total = float(selected.get("donationsTotal") or 0)
    email_amt = float(selected.get("emailDonations") or 0)
    p2p_amt = float(selected.get("p2pDonations") or 0)
    call_amt = float(selected.get("callDonations") or 0)

    email_donations = _channel_donation_stats(
        email_amt,
        _weekly_donation_count(email_amt, aggregate_metrics.get("email_donations"), aggregate_metrics.get("email_donation_count")),
        total,
    )
    p2p_donations = _channel_donation_stats(
        p2p_amt,
        _weekly_donation_count(p2p_amt, aggregate_metrics.get("p2p_donations"), aggregate_metrics.get("p2p_donation_count")),
        total,
    )
    call_donations = _channel_donation_stats(
        call_amt,
        _weekly_donation_count(call_amt, aggregate_metrics.get("call_donations"), aggregate_metrics.get("call_donation_count")),
        total,
    )

    other = max(total - email_amt - p2p_amt - call_amt, 0.0)
    channel_breakdown = {
        "email": email_amt,
        "p2pTexting": p2p_amt,
        "callTime": call_amt,
        "other": other,
        "total": total,
    }

    messages_sent = int(selected.get("p2pMessagesSent") or 0)
    responses = int(selected.get("p2pResponses") or 0)
    response_rate = round((responses / messages_sent) * 100, 1) if messages_sent > 0 else 0.0

    return {
        "email": {
            "opensCurrent": opens_current,
            "opensPrevious": opens_previous,
            "opensChange": change,
            "opensChangePct": change_pct,
            "trend": _email_trend(change),
            **email_donations,
        },
        "p2pTexting": {
            "messagesSent": messages_sent,
            "responses": responses,
            "optOuts": int(selected.get("p2pOptOuts") or 0),
            "responseRate": response_rate,
            **p2p_donations,
        },
        "callTime": {
            "totalHours": float(selected.get("callHours") or 0),
            "callsMade": int(selected.get("callsMade") or 0),
            "contactsReached": int(selected.get("contactsReached") or 0),
            "avgDurationMinutes": float(aggregate_metrics.get("call_avg_duration_minutes") or 0),
            **call_donations,
        },
        "donors": {
            "donorCount": int(selected.get("donorCount") or 0),
            "totalDonations": total,
            "highestDonation": float(aggregate_metrics.get("highest_donation") or 0),
            "biggestDonorName": aggregate_metrics.get("biggest_donor_name") or "",
            "donors": [_serialize_donor(d) for d in donors],
            "channelBreakdown": channel_breakdown,
        },
    }


def _summary_from_weekly_snapshot(selected, active_programs, total_programs):
    return {
        "donorCount": int(selected.get("donorCount") or 0),
        "totalDonations": float(selected.get("donationsTotal") or 0),
        "activeVolunteers": int(selected.get("activeVolunteers") or 0),
        "volunteerHours": int(selected.get("volunteerHours") or 0),
        "activePrograms": active_programs,
        "totalPrograms": total_programs,
    }


def _insights_from_weekly_snapshot(selected, prior, aggregate_metrics):
    opens_current = int(selected.get("emailOpens") or 0)
    opens_previous = int(prior.get("emailOpens") or 0) if prior else 0
    change = opens_current - opens_previous
    change_pct = round((change / opens_previous) * 100, 1) if opens_previous > 0 else 0.0
    return {
        "highestDonation": float(aggregate_metrics.get("highest_donation") or 0),
        "biggestDonorName": aggregate_metrics.get("biggest_donor_name") or "",
        "emailOpensCurrent": opens_current,
        "emailOpensPrevious": opens_previous,
        "emailOpensChange": change,
        "emailOpensChangePct": change_pct,
        "emailOpensTrend": _email_trend(change),
    }


def _build_weekly_metrics_payload(nonprofit_id, week_start=None):
    docs = metrics_repo.list_weekly(nonprofit_id, limit=6)
    if not docs:
        return None

    history_newest_first = [_serialize_weekly_snapshot(d) for d in docs]
    history_chrono = list(reversed(history_newest_first))
    available_weeks = [_week_info(row) for row in history_chrono]

    parsed_week = _parse_week_start(week_start)
    if parsed_week:
        selected = next((row for row in history_chrono if row["weekStart"] == parsed_week), None)
        if not selected:
            raise ValueError("Invalid weekStart; no snapshot for that week")
    else:
        selected = history_chrono[-1] if history_chrono else None

    prior = None
    if selected:
        idx = next(i for i, row in enumerate(history_chrono) if row["weekStart"] == selected["weekStart"])
        if idx > 0:
            prior = history_chrono[idx - 1]

    comparisons = _build_weekly_comparisons(selected, prior)

    return {
        "selectedWeekStart": selected["weekStart"] if selected else None,
        "availableWeeks": available_weeks,
        "reportingWeek": _week_info(selected) if selected else None,
        "priorWeek": _week_info(prior) if prior else None,
        "history": history_chrono,
        "comparisons": comparisons,
        "summaries": [],
    }


def list_nonprofits():
    ctx = _ctx()
    ids = _nonprofit_ids_for_ctx(ctx)
    if not ids:
        return []
    docs = nonprofit_repo.list_by_ids(ids)
    return [_serialize_nonprofit(d) for d in docs]


def create_nonprofit(name, mission, location, slug=None):
    ctx = _ctx()
    if not _is_platform_admin(ctx):
        raise ValueError("Forbidden")
    if not name or not name.strip():
        raise ValueError("name is required")
    slug = (slug or _slugify(name)).strip()
    if nonprofit_repo.get_by_slug(slug):
        raise ValueError("slug already in use")
    doc = nonprofit_repo.add(name.strip(), slug, (mission or "").strip(), (location or "").strip())
    metrics_repo.upsert(doc["nonprofit_id"], {})
    return _serialize_nonprofit(doc)


def get_nonprofit(nonprofit_id):
    _require_nonprofit_access(nonprofit_id)
    doc = nonprofit_repo.get_by_id(nonprofit_id)
    if not doc:
        raise ValueError("Nonprofit not found")
    return _serialize_nonprofit(doc)


def update_nonprofit(nonprofit_id, updates):
    ctx = _require_nonprofit_access(nonprofit_id)
    if not _is_platform_admin(ctx):
        allowed = {"mission", "location"}
        updates = {k: v for k, v in updates.items() if k in allowed}
    mapping = {
        "name": "name",
        "slug": "slug",
        "mission": "mission",
        "location": "location",
        "isActive": "is_active",
        "referenceCode": "reference_code",
        "sourceCode": "source_code",
    }
    payload = {}
    for src, dest in mapping.items():
        if src in updates and updates[src] is not None:
            payload[dest] = updates[src]
    doc = nonprofit_repo.update(nonprofit_id, payload)
    if not doc:
        raise ValueError("Nonprofit not found")
    return _serialize_nonprofit(doc)


def get_dashboard(nonprofit_id, week_start=None):
    _require_nonprofit_access(nonprofit_id)
    nonprofit = nonprofit_repo.get_by_id(nonprofit_id)
    if not nonprofit:
        raise ValueError("Nonprofit not found")
    metrics = metrics_repo.get_for_nonprofit(nonprofit_id)
    programs = program_repo.list_for_nonprofit(nonprofit_id)
    donors = donor_repo.list_for_nonprofit(nonprofit_id, limit=10)
    active_programs = sum(1 for p in programs if p.get("status") == "active")
    total_programs = len(programs)

    weekly_metrics = _build_weekly_metrics_payload(nonprofit_id, week_start=week_start)
    view_mode = "aggregate"
    categories = _serialize_categories(metrics, donors)
    summary = {
        "donorCount": int(metrics.get("donor_count") or 0),
        "totalDonations": float(metrics.get("total_donations") or 0),
        "activeVolunteers": int(metrics.get("active_volunteers") or 0),
        "volunteerHours": int(metrics.get("volunteer_hours") or 0),
        "activePrograms": active_programs,
        "totalPrograms": total_programs,
    }
    insights = _serialize_insights(metrics)
    serialized_metrics = _serialize_metrics(metrics)
    donation_channels = _serialize_donation_channels(metrics)

    if weekly_metrics and weekly_metrics.get("reportingWeek"):
        selected_start = weekly_metrics["selectedWeekStart"]
        history = weekly_metrics["history"]
        selected = next((row for row in history if row["weekStart"] == selected_start), None)
        prior = None
        prior_week = weekly_metrics.get("priorWeek")
        if prior_week and selected:
            prior = next((row for row in history if row["weekStart"] == prior_week["weekStart"]), None)
        if selected:
            view_mode = "weekly"
            categories = _categories_from_weekly_snapshot(selected, prior, donors, metrics)
            summary = _summary_from_weekly_snapshot(selected, active_programs, total_programs)
            insights = _insights_from_weekly_snapshot(selected, prior, metrics)
            donation_channels = categories["donors"]["channelBreakdown"]
            goal = float(metrics.get("funding_goal") or 0)
            raised = float(selected.get("fundingRaised") or 0)
            serialized_metrics = {
                **serialized_metrics,
                "fundingRaised": raised,
                "fundingProgress": round((raised / goal) * 100, 1) if goal > 0 else 0.0,
                "emailOpensCurrent": selected["emailOpens"],
                "emailOpensPrevious": prior["emailOpens"] if prior else 0,
            }
            weekly_metrics["summaries"] = _build_weekly_narratives(weekly_metrics["comparisons"], categories)

    return {
        "nonprofit": _serialize_nonprofit(nonprofit),
        "viewMode": view_mode,
        "selectedWeekStart": weekly_metrics.get("selectedWeekStart") if weekly_metrics else None,
        "summary": summary,
        "metrics": serialized_metrics,
        "insights": insights,
        "categories": categories,
        "donationChannels": donation_channels,
        "donors": [_serialize_donor(d) for d in donors],
        "programs": [_serialize_program(p) for p in programs],
        "weeklyMetrics": weekly_metrics,
    }


def update_metrics(nonprofit_id, data):
    _require_platform_admin()
    _require_nonprofit_access(nonprofit_id)
    if not nonprofit_repo.get_by_id(nonprofit_id):
        raise ValueError("Nonprofit not found")
    mapping = {
        "donorCount": "donor_count",
        "totalDonations": "total_donations",
        "activeVolunteers": "active_volunteers",
        "volunteerHours": "volunteer_hours",
        "fundingGoal": "funding_goal",
        "fundingRaised": "funding_raised",
        "grantsReceived": "grants_received",
        "emailOpensCurrent": "email_opens_current",
        "emailOpensPrevious": "email_opens_previous",
        "p2pMessagesSent": "p2p_messages_sent",
        "p2pResponses": "p2p_responses",
        "p2pOptOuts": "p2p_opt_outs",
        "callHours": "call_hours",
        "callsMade": "calls_made",
        "contactsReached": "contacts_reached",
        "callAvgDurationMinutes": "call_avg_duration_minutes",
        "emailDonations": "email_donations",
        "emailDonationCount": "email_donation_count",
        "p2pDonations": "p2p_donations",
        "p2pDonationCount": "p2p_donation_count",
        "callDonations": "call_donations",
        "callDonationCount": "call_donation_count",
    }
    updates = {}
    for camel, snake in mapping.items():
        if camel in data:
            updates[snake] = data[camel]
    doc = metrics_repo.upsert(nonprofit_id, updates)
    doc = metrics_repo.recompute_highlights(nonprofit_id)
    return _serialize_metrics(doc)


def list_programs(nonprofit_id):
    _require_nonprofit_access(nonprofit_id)
    return [_serialize_program(p) for p in program_repo.list_for_nonprofit(nonprofit_id)]


def create_program(nonprofit_id, name, status, participants, budget):
    _require_platform_admin()
    _require_nonprofit_access(nonprofit_id)
    if not nonprofit_repo.get_by_id(nonprofit_id):
        raise ValueError("Nonprofit not found")
    if not name or not name.strip():
        raise ValueError("name is required")
    status = (status or "active").lower()
    if status not in VALID_PROGRAM_STATUSES:
        raise ValueError("status must be active or paused")
    doc = program_repo.add(
        nonprofit_id,
        name.strip(),
        status,
        int(participants or 0),
        float(budget or 0),
    )
    return _serialize_program(doc)


def update_program(nonprofit_id, program_id, updates):
    _require_platform_admin()
    _require_nonprofit_access(nonprofit_id)
    program = program_repo.get_by_id(program_id)
    if not program or program["nonprofit_id"] != nonprofit_id:
        raise ValueError("Program not found")
    status = updates.get("status")
    if status is not None:
        status = status.lower()
        if status not in VALID_PROGRAM_STATUSES:
            raise ValueError("status must be active or paused")
    payload = {}
    if "name" in updates:
        payload["name"] = updates["name"]
    if status is not None:
        payload["status"] = status
    if "participants" in updates:
        payload["participants"] = int(updates["participants"])
    if "budget" in updates:
        payload["budget"] = float(updates["budget"])
    doc = program_repo.update(program_id, payload)
    return _serialize_program(doc)


def delete_program(nonprofit_id, program_id):
    _require_platform_admin()
    _require_nonprofit_access(nonprofit_id)
    program = program_repo.get_by_id(program_id)
    if not program or program["nonprofit_id"] != nonprofit_id:
        raise ValueError("Program not found")
    if not program_repo.delete(program_id):
        raise ValueError("Program not found")
    return {"deleted": True}


def list_users():
    ctx = _ctx()
    if not _is_platform_admin(ctx):
        raise ValueError("Forbidden")
    users = user_repo.get_all_users()
    return [
        {
            "userId": u["user_id"],
            "name": u["name"],
            "email": u["email"],
            "role": u.get("role", "nonprofit_user"),
            "nonprofitId": u.get("nonprofit_id"),
            "isDeleted": u.get("is_deleted", False),
        }
        for u in users
        if not u.get("is_deleted")
    ]


def list_nonprofits_public():
    docs = nonprofit_repo.list_all()
    return [
        {
            "nonprofitId": d["nonprofit_id"],
            "name": d["name"],
            "location": d.get("location", ""),
        }
        for d in docs
    ]


def _serialize_org_member(user):
    return {
        "userId": user["user_id"],
        "name": user["name"],
        "email": user["email"],
        "role": user.get("role", "nonprofit_user"),
    }


def _ensure_nonprofit_exists(nonprofit_id):
    if not nonprofit_repo.get_by_id(nonprofit_id):
        raise ValueError("Nonprofit not found")


def _validate_org_member_role(role):
    if role not in ORG_MEMBER_ROLES:
        raise ValueError("Invalid role; use nonprofit_owner or nonprofit_user")


def list_org_members(nonprofit_id):
    _require_nonprofit_access(nonprofit_id)
    _ensure_nonprofit_exists(nonprofit_id)
    users = user_repo.list_for_nonprofit(nonprofit_id)
    return [_serialize_org_member(u) for u in users]


def create_org_member(nonprofit_id, data):
    from werkzeug.security import generate_password_hash

    ctx = _require_manage_org_members(nonprofit_id)
    _ensure_nonprofit_exists(nonprofit_id)

    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    role = data.get("role", "nonprofit_user")

    if not name:
        raise ValueError("name is required")
    if not email:
        raise ValueError("email is required")
    if not password:
        raise ValueError("password is required")
    _validate_org_member_role(role)

    existing = user_repo.get_user_by_email(email)
    if existing and not existing.get("is_deleted"):
        raise ValueError("Email already in use")

    password_hash = generate_password_hash(password)
    if existing and existing.get("is_deleted"):
        doc = user_repo.reactivate_user(
            existing["user_id"],
            name,
            password_hash=password_hash,
        )
        doc = user_repo.update_user(existing["user_id"], {
            "role": role,
            "nonprofit_id": nonprofit_id,
            "is_admin": False,
        })
    else:
        doc = user_repo.add_user(
            name,
            email,
            password_hash=password_hash,
            role=role,
            nonprofit_id=nonprofit_id,
            is_admin=False,
        )
    return _serialize_org_member(doc)


def update_org_member(nonprofit_id, user_id, data):
    ctx = _require_manage_org_members(nonprofit_id)
    _ensure_nonprofit_exists(nonprofit_id)

    user = user_repo.get_user_by_id(user_id)
    if not user or user.get("is_deleted") or user.get("nonprofit_id") != nonprofit_id:
        raise ValueError("Member not found")

    updates = {}
    if "name" in data and data["name"] is not None:
        name = str(data["name"]).strip()
        if not name:
            raise ValueError("name cannot be empty")
        updates["name"] = name
    if "role" in data and data["role"] is not None:
        role = data["role"]
        _validate_org_member_role(role)
        if user_id == ctx["user_id"] and role != "nonprofit_owner":
            raise ValueError("You cannot remove your own owner role")
        updates["role"] = role

    if not updates:
        return _serialize_org_member(user)

    doc = user_repo.update_user(user_id, updates)
    return _serialize_org_member(doc)


def delete_org_member(nonprofit_id, user_id):
    ctx = _require_manage_org_members(nonprofit_id)
    _ensure_nonprofit_exists(nonprofit_id)

    if user_id == ctx["user_id"]:
        raise ValueError("You cannot remove yourself")

    user = user_repo.get_user_by_id(user_id)
    if not user or user.get("is_deleted") or user.get("nonprofit_id") != nonprofit_id:
        raise ValueError("Member not found")

    if user.get("role") == "nonprofit_owner":
        owners = [u for u in user_repo.list_for_nonprofit(nonprofit_id) if u.get("role") == "nonprofit_owner"]
        if len(owners) <= 1:
            raise ValueError("Cannot remove the last owner")

    if not user_repo.soft_delete(user_id):
        raise ValueError("Member not found")
    return {"deleted": True}


def generate_report_pdf(nonprofit_id, week_start=None):
    from services.report_service import build_nonprofit_pdf

    ctx = _require_nonprofit_access(nonprofit_id)
    dashboard = get_dashboard(nonprofit_id, week_start=week_start)
    return build_nonprofit_pdf(dashboard, generated_by=ctx["name"], role=ctx["role"])
