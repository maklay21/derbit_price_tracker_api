from datetime import date

from app.models import Price
from app.repositories import PriceRepository


class PriceService:
    def __init__(self, repository: PriceRepository) -> None:
        self._repository = repository

    def history(self, ticker: str) -> list[Price]:
        return self._repository.list_by_ticker(normalize_ticker(ticker))

    def latest(self, ticker: str) -> Price | None:
        return self._repository.latest(normalize_ticker(ticker))

    def for_date(self, ticker: str, requested_date: date) -> list[Price]:
        return self._repository.list_for_date(normalize_ticker(ticker), requested_date)


def normalize_ticker(ticker: str) -> str:
    normalized = ticker.strip().lower()
    if normalized not in {"btc_usd", "eth_usd"}:
        raise ValueError("ticker must be one of: btc_usd, eth_usd")
    return normalized
