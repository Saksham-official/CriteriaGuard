import requests
import os
import time

BASE_URL = "http://localhost:8000/api"

def populate_demo():
    print("Starting demo data population...")
    
    # 1. Upload Tender
    tender_path = "uploads/tenders/mock_tender.pdf"
    if not os.path.exists(tender_path):
        # Check relative to backend dir if running from there
        tender_path = os.path.join("backend", tender_path)
        
    print(f"Uploading tender: {tender_path}")
    with open(tender_path, "rb") as f:
        res = requests.post(f"{BASE_URL}/tenders/upload", files={"file": f})
    
    if res.status_code != 200:
        print(f"Failed to upload tender: {res.text}")
        return
    
    tender_id = res.json()["tender_id"]
    print(f"Tender uploaded successfully. ID: {tender_id}")
    
    # Wait for criteria extraction (llama-3.3 on groq is fast)
    print("Waiting for criteria extraction...")
    time.sleep(5)
    
    # 2. Upload Bidders
    bidders = [
        ("AeroTech Solutions", "uploads/bidders/bidder_1_eligible.pdf"),
        ("SkyBound Drones", "uploads/bidders/bidder_2_low_turnover.pdf"),
        ("Global Defense Systems", "uploads/bidders/bidder_3_no_experience.pdf"),
        ("Precision Airworks", "uploads/bidders/bidder_4_missing_iso.pdf"),
        ("Marginal Aviations", "uploads/bidders/bidder_5_borderline.pdf")
    ]
    
    for name, path in bidders:
        if not os.path.exists(path):
            path = os.path.join("backend", path)
            
        print(f"Uploading bidder: {name} ({path})")
        with open(path, "rb") as f:
            res = requests.post(f"{BASE_URL}/bidders/upload", data={
                "tender_id": tender_id,
                "bidder_name": name
            }, files={"files": f})
        
        if res.status_code != 200:
            print(f"Failed to upload bidder {name}: {res.text}")
        else:
            print(f"Bidder {name} uploaded. ID: {res.json()['bidder_id']}")
            
    print("All demo data uploaded. Processing continues in background.")

if __name__ == "__main__":
    populate_demo()
