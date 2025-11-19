import logging
from fastapi import FastAPI
from app.api import router

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.

    Returns:
        Configured FastAPI application instance
    """
    app = FastAPI(
        title="Powerplant Production Plan API",
        description="Calculate optimal power production plans based on merit order",
        version="0.1.0",
    )

    # Include routers
    app.mount("/", router)

    logger.info("Application initialized successfully")

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8888, reload=True, log_level="info")
