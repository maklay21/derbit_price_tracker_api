from datetime import UTC, datetime

from app.db.session import get_db
from app.main import app
from app.models import Price


def insert_prices():
    generator = app.dependency_overrides[get_db]()
    session = next(generator)
    session.add_all(
        [
            Price(ticker="btc_usd", price=65000.5, timestamp=1_760_000_000),
            Price(ticker="btc_usd", price=65100.0, timestamp=1_760_000_060),
            Price(ticker="eth_usd", price=3200.0, timestamp=1_760_000_000),
        ]
    )
    session.commit()
    session.close()
    generator.close()


def test_get_all_prices_by_ticker(client):
    insert_prices()
    response = client.get("/prices", params={"ticker": "BTC_USD"})
    assert response.status_code == 200
    assert len(response.json()) == 2
    assert response.json()[0]["price"] == 65100.0


def test_get_latest_price(client):
    insert_prices()
    response = client.get("/prices/latest", params={"ticker": "btc_usd"})
    assert response.status_code == 200
    assert response.json()["price"] == 65100.0


def test_get_price_history_for_utc_date(client):
    requested = datetime.fromtimestamp(1_760_000_000, tz=UTC).date().isoformat()
    insert_prices()
    response = client.get("/prices/by-date", params={"ticker": "btc_usd", "on": requested})
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_missing_ticker_is_rejected(client):
    assert client.get("/prices").status_code == 422


def test_unknown_ticker_is_rejected(client):
    response = client.get("/prices/latest", params={"ticker": "doge_usd"})
    assert response.status_code == 422
