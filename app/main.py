from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from app.api.routes.optimize import router

app = FastAPI(
    title="Portfolio Optimizer API",
    version="1.0.0",
    docs_url="/swagger",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

@app.get("/")
def read_root():
    return {"message": "Portfolio Optimizer API is running"}

@app.get("/docs", include_in_schema=False)
def docs_redirect():
    return RedirectResponse(url="/swagger")

app.include_router(router)





