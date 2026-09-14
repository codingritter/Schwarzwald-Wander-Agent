from __future__ import annotations

from fpdf import FPDF


def report_to_markdown_bytes(report: str) -> bytes:
    return report.encode("utf-8")


def report_to_pdf_bytes(title: str, report: str) -> bytes:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.multi_cell(0, 10, title)
    pdf.ln(4)
    pdf.set_font("Helvetica", size=11)
    safe_text = report.encode("latin-1", errors="replace").decode("latin-1")
    pdf.multi_cell(0, 6, safe_text)
    return bytes(pdf.output())
