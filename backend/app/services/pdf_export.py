"""Renders Markdown audit reports into downloadable PDF documents.
Pure-Python stack (markdown + xhtml2pdf) chosen deliberately — no external
binaries (wkhtmltopdf, GTK) required, so this works without extra system
installs on Windows dev machines."""
import io
from datetime import datetime, timezone

import markdown as md
from xhtml2pdf import pisa

PDF_CSS = """
<style>
    body { font-family: Helvetica, Arial, sans-serif; font-size: 10.5pt; color: #1a1a1a; }
    h1 { font-size: 20pt; color: #111; border-bottom: 2px solid #333; padding-bottom: 8px; margin-bottom: 4px; }
    h2 { font-size: 14pt; color: #222; margin-top: 22px; margin-bottom: 8px; border-bottom: 1px solid #ccc; padding-bottom: 4px; }
    p { line-height: 1.5; margin: 6px 0; }
    table { border-collapse: collapse; width: 100%; margin: 10px 0; }
    th, td { border: 1px solid #999; padding: 6px 10px; font-size: 10pt; text-align: left; }
    th { background-color: #eee; font-weight: bold; }
    ul, ol { margin: 6px 0; padding-left: 22px; }
    li { margin-bottom: 4px; line-height: 1.5; }
    .meta { color: #666; font-size: 9pt; margin-bottom: 20px; }
    strong { color: #000; }
</style>
"""


def render_audit_report_pdf(run_name: str, content_markdown: str, generated_at: datetime | None = None) -> bytes:
    """Converts a Markdown audit report (as produced by FINAL_REPORT_PROMPT)
    into formatted PDF bytes."""
    html_body = md.markdown(content_markdown, extensions=["tables", "fenced_code"])

    generated_at = generated_at or datetime.now(timezone.utc)
    timestamp = generated_at.strftime("%Y-%m-%d %H:%M UTC")

    full_html = f"""
    <html>
    <head>{PDF_CSS}</head>
    <body>
        <div class="meta">Generated {timestamp} &middot; {run_name}</div>
        {html_body}
    </body>
    </html>
    """

    output = io.BytesIO()
    result = pisa.CreatePDF(src=full_html, dest=output)
    if result.err:
        raise RuntimeError(f"PDF generation failed with {result.err} error(s)")

    return output.getvalue()