from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
import sys

# Load environment variables
load_dotenv()

from utils.logger import setup_logging, logger
from routers.tenders import router as tenders_router
from routers.bidders import router as bidders_router
from routers.verdicts import router as verdicts_router
from routers.reports import router as reports_router
from routers.audit import router as audit_router

# Initialize Logging
setup_logging()

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

@app.on_event("startup")
async def startup_event():
    logger.info("Initializing CriteriaGuard Production Environment...")
    
    # Critical dependency checks
    required_vars = ["GROQ_API_KEY", "SUPABASE_URL", "SUPABASE_SERVICE_KEY"]
    missing = [var for var in required_vars if not os.getenv(var)]
    
    for var in required_vars:
        if os.getenv(var):
            logger.info(f"Configuration found: {var}")
        else:
            logger.error(f"Missing configuration: {var}")
    
    if missing:
        logger.critical(f"Startup failed. Missing environment variables: {', '.join(missing)}")
        # On Render, we want to stay alive long enough for logs to flush
        import asyncio
        await asyncio.sleep(2)
        sys.exit(1)
        
    logger.info("All environment variables validated. System ready.")

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception caught: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred. Please contact the administrator."},
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
    port = int(os.getenv("PORT", 8000))
    # In production, reload should be False
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
