from datetime import UTC, date, datetime, time

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.models import Price


class PriceRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, ticker: str, price: float, timestamp: int) -> Price:
        record = Price(ticker=ticker, price=price, timestamp=timestamp)
        self._session.add(record)
        self._session.commit()
        self._session.refresh(record)
        return record

    def list_by_ticker(self, ticker: str) -> list[Price]:
        statement: Select[tuple[Price]] = (
            select(Price).where(Price.ticker == ticker).order_by(Price.timestamp.desc())
        )
        return list(self._session.scalars(statement))

    def latest(self, ticker: str) -> Price | None:
        statement: Select[tuple[Price]] = (
            select(Price).where(Price.ticker == ticker).order_by(Price.timestamp.desc()).limit(1)
        )
        return self._session.scalar(statement)

    def list_for_date(self, ticker: str, requested_date: date) -> list[Price]:
        start = int(datetime.combine(requested_date, time.min, tzinfo=UTC).timestamp())
        end = start + 86_400
        statement: Select[tuple[Price]] = (
            select(Price)
            .where(Price.ticker == ticker, Price.timestamp >= start, Price.timestamp < end)
            .order_by(Price.timestamp.asc())
        )
        return list(self._session.scalars(statement))
