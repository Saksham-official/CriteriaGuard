import logging
import sys
import os

def setup_logging():
    # Create logs directory if it doesn't exist
    os.makedirs("logs", exist_ok=True)
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("logs/backend.log")
        ]
    )
    
    # Set levels for specific libraries
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("groq").setLevel(logging.INFO)

logger = logging.getLogger("CriteriaGuard")
