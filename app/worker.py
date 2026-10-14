from celery import Celery

from app.core.config import get_settings

settings = get_settings()
celery_app = Celery("price_tracker", broker=settings.redis_url, backend=settings.redis_url)
celery_app.conf.update(
    timezone="UTC",
    enable_utc=True,
    beat_schedule={
        "collect-index-prices-every-minute": {
            "task": "app.worker.collect_prices",
            "schedule": 60.0,
        }
    },
    task_routes={"app.worker.collect_prices": {"queue": "prices"}},
)


@celery_app.task(
    name="app.worker.collect_prices",
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=5,
)
def collect_prices() -> dict[str, int]:
    import asyncio
    import time

    from app.clients import DeribitClient
    from app.db.session import SessionLocal
    from app.repositories import PriceRepository

    async def fetch_all() -> dict[str, float]:
        client = DeribitClient(settings.deribit_base_url)
        tickers = ("btc_usd", "eth_usd")
        results = await asyncio.gather(*(client.get_index_price(ticker) for ticker in tickers))
        return dict(zip(tickers, results, strict=True))

    prices = asyncio.run(fetch_all())
    timestamp = int(time.time())
    with SessionLocal() as session:
        repository = PriceRepository(session)
        for ticker, price in prices.items():
            repository.add(ticker, price, timestamp)
    return {"collected": len(prices)}
