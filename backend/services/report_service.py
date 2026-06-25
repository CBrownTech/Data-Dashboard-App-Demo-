"""Generate PDF dashboard reports for nonprofit organizations."""
from datetime import datetime, timezone

from fpdf import FPDF


_PDF_CHAR_REPLACEMENTS = {
    "\u2013": "-",   # en dash
    "\u2014": "-",   # em dash
    "\u2212": "-",   # minus sign
    "\u2010": "-",   # hyphen
    "\u2011": "-",   # non-breaking hyphen
    "\u2192": "->",  # rightwards arrow
    "\u2190": "<-",  # leftwards arrow
    "\u2026": "...", # ellipsis
    "\u00a0": " ",   # non-breaking space
}


def _safe(text):
    if text is None:
        return ""
    text = str(text)
    for src, dest in _PDF_CHAR_REPLACEMENTS.items():
        text = text.replace(src, dest)
    return text.encode("latin-1", "replace").decode("latin-1")


def _paragraph(pdf, text, height=6):
    pdf.set_x(pdf.l_margin)
    pdf.multi_cell(pdf.epw, height, _safe(text))


def _money(value):
    return f"${float(value or 0):,.2f}"


def _int(value):
    return f"{int(value or 0):,}"


def _wow_line(comparison, *, is_money=False):
    if not comparison:
        return "No prior-week data."
    change = comparison.get("change", 0)
    pct = comparison.get("changePct", 0)
    trend = comparison.get("trend", "flat")
    sign = "+" if change > 0 else ""
    cur = _money(comparison.get("current")) if is_money else _int(comparison.get("current"))
    prev = _money(comparison.get("previous")) if is_money else _int(comparison.get("previous"))
    if trend == "flat":
        return f"Unchanged vs prior week ({cur}; prior: {prev})"
    direction = "Up" if trend == "up" else "Down"
    return f"{direction} {abs(pct)}% week-over-week ({prev} -> {cur}, {sign}{change:,.0f})"


