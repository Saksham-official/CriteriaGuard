import fitz
import os

def generate_tender_1():
    doc = fitz.open()
    page = doc.new_page()
    
    text = """
    GOVERNMENT OF INDIA
    MINISTRY OF HOME AFFAIRS
    CENTRAL RESERVE POLICE FORCE
    
    TENDER NOTICE
    Subject: Construction of 200-bed Barracks at Group Centre, Pune
    
    1. Introduction
    The CRPF invites electronic bids from eligible bidders for the construction of 200-bed barracks.
    
    4. Eligibility Criteria
    4.1 The bidder shall have a minimum annual turnover of Rupees Five Crore (Rs. 5,000,000,000) 
        during the last three financial years. Evidence: CA Certificate.
    4.2 The bidder must have completed at least 3 similar works in the last 5 years. 
        Evidence: Completion Certificates.
    4.3 The bidder should preferably have a valid ISO 9001 certification.
    4.4 It is mandatory for the bidder to submit a valid GST Registration Certificate.
    
    5. Submission Guidelines
    All documents must be uploaded before 15th June 2026.
    """
    
    page.insert_text((50, 50), text, fontsize=12)
    
    os.makedirs("../../demo_data", exist_ok=True)
    doc.save("../../demo_data/synthetic_tender_1.pdf")
    doc.close()
    print("synthetic_tender_1.pdf created.")

if __name__ == "__main__":
    generate_tender_1()
