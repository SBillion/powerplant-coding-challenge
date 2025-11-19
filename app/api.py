from fastapi import FastAPI
import logging

logger = logging.getLogger(__name__)

router = FastAPI()


@router.get(
    "/",
    summary="Health Check",
    description="Check the health status of the API",
)
def health_check():
    """Health check endpoint."""
    return {
        "status": "ok",
        "message": "Powerplant Production Plan API is running",
        "version": "0.1.0",
    }
