from pydantic import BaseModel
from typing import List, Optional, Dict

class FinancialData(BaseModel):
    ticker: str
    fiscal_years: List[str]  # e.g., ["2021", "2022", ...]
    
    # 9 Scoring Metrics Data (Lists corresponding to fiscal_years)
    # 1. Revenue (经常收益 / 売上高)
    revenue: List[float]
    # 2. EPS
    eps: List[float]
    # 3. Total Assets
    total_assets: List[float]
    # 4. Operating CF
    operating_cf: List[float]
    # 5. Cash & Equivalents
    cash_equivalents: List[float]
    # 6. ROE
    roe: List[float]
    # 7. Equity Ratio
    equity_ratio: List[float]
    # 8. Dividend per Share
    dividend_ps: List[float]
    # 9. Dividend Payout Ratio
    dividend_payout_ratio: List[float]
    
    # Optional extra data
    stock_price: Optional[float] = None
    
class StockScore(BaseModel):
    ticker: str
    total_score: float
    breakdown: Dict[str, float] # 9 items
    financial_data: FinancialData
