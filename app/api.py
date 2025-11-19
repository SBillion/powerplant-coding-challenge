from fastapi import FastAPI
import logging

from app.schemas import ProductionResponseItem, ProductionResponse

logger = logging.getLogger(__name__)

router = FastAPI()


@router.get(
    "/",
    summary="Health Check",
    description="Check the health status of the API",
)
async def health_check():
    """Health check endpoint."""
    return {
        "status": "ok",
        "message": "Powerplant Production Plan API is running",
        "version": "0.1.0",
    }


@router.post(
    "/productionplan",
    summary="Calculate Production Plan",
    description="Calculate the optimal power production plan based on the merit order",
    response_model=list[ProductionResponseItem],
)
async def calculate_production_plan(request: dict) -> ProductionResponse:
    """
    Calculate the optimal production plan for powerplants to meet the load.

    The endpoint accepts a payload with:
    - load: The required power load in MWh
    - fuels: Current fuel prices and wind percentage
    - powerplants: Available powerplants with their specifications

    Returns a list of powerplants with their allocated power output.
    """
    # Placeholder implementation
    logger.info("Received production plan request: %s", request)

    # For now, just return an empty response
    response = ProductionResponse()

    logger.info("Returning production plan response: %s", response)
    return response
