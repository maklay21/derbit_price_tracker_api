from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories import PriceRepository
from app.schemas import PriceRead
from app.services import PriceService, normalize_ticker

router = APIRouter(prefix="/prices", tags=["prices"])
Ticker = Annotated[str, Query(min_length=1, max_length=16, description="Deribit index ticker")]


def get_service(session: Session = Depends(get_db)) -> PriceService:
    return PriceService(PriceRepository(session))


def validate_ticker(ticker: str) -> str:
    try:
        return normalize_ticker(ticker)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@router.get("", response_model=list[PriceRead], summary="Get all stored prices for a ticker")
def get_prices(ticker: Ticker, service: PriceService = Depends(get_service)) -> list[PriceRead]:
    return service.history(validate_ticker(ticker))


@router.get("/latest", response_model=PriceRead, summary="Get the latest stored price")
def get_latest_price(ticker: Ticker, service: PriceService = Depends(get_service)) -> PriceRead:
    price = service.latest(validate_ticker(ticker))
    if price is None:
        raise HTTPException(status_code=404, detail="No prices found for ticker")
    return price


@router.get("/by-date", response_model=list[PriceRead], summary="Get prices recorded on a UTC date")
def get_prices_by_date(
    ticker: Ticker,
    on: Annotated[date, Query(description="UTC calendar date, YYYY-MM-DD")],
    service: PriceService = Depends(get_service),
) -> list[PriceRead]:
    return service.for_date(validate_ticker(ticker), on)
