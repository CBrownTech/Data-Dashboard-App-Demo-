"""Generate PDF dashboard reports for nonprofit organizations."""
from datetime import datetime, timezone

from fpdf import FPDF


def _safe(text):
    if text is None:
        return ""
    return str(text).encode("latin-1", "replace").decode("latin-1")


def _paragraph(pdf, text, height=6):
    pdf.set_x(pdf.l_margin)
    pdf.multi_cell(pdf.epw, height, _safe(text))


def _money(value):
    return f"${value:,.2f}"


class NonprofitReport(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(100, 100, 100)
        self.cell(0, 8, "ImpactDash - Nonprofit Dashboard Report", align="L", new_x="LMARGIN", new_y="NEXT")
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


def _format_email_change(insights):
    change = insights.get("emailOpensChange", 0)
    pct = insights.get("emailOpensChangePct", 0)
    sign = "+" if change > 0 else ""
    return f"{sign}{change:,} opens ({sign}{pct}%)"


def _email_trend_label(trend):
    if trend == "up":
        return "Email opens increased compared to the previous period."
    if trend == "down":
        return "Email opens decreased compared to the previous period."
    return "Email opens were unchanged compared to the previous period."


def build_nonprofit_pdf(dashboard, generated_by, role):
    pdf = NonprofitReport()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()

    nonprofit = dashboard["nonprofit"]
    summary = dashboard["summary"]
    metrics = dashboard["metrics"]
    insights = dashboard.get("insights") or {}
    donors = dashboard.get("donors") or []
    programs = dashboard["programs"]
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    pdf.set_font("Helvetica", "B", 22)
    pdf.set_text_color(30, 58, 95)
    pdf.cell(0, 12, _safe(nonprofit["name"]), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(0, 7, f"Generated: {generated_at}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 7, f"Prepared for: {_safe(generated_by)} ({_safe(role)})", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(6)

    pdf.section_title("Organization Profile")
    pdf.body_text(f"Location: {nonprofit.get('location') or 'N/A'}")
    pdf.body_text(f"Mission: {nonprofit.get('mission') or 'N/A'}")

    pdf.section_title("KPI Summary")
    pdf.bullet(f"Donors: {summary['donorCount']}")
    pdf.bullet(f"Total donations: {_money(summary['totalDonations'])}")
    pdf.bullet(f"Active volunteers: {summary['activeVolunteers']}")
    pdf.bullet(f"Volunteer hours: {summary['volunteerHours']:,}")
    pdf.bullet(f"Active programs: {summary['activePrograms']} of {summary['totalPrograms']}")

    highest = insights.get("highestDonation") or metrics.get("highestDonation") or 0
    biggest_name = insights.get("biggestDonorName") or metrics.get("biggestDonorName") or ""
    if highest > 0 or biggest_name or donors:
        pdf.section_title("Donor Highlights")
        if biggest_name:
            pdf.bullet(f"Biggest donor: {biggest_name} ({_money(highest)})")
        pdf.bullet(f"Highest single donation: {_money(highest)}")
        if donors:
            pdf.ln(2)
            pdf.set_font("Helvetica", "B", 10)
            pdf.cell(0, 6, "Top Donors", new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("Helvetica", "", 9)
            for donor in donors[:5]:
                _paragraph(
                    pdf,
                    f"  {donor['name']}: {_money(donor['donationAmount'])}",
                    height=5,
                )

    email_current = insights.get("emailOpensCurrent") or metrics.get("emailOpensCurrent") or 0
    email_previous = insights.get("emailOpensPrevious") or metrics.get("emailOpensPrevious") or 0
    if email_current > 0 or email_previous > 0:
        pdf.section_title("Email Engagement")
        pdf.bullet(f"Current period opens: {email_current:,}")
        pdf.bullet(f"Previous period opens: {email_previous:,}")
        pdf.bullet(f"Change: {_format_email_change(insights)}")
        pdf.body_text(_email_trend_label(insights.get("emailOpensTrend", "flat")))

    pdf.section_title("Funding")
    pdf.bullet(f"Goal: {_money(metrics['fundingGoal'])}")
    pdf.bullet(f"Raised: {_money(metrics['fundingRaised'])} ({metrics['fundingProgress']}% of goal)")
    pdf.bullet(f"Grants received: {_money(metrics['grantsReceived'])}")

    pdf.section_title("Programs")
    if not programs:
        pdf.body_text("No programs recorded.")
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

    return bytes(pdf.output())
