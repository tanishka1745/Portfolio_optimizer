from fastapi import APIRouter, UploadFile, File, Form, HTTPException
import pandas as pd

from app.models.request_model import OptimizationRequest
from app.services.optimizer_service import optimize_portfolio

router = APIRouter()


def _parse_excel_to_request(file: UploadFile, strategy: str) -> OptimizationRequest:
    try:
        df = pd.read_excel(file.file)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Failed to read Excel file: {exc}")

    required_columns = {"ticker", "security_name", "current_weight"}
    missing_columns = required_columns.difference(df.columns)
    if missing_columns:
        raise HTTPException(
            status_code=400,
            detail=f"Missing required columns: {', '.join(sorted(missing_columns))}"
        )

    return_columns = [c for c in df.columns if c not in required_columns]
    if not return_columns:
        raise HTTPException(
            status_code=400,
            detail="Excel file must include one or more return columns in addition to ticker, security_name, and current_weight"
        )

    securities = []
    for index, row in df.iterrows():
        try:
            returns = [float(row[col]) for col in return_columns]
            security = {
                "ticker": str(row["ticker"]),
                "security_name": str(row["security_name"]),
                "current_weight": float(row["current_weight"]),
                "returns": returns,
            }
            securities.append(security)
        except Exception as exc:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid data in row {index + 2}: {exc}"
            )

    return OptimizationRequest(strategy=strategy, securities=securities)


@router.post("/optimize")
def optimize(request: OptimizationRequest):
    return optimize_portfolio(request)


@router.post("/optimize/upload")
def optimize_upload(
    strategy: str = Form("equal_weight"),
    file: UploadFile = File(...),
):
    request = _parse_excel_to_request(file, strategy)
    return optimize_portfolio(request)