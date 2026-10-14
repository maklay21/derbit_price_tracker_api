import aiohttp


class DeribitClient:
    def __init__(self, base_url: str, timeout_seconds: float = 10.0) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = aiohttp.ClientTimeout(total=timeout_seconds)

    async def get_index_price(self, ticker: str) -> float:
        async with aiohttp.ClientSession(timeout=self._timeout) as session:
            async with session.get(
                f"{self._base_url}/public/get_index_price", params={"index_name": ticker}
            ) as response:
                response.raise_for_status()
                payload = await response.json()
        try:
            price = float(payload["result"]["index_price"])
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError("Deribit returned an invalid index price response") from error
        if price <= 0:
            raise ValueError("Deribit returned a non-positive index price")
        return price
