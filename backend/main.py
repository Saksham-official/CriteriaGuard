import asyncio
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Load environment variables
load_dotenv()

from routers.audit import router as audit_router
from routers.bidders import router as bidders_router
from routers.reports import router as reports_router
from routers.tenders import router as tenders_router
from routers.verdicts import router as verdicts_router
from utils.logger import logger, setup_logging
from utils.websocket_manager import manager

# Initialize Logging
setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle handler."""
    is_mock = (
        os.getenv("MOCK_LLM", "").lower() in ("true", "1")
        or os.getenv("USE_SAMPLE_DATA", "").lower() in ("true", "1")
        or not (
            os.getenv("GROQ_API_KEY")
            and os.getenv("SUPABASE_URL")
            and (os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_KEY"))
        )
    )

    if is_mock:
        logger.info("=" * 64)
        logger.info("🛡️  CRITERIAGUARD CONTRIBUTOR / MOCK MODE ACTIVE")
        logger.info("Zero external API keys or cloud credentials required!")
        logger.info("- Extraction Engine : Deterministic mock mode (MOCK_LLM=true)")
        logger.info("- Database Layer    : In-memory store pre-seeded (USE_SAMPLE_DATA=true)")
        logger.info("- Rules Engine      : Active deterministic evaluation (VerdictCore)")
        logger.info("- Audit Trail       : SHA-256 cryptographic chain active")
        logger.info("=" * 64)
    else:
        logger.info("Initializing CriteriaGuard Production Environment...")
        logger.info("All production environment variables validated. System ready.")

    # Set running event loop for thread-safe websocket broadcasts
    manager.set_loop(asyncio.get_running_loop())

    yield


app = FastAPI(
    title="CriteriaGuard API",
    description="Explainable AI Platform for Government Tender Eligibility Evaluation",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(bidder_id, websocket)
    except Exception as e:
        logger.error(f"WebSocket error for bidder {bidder_id}: {e}")
        manager.disconnect(bidder_id, websocket)


@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "message": "CriteriaGuard API is running.",
        "mode": (
            "mock"
            if (os.getenv("MOCK_LLM", "").lower() in ("true", "1") or not os.getenv("GROQ_API_KEY"))
            else "production"
        ),
    }


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
