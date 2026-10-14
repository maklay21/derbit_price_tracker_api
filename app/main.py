from fastapi import FastAPI

from app.api.routes import router

app = FastAPI(
    title="Deribit Price Tracker API",
    description="Minute-level BTC and ETH index price history collected from Deribit.",
    version="0.1.0",
)
app.include_router(router)


@app.get("/health", tags=["operations"], summary="Liveness check")
def health() -> dict[str, str]:
    return {"status": "ok"}
