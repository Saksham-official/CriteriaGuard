import os
from xhtml2pdf import pisa
from jinja2 import Template
import io
from datetime import datetime

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
<style>
    @page {
        size: A4;
        margin: 2cm;
        @frame footer {
            -pdf-frame-content: footerContent;
            bottom: 1cm;
            margin-left: 2cm;
            margin-right: 2cm;
            height: 1cm;
        }
    }
    body { font-family: Helvetica, sans-serif; font-size: 11pt; color: #333; }
    h1 { color: #1a365d; text-align: center; border-bottom: 2px solid #1a365d; padding-bottom: 10px; }
    h2 { color: #2d3748; margin-top: 30px; border-bottom: 1px solid #cbd5e0; padding-bottom: 5px; }
    .header { text-align: center; margin-bottom: 40px; }
    .org-name { font-size: 16pt; font-weight: bold; color: #1a365d; text-transform: uppercase; }
    .sub-org { font-size: 12pt; color: #4a5568; }
    table { width: 100%; border-collapse: collapse; margin-top: 15px; }
    th, td { border: 1px solid #cbd5e0; padding: 8px; text-align: left; }
    th { background-color: #f7fafc; font-weight: bold; }
    .badge-eligible { color: green; font-weight: bold; }
    .badge-not-eligible { color: red; font-weight: bold; }
    .badge-review { color: orange; font-weight: bold; }
    .meta-box { background: #f8fafc; padding: 15px; border: 1px solid #e2e8f0; margin-bottom: 30px; }
    .signature-block { margin-top: 60px; float: right; width: 250px; text-align: center; }
    .signature-line { border-top: 1px solid #000; margin-top: 50px; padding-top: 5px; }
</style>
</head>
<body>

<div class="header">
    <div class="org-name">Government of India</div>
    <div class="sub-org">Central Procurement Portal Verification Report</div>
</div>

<div class="meta-box">
    <strong>Tender ID:</strong> {{ tender_id }}<br/>
    <strong>Tender Title:</strong> {{ tender_title }}<br/>
    <strong>Date of Evaluation:</strong> {{ date }}<br/>
    <strong>Officer in Charge:</strong> System Generated (CriteriaGuard AI)
</div>

<h1>Evaluation Summary</h1>
<p>This document contains the automated eligibility evaluation for the bidders submitted against the aforementioned tender. All verdicts are derived deterministically based on extracted values.</p>

{% for bidder in bidders %}
<h2>Bidder: {{ bidder.name }}</h2>
<p><strong>Overall Status:</strong> {{ bidder.status | upper }}</p>

<table>
    <thead>
        <tr>
            <th>Criterion</th>
            <th>Extracted Value</th>
            <th>Status</th>
            <th>System Reason</th>
        </tr>
    </thead>
    <tbody>
        {% for ext in bidder.extractions %}
        <tr>
            <td>{{ ext.criteria.category | upper }}<br/><small>{{ ext.criteria.text }}</small></td>
            <td>{{ ext.extracted_value or 'Not Found' }}</td>
            <td class="
                {% if ext.verdict.status == 'Eligible' %}badge-eligible
                {% elif ext.verdict.status == 'Not Eligible' %}badge-not-eligible
                {% else %}badge-review{% endif %}
            ">{{ ext.verdict.status }}</td>
            <td><small>{{ ext.verdict.reason }}</small></td>
        </tr>
        {% endfor %}
    </tbody>
</table>
{% endfor %}

<div class="signature-block">
    <div class="signature-line">
        <strong>Digital Authorization</strong><br/>
        CriteriaGuard Verification Engine<br/>
        Generated on {{ date }}
    </div>
</div>

<div id="footerContent" style="text-align:center; font-size: 9pt; color: #718096;">
    CriteriaGuard Automated Report | Page <pdf:pagenumber> of <pdf:pagecount>
</div>

</body>
</html>
"""

def generate_tender_report_pdf(tender_id: str, tender_title: str, bidders_data: list) -> bytes:
    template = Template(HTML_TEMPLATE)
    
    html_content = template.render(
        tender_id=tender_id,
        tender_title=tender_title,
        date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        bidders=bidders_data
    )
    
    # Render PDF
    pdf_buffer = io.BytesIO()
    pisa_status = pisa.CreatePDF(io.StringIO(html_content), dest=pdf_buffer)
    
    if pisa_status.err:
        raise Exception("Failed to generate PDF report")
        
    return pdf_buffer.getvalue()
