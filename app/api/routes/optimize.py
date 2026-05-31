from fastapi import APIRouter, UploadFile, File, Form, HTTPException
import pandas as pd

from app.models.request_model import OptimizationRequest
from app.services.optimizer_service import optimize_portfolio

router = APIRouter()


def _parse_excel_to_request(file: UploadFile, strategy: str, factor_file: UploadFile = None) -> OptimizationRequest:
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

    # Accept optional dividend_yield column; remaining columns are treated as returns
    return_columns = [c for c in df.columns if c not in required_columns and c != 'dividend_yield']
    if not return_columns:
        raise HTTPException(
            status_code=400,
            detail="Excel file must include one or more return columns in addition to ticker, security_name, and current_weight"
        )

    securities = []
    for index, row in df.iterrows():
        try:
            returns = [float(row[col]) for col in return_columns]
            div_yield = None
            if 'dividend_yield' in df.columns and not pd.isna(row['dividend_yield']):
                div_yield = float(row['dividend_yield'])
            security = {
                "ticker": str(row["ticker"]),
                "security_name": str(row["security_name"]),
                "current_weight": float(row["current_weight"]),
                "returns": returns,
                "dividend_yield": div_yield,
            }
            securities.append(security)
        except Exception as exc:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid data in row {index + 2}: {exc}"
            )

    factor_returns = None
    if factor_file is not None:
        try:
            fdf = pd.read_excel(factor_file.file)
            # expect columns for each factor; if there is a date column it will be ignored
            factor_cols = [c for c in fdf.columns if c.lower() != 'date']
            factor_returns = {c: list(fdf[c].astype(float).values) for c in factor_cols}
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"Failed to read factor file: {exc}")

    return OptimizationRequest(strategy=strategy, securities=securities, factor_returns=factor_returns)


@router.post("/optimize")
def optimize(request: OptimizationRequest):
    try:
        return optimize_portfolio(request)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/optimize/upload")
def optimize_upload(
    strategy: str = Form("equal_weight"),
    file: UploadFile = File(...),
    factor_file: UploadFile = File(None),
    constraints: str = Form(None),
):
    import json
    from app.models.request_model import Constraints
    parsed_constraints = None
    if constraints:
        try:
            parsed_constraints = Constraints.parse_raw(constraints)
        except Exception:
            try:
                parsed_constraints = Constraints(**json.loads(constraints))
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Invalid constraints JSON: {e}")

    # Check for multi-sheet Data.xlsx format
    try:
        xls = pd.ExcelFile(file.file)
        if 'Fund Info' in xls.sheet_names and 'Fund Returns' in xls.sheet_names:
            file.file.seek(0)
            with open("Data.xlsx", "wb") as f_out:
                f_out.write(file.file.read())
            
            df_info = pd.read_excel(xls, sheet_name='Fund Info')
            securities = []
            for _, row in df_info.iterrows():
                securities.append({
                    "ticker": str(row["ticker"]),
                    "security_name": str(row["fund_name"]),
                    "current_weight": 20.0,  # Default weight
                    "returns": None,
                    "dividend_yield": float(row["dividend_yield"]) if not pd.isna(row["dividend_yield"]) else None
                })
            
            req = OptimizationRequest(strategy=strategy, securities=securities, constraints=parsed_constraints)
            try:
                return optimize_portfolio(req)
            except Exception as exc:
                raise HTTPException(status_code=400, detail=str(exc))
    except Exception:
        pass

    file.file.seek(0)
    try:
        req = _parse_excel_to_request(file, strategy, factor_file)
        if parsed_constraints:
            req.constraints = parsed_constraints
        return optimize_portfolio(req)
    except Exception as exc:
        if isinstance(exc, HTTPException):
            raise exc
        raise HTTPException(status_code=400, detail=str(exc))