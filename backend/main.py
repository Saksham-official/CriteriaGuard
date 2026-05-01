from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

# Load environment variables FIRST before importing routers
load_dotenv()

from routers.tenders import router as tenders_router
from routers.bidders import router as bidders_router
from routers.verdicts import router as verdicts_router
from routers.reports import router as reports_router
from routers.audit import router as audit_router

app = FastAPI(
    title="CriteriaGuard API",
    description="Explainable AI Platform for Government Tender Eligibility Evaluation",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tenders_router)
app.include_router(bidders_router)
app.include_router(verdicts_router)
app.include_router(reports_router)
app.include_router(audit_router)

@app.get("/health")
async def health_check():
    return {"status": "ok", "message": "CriteriaGuard API is running."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
