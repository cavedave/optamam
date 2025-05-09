from fastapi import APIRouter, HTTPException
from app.core.fair_division import calculate_fair_division
from app.models.calculator import FairDivisionRequest, FairDivisionResponse
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/calculate", response_model=FairDivisionResponse)
async def calculate(request: FairDivisionRequest):
    try:
        # Convert request to the format expected by calculate_fair_division
        items = [{"name": item.name, "is_divisible": item.is_divisible} for item in request.items]
        people = [person.name for person in request.people]
        
        # Convert valuations to the expected format
        valuations = {}
        for item in items:
            valuations[item['name']] = {}
            for person in people:
                # Find the valuation for this item-person pair
                valuation = next(
                    (v for v in request.valuations if v.item == item['name'] and v.person == person),
                    None
                )
                if valuation is None:
                    raise ValueError(f"Missing valuation for {person} and {item['name']}")
                valuations[item['name']][person] = valuation.value
        
        # Calculate fair division
        result = calculate_fair_division(items, people, valuations)
        
        return FairDivisionResponse(
            success=True,
            message="Calculation successful",
            result=result
        )
        
    except Exception as e:
        logger.error(f"Calculation failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=400,
            detail=str(e)
        ) 