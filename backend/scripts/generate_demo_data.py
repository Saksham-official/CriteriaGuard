import os
from xhtml2pdf import pisa
from jinja2 import Template
import io

# Simple HTML template for generating demo PDFs
DEMO_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
<style>
    body { font-family: Helvetica, sans-serif; font-size: 11pt; line-height: 1.5; }
    h1 { color: #1a365d; text-align: center; }
    h2 { color: #2d3748; border-bottom: 1px solid #ccc; }
    .content { margin: 20px; }
    .clause { font-weight: bold; margin-top: 10px; }
    .footer { font-size: 9pt; text-align: center; color: #777; margin-top: 50px; }
</style>
</head>
<body>
    <h1>{{ title }}</h1>
    <div class="content">
        {{ body | safe }}
    </div>
    <div class="footer">
        Confidential - CriteriaGuard Demo Data
    </div>
</body>
</html>
"""

def create_pdf(filename, title, body):
    template = Template(DEMO_TEMPLATE)
    html_content = template.render(title=title, body=body)
    
    with open(filename, "wb") as f:
        pisa.CreatePDF(io.StringIO(html_content), dest=f)
    print(f"Created {filename}")

# 1. Mock Tender
tender_body = """
<h2>Section 4: Eligibility Criteria</h2>
<p class="clause">4.1 Financial Standing</p>
<p>The bidder must have an average annual turnover of at least 50 Crores INR during the last three financial years. Proof of turnover certified by a Chartered Accountant must be submitted.</p>

<p class="clause">4.2 Technical Experience</p>
<p>The bidder should have successfully executed orders for the supply of at least 500 Tactical Drones to Government or Defense agencies in the last 5 years.</p>

<p class="clause">4.3 Quality Certifications</p>
<p>The bidder shall possess a valid ISO 9001:2015 certification for manufacturing of unmanned aerial vehicles.</p>

<p class="clause">4.4 Local Content</p>
<p>As per Make in India policy, the bidder must have a minimum local content of 50%.</p>
"""

# 2. Bidders
bidder_1 = """
<h2>Bidder: AeroTech Solutions Ltd.</h2>
<p>Average Annual Turnover: 75 Crores INR (Last 3 years).</p>
<p>Experience: Supplied 1,200 drones to the Indian Army in 2023.</p>
<p>Certification: Attached ISO 9001:2015 certificate (Valid until 2027).</p>
<p>Local Content: 65%.</p>
"""

bidder_2 = """
<h2>Bidder: SkyBound Drones Pvt. Ltd.</h2>
<p>Average Annual Turnover: 35 Crores INR (Last 3 years).</p>
<p>Experience: Supplied 600 drones to State Police departments.</p>
<p>Certification: Attached ISO 9001:2015 certificate.</p>
<p>Local Content: 55%.</p>
"""

bidder_3 = """
<h2>Bidder: Global Defense Systems</h2>
<p>Average Annual Turnover: 120 Crores INR.</p>
<p>Experience: New entrant in drone market. Supplied 50 drones for research.</p>
<p>Certification: ISO 9001:2015 certified.</p>
<p>Local Content: 52%.</p>
"""

bidder_4 = """
<h2>Bidder: Precision Airworks</h2>
<p>Average Annual Turnover: 55 Crores INR.</p>
<p>Experience: Supplied 800 drones to various agencies.</p>
<p>Certification: Pending ISO 9001 renewal. Currently has ISO 14001 only.</p>
<p>Local Content: 60%.</p>
"""

bidder_5 = """
<h2>Bidder: Marginal Aviations</h2>
<p>Average Annual Turnover: 49.5 Crores INR (Audited Financials 2024).</p>
<p>Experience: Supplied 510 drones to paramilitary forces.</p>
<p>Certification: ISO 9001:2015 certified.</p>
<p>Local Content: 50%.</p>
"""

def main():
    upload_dir = "backend/uploads"
    tenders_dir = os.path.join(upload_dir, "tenders")
    bidders_dir = os.path.join(upload_dir, "bidders")
    
    os.makedirs(tenders_dir, exist_ok=True)
    os.makedirs(bidders_dir, exist_ok=True)
    
    create_pdf(os.path.join(tenders_dir, "mock_tender.pdf"), "Tender for High-Altitude Tactical Drones", tender_body)
    create_pdf(os.path.join(bidders_dir, "bidder_1_eligible.pdf"), "AeroTech Solutions Proposal", bidder_1)
    create_pdf(os.path.join(bidders_dir, "bidder_2_low_turnover.pdf"), "SkyBound Drones Proposal", bidder_2)
    create_pdf(os.path.join(bidders_dir, "bidder_3_no_experience.pdf"), "Global Defense Proposal", bidder_3)
    create_pdf(os.path.join(bidders_dir, "bidder_4_missing_iso.pdf"), "Precision Airworks Proposal", bidder_4)
    create_pdf(os.path.join(bidders_dir, "bidder_5_borderline.pdf"), "Marginal Aviations Proposal", bidder_5)

if __name__ == "__main__":
    main()
