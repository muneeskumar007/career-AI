"""PDF rendering for the performance report, using reportlab (already a
dependency for test fixtures, now also a real product feature)."""

import io

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.schemas.report import PerformanceReportResponse


def render_report_pdf(report: PerformanceReportResponse, candidate_name: str) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.75 * inch, bottomMargin=0.75 * inch)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("ReportTitle", parent=styles["Title"], textColor=colors.HexColor("#0e8e79"))
    heading_style = ParagraphStyle("ReportHeading", parent=styles["Heading2"], spaceBefore=16)

    story = [
        Paragraph("CareerAI Performance Report", title_style),
        Paragraph(f"Candidate: {candidate_name}", styles["Normal"]),
        Paragraph(f"Generated: {report.generated_at.strftime('%B %d, %Y')}", styles["Normal"]),
        Spacer(1, 16),
    ]

    score_rows = [["Metric", "Score"]]
    for label, value in [
        ("Resume Score", report.resume_score), ("ATS Score", report.ats_score),
        ("Interview Score", report.interview_score), ("Communication Score", report.communication_score),
        ("Technical Score", report.technical_score), ("Confidence Score", report.confidence_score),
    ]:
        score_rows.append([label, f"{value}/100" if value is not None else "Not available"])
    score_table = Table(score_rows, colWidths=[3 * inch, 2 * inch])
    score_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0e8e79")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#dfe3e9")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f6f7f9")]),
            ]
        )
    )
    story.append(score_table)

    if report.strong_skills:
        story.append(Paragraph("Strong Skills", heading_style))
        story.append(Paragraph(", ".join(report.strong_skills), styles["Normal"]))

    if report.weak_skills:
        story.append(Paragraph("Skills to Develop", heading_style))
        story.append(Paragraph(", ".join(report.weak_skills), styles["Normal"]))

    if report.recommendations:
        story.append(Paragraph("Recommendations", heading_style))
        for rec in report.recommendations:
            story.append(Paragraph(f"• {rec}", styles["Normal"]))

    doc.build(story)
    return buffer.getvalue()
