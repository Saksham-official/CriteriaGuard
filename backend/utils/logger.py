import logging
import sys
import os

def setup_logging():
    # Configure logging for cloud environment (stdout only)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Set levels for specific libraries
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("groq").setLevel(logging.INFO)

logger = logging.getLogger("CriteriaGuard")
