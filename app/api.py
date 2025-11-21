from fastapi import APIRouter, HTTPException
import logging

from app.schemas import (
    ProductionPlanRequest,
    ProductionResponseItem,
)
from app.services import ProductionPlanService

logger = logging.getLogger(__name__)

router = APIRouter()


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
async def calculate_production_plan(
    request: ProductionPlanRequest,
) -> list[ProductionResponseItem]:
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

    try:
        # Call the service to calculate the production plan
        response = await ProductionPlanService.calculate_production_plan(
            load=request.load, fuels=request.fuels, powerplants=request.powerplants
        )
    except ValueError as e:
        logger.error("Error calculating production plan: %s", str(e))
        raise HTTPException(
            status_code=400, detail=f"Unable to calculate production plan: {str(e)}"
        )

    logger.info("Returning production plan response: %s", response)
    return response
