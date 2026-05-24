from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
import sys
import asyncio

# Load environment variables
load_dotenv()

from utils.logger import setup_logging, logger
from utils.websocket_manager import manager
from routers.tenders import router as tenders_router
from routers.bidders import router as bidders_router
from routers.verdicts import router as verdicts_router
from routers.reports import router as reports_router
from routers.audit import router as audit_router

# Initialize Logging
setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle handler (replaces deprecated on_event)."""
    logger.info("Initializing CriteriaGuard Production Environment...")

    # Critical dependency checks
    required_vars = ["GROQ_API_KEY", "SUPABASE_URL"]
    missing = [var for var in required_vars if not os.getenv(var)]

    # Check for either service key or general key
    if not os.getenv("SUPABASE_SERVICE_KEY") and not os.getenv("SUPABASE_KEY"):
        missing.append("SUPABASE_SERVICE_KEY/SUPABASE_KEY")

    for var in required_vars:
        if os.getenv(var):
            logger.info(f"Configuration found: {var}")
        else:
            logger.error(f"Missing configuration: {var}")

    if missing:
        logger.critical(f"Startup failed. Missing environment variables: {', '.join(missing)}")
        import asyncio
        await asyncio.sleep(2)
        sys.exit(1)

    logger.info("All environment variables validated. System ready.")

    # Set running event loop for thread-safe websocket broadcasts
    manager.set_loop(asyncio.get_running_loop())

    yield  # application runs here

    # (shutdown logic can go here if needed)


app = FastAPI(
    title="CriteriaGuard API",
    description="Explainable AI Platform for Government Tender Eligibility Evaluation",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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


@app.websocket("/ws/progress/{bidder_id}")
async def websocket_progress_endpoint(websocket: WebSocket, bidder_id: str):
    await manager.connect(bidder_id, websocket)
    try:
        while True:
            # Maintain connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(bidder_id, websocket)
    except Exception as e:
        logger.error(f"WebSocket error for bidder {bidder_id}: {e}")
        manager.disconnect(bidder_id, websocket)


@app.get("/health")
async def health_check():
    return {"status": "ok", "message": "CriteriaGuard API is running."}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
