import logging
import sys


def setup_logging():
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    # Configure logging for cloud and local environment (stdout only)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )

    # Set levels for specific libraries
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("groq").setLevel(logging.INFO)


logger = logging.getLogger("CriteriaGuard")