class NonprofitReport(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(100, 100, 100)
        self.cell(0, 8, "ImpactDash - Weekly Nonprofit Dashboard Report", align="L", new_x="LMARGIN", new_y="NEXT")
        self.ln(2)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(130, 130, 130)
        self.cell(0, 10, f"Page {self.page_no()}", align="C", new_x="LMARGIN", new_y="NEXT")

    def section_title(self, title):
        self.set_font("Helvetica", "B", 14)
        self.set_text_color(30, 58, 95)
        self.ln(4)
        self.cell(0, 10, _safe(title), new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(0, 102, 179)
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        self.ln(6)

    def body_text(self, text):
        self.set_font("Helvetica", "", 10)
        self.set_text_color(50, 50, 50)
        _paragraph(self, text)
        self.ln(2)

    def bullet(self, text):
        self.set_font("Helvetica", "", 10)
        self.set_text_color(50, 50, 50)
        _paragraph(self, f"- {text}")
        self.ln(1)


def _section_reporting_period(pdf, weekly):
    pdf.section_title("Reporting Period")
    reporting = (weekly or {}).get("reportingWeek") or {}
    prior = (weekly or {}).get("priorWeek") or {}
    if reporting.get("reportLabel"):
        pdf.body_text(f"Selected week: {reporting['reportLabel']}")
    elif reporting.get("label"):
        pdf.body_text(f"Selected week: {reporting['label']}")
    if prior.get("reportLabel"):
        pdf.body_text(f"Compared to: {prior['reportLabel']}")
    elif prior.get("label"):
        pdf.body_text(f"Compared to: {prior['label']} (prior week)")
    if not reporting and not prior:
        pdf.body_text("Weekly snapshots not available; showing latest dashboard totals.")


def _section_executive_summary(pdf, weekly):
    summaries = (weekly or {}).get("summaries") or []
    if not summaries:
        return
    pdf.section_title("Executive Summary")
    for line in summaries:
        pdf.bullet(line)


def _section_weekly_trend_table(pdf, weekly):
    history = (weekly or {}).get("history") or []
    if not history:
        return
    pdf.section_title("Weekly Trend (Last 6 Weeks)")
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_text_color(30, 58, 95)
    col_w = pdf.epw / 5
    headers = ["Week", "Email Opens", "P2P Msgs", "Call Hrs", "Donations"]
    for h in headers:
        pdf.cell(col_w, 6, h, border=1)
    pdf.ln()
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(50, 50, 50)
    for row in history:
        pdf.cell(col_w, 5, _safe(row.get("label", "")[:18]), border=1)
        pdf.cell(col_w, 5, _int(row.get("emailOpens")), border=1)
        pdf.cell(col_w, 5, _int(row.get("p2pMessagesSent")), border=1)
        pdf.cell(col_w, 5, f"{float(row.get('callHours') or 0):,.1f}", border=1)
        pdf.cell(col_w, 5, _money(row.get("donationsTotal")), border=1)
        pdf.ln()
    pdf.ln(4)


def _section_email(pdf, categories, comparisons):
    email = (categories or {}).get("email") or {}
    comp = (comparisons or {}).get("emailOpens")
    if not email and not comp:
        return
    pdf.section_title("Email")
    if comp:
        pdf.bullet(f"Weekly opens: {_wow_line(comp)}")
    pdf.bullet(
        f"Channel donations: {_money(email.get('donationsRaised'))} "
        f"({email.get('donationCount', 0):,} gifts, avg {_money(email.get('avgGift'))})"
    )
    pdf.bullet(f"Share of weekly donations: {email.get('shareOfTotal', 0)}%")


def _section_p2p(pdf, categories, comparisons):
    p2p = (categories or {}).get("p2pTexting") or {}
    if not p2p:
        return
    pdf.section_title("P2P Texting")
    msg_comp = (comparisons or {}).get("p2pMessagesSent")
    if msg_comp:
        pdf.bullet(f"Messages sent: {_wow_line(msg_comp)}")
    pdf.bullet(f"Responses: {p2p.get('responses', 0):,} (rate {p2p.get('responseRate', 0)}%)")
    pdf.bullet(f"Opt-outs: {p2p.get('optOuts', 0):,}")
    resp_comp = (comparisons or {}).get("p2pResponses")
    if resp_comp:
        pdf.bullet(f"Response volume: {_wow_line(resp_comp)}")
    pdf.bullet(
        f"P2P donations: {_money(p2p.get('donationsRaised'))} "
        f"({p2p.get('donationCount', 0):,} gifts, {p2p.get('shareOfTotal', 0)}% of total)"
    )


def _section_call_time(pdf, categories, comparisons):
    call = (categories or {}).get("callTime") or {}
    if not call:
        return
    pdf.section_title("Call Time")
    hrs_comp = (comparisons or {}).get("callHours")
    if hrs_comp:
        pdf.bullet(f"Call hours: {_wow_line(hrs_comp)}")
    pdf.bullet(f"Calls made: {call.get('callsMade', 0):,}")
    pdf.bullet(f"Contacts reached: {call.get('contactsReached', 0):,}")
    pdf.bullet(f"Average duration: {call.get('avgDurationMinutes', 0)} minutes")
    calls_comp = (comparisons or {}).get("callsMade")
    if calls_comp:
        pdf.bullet(f"Call volume: {_wow_line(calls_comp)}")
    pdf.bullet(
        f"Call-time donations: {_money(call.get('donationsRaised'))} "
        f"({call.get('donationCount', 0):,} gifts, {call.get('shareOfTotal', 0)}% of total)"
    )


def _section_donors_channels(pdf, categories, donors, summary):
    donors_cat = (categories or {}).get("donors") or {}
    channels = donors_cat.get("channelBreakdown") or {}
    pdf.section_title("Donors and Channels")
    pdf.bullet(f"Donor count: {summary.get('donorCount', 0):,}")
    pdf.bullet(f"Total donations (dashboard): {_money(summary.get('totalDonations'))}")
    biggest = donors_cat.get("biggestDonorName") or ""
    highest = donors_cat.get("highestDonation") or 0
    if biggest:
        pdf.bullet(f"Biggest donor: {biggest} ({_money(highest)})")
    if channels:
        pdf.bullet(
            f"Channel mix - Email: {_money(channels.get('email'))}, "
            f"P2P: {_money(channels.get('p2pTexting'))}, "
            f"Call: {_money(channels.get('callTime'))}, "
            f"Other: {_money(channels.get('other'))}"
        )
    if donors:
        pdf.ln(2)
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(0, 6, "Top Donors", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 9)
        for donor in donors[:5]:
            _paragraph(pdf, f"  {donor['name']}: {_money(donor['donationAmount'])}", height=5)


def _section_funding_volunteers(pdf, metrics, summary, comparisons):
    pdf.section_title("Funding and Volunteers")
    pdf.bullet(f"Funding goal: {_money(metrics.get('fundingGoal'))}")
    pdf.bullet(f"Raised: {_money(metrics.get('fundingRaised'))} ({metrics.get('fundingProgress', 0)}% of goal)")
    pdf.bullet(f"Grants received: {_money(metrics.get('grantsReceived'))}")
    funding_comp = (comparisons or {}).get("fundingRaised")
    if funding_comp:
        pdf.bullet(f"Weekly funding trend: {_wow_line(funding_comp, is_money=True)}")
    pdf.bullet(f"Active volunteers: {summary.get('activeVolunteers', 0):,}")
    pdf.bullet(f"Volunteer hours: {summary.get('volunteerHours', 0):,}")
    vol_comp = (comparisons or {}).get("activeVolunteers")
    if vol_comp:
        pdf.bullet(f"Volunteer count: {_wow_line(vol_comp)}")
    hrs_comp = (comparisons or {}).get("volunteerHours")
    if hrs_comp:
        pdf.bullet(f"Volunteer hours (weekly): {_wow_line(hrs_comp)}")


def _section_programs(pdf, programs):
    pdf.section_title("Programs")
    if not programs:
        pdf.body_text("No programs recorded.")
        return
    for program in programs:
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(30, 58, 95)
        pdf.cell(0, 7, _safe(program["name"]), new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(50, 50, 50)
        _paragraph(
            pdf,
            f"Status: {program['status']} | Participants: {program['participants']} | "
            f"Budget: {_money(program['budget'])}",
        )
        pdf.ln(2)


def build_nonprofit_pdf(dashboard, generated_by, role):
    pdf = NonprofitReport()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()

    nonprofit = dashboard["nonprofit"]
    summary = dashboard["summary"]
    metrics = dashboard["metrics"]
    categories = dashboard.get("categories") or {}
    donors = dashboard.get("donors") or []
    programs = dashboard["programs"]
    weekly = dashboard.get("weeklyMetrics") or {}
    comparisons = weekly.get("comparisons") or {}
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    pdf.set_font("Helvetica", "B", 22)
    pdf.set_text_color(30, 58, 95)
    pdf.cell(0, 12, _safe(nonprofit["name"]), new_x="LMARGIN", new_y="NEXT")
    reporting = weekly.get("reportingWeek") or {}
    if reporting.get("reportLabel"):
        pdf.set_font("Helvetica", "B", 12)
        pdf.set_text_color(0, 102, 179)
        pdf.cell(0, 8, _safe(reporting["reportLabel"]), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(0, 7, f"Generated: {generated_at}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 7, f"Prepared for: {_safe(generated_by)} ({_safe(role)})", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(6)

    pdf.section_title("Organization Profile")
    pdf.body_text(f"Location: {nonprofit.get('location') or 'N/A'}")
    pdf.body_text(f"Mission: {nonprofit.get('mission') or 'N/A'}")

    pdf.section_title("KPI Summary")
    pdf.bullet(f"Donors: {summary['donorCount']:,}")
    pdf.bullet(f"Total donations: {_money(summary['totalDonations'])}")
    pdf.bullet(f"Active volunteers: {summary['activeVolunteers']:,}")
    pdf.bullet(f"Volunteer hours: {summary['volunteerHours']:,}")
    pdf.bullet(f"Active programs: {summary['activePrograms']} of {summary['totalPrograms']}")

    _section_reporting_period(pdf, weekly)
    _section_executive_summary(pdf, weekly)
    _section_weekly_trend_table(pdf, weekly)
    _section_email(pdf, categories, comparisons)
    _section_p2p(pdf, categories, comparisons)
    _section_call_time(pdf, categories, comparisons)
    _section_donors_channels(pdf, categories, donors, summary)
    _section_funding_volunteers(pdf, metrics, summary, comparisons)
    _section_programs(pdf, programs)

    return bytes(pdf.output())
