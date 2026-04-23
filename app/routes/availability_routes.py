from fastapi import APIRouter, HTTPException

from app.services.availability_page_service import get_availability_page_data

router = APIRouter()


@router.get("/availability-page-data")
def availability_page_data(date: str, view: str = "shared"):
    try:
        return get_availability_page_data(date, view)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Availability page error: {exc}")