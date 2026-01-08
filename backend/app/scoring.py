import numpy as np
from typing import List
from .models import FinancialData, StockScore

def calculate_score(data: FinancialData) -> StockScore:
    breakdown = {}
    years_count = len(data.fiscal_years)
    
    # We analyze up to the last 5 years available.
    # If less than 2 years, we cannot determine trend -> Score 0.
    if years_count < 2:
        return StockScore(
            ticker=data.ticker,
            total_score=0.0,
            breakdown={k: 0.0 for k in [
                "revenue", "eps", "total_assets", "operating_cf", 
                "cash_equivalents", "roe", "equity_ratio", 
                "dividend_ps", "dividend_payout_ratio"
            ]},
            financial_data=data
        )

    # Helper: Calculate Slope
    def get_slope(values: List[float]) -> float:
        if len(values) < 2:
            return 0.0
        x = np.arange(len(values))
        y = np.array(values)
        slope, _ = np.polyfit(x, y, 1)
        return slope

    # Helper checks
    def is_right_shoulder_up(values: List[float]) -> bool:
        return get_slope(values) > 0

    # 1. Revenue (15 pts) - Trend Up
    # "経常収益直近3〜5年で右肩上がりか"
    if is_right_shoulder_up(data.revenue):
        breakdown["revenue"] = 15.0
    else:
        breakdown["revenue"] = 0.0

    # 2. EPS (15 pts) - Trend Up
    if is_right_shoulder_up(data.eps):
        breakdown["eps"] = 15.0
    else:
        breakdown["eps"] = 0.0

    # 3. Total Assets (10 pts) - Trend Up (Increase)
    if is_right_shoulder_up(data.total_assets):
        breakdown["total_assets"] = 10.0
    else:
        breakdown["total_assets"] = 0.0

    # 4. Operating CF (10 pts) - Always Positive AND Trend Up
    # "常にプラスかつ増加傾向か"
    is_ocf_positive = all(v > 0 for v in data.operating_cf)
    if is_ocf_positive and is_right_shoulder_up(data.operating_cf):
        breakdown["operating_cf"] = 10.0
    else:
        breakdown["operating_cf"] = 0.0

    # 5. Cash (10 pts) - Not Decreasing & Piling up (Trend Up)
    # "減少しておらず、積み上がっているか"
    # "Not decreasing" could imply strict monotonicity, but "piling up" implies growth.
    # We'll check Slope > 0 again for "piling up".
    if is_right_shoulder_up(data.cash_equivalents):
        breakdown["cash_equivalents"] = 10.0
    else:
        breakdown["cash_equivalents"] = 0.0

    # 6. ROE (10 pts) - >= 7% Maintained
    # "7%以上を維持しているか"
    if all(v >= 7.0 for v in data.roe):
        breakdown["roe"] = 10.0
    else:
        breakdown["roe"] = 0.0

    # 7. Equity Ratio (10 pts) - >= 50% Maintained
    if all(v >= 50.0 for v in data.equity_ratio):
        breakdown["equity_ratio"] = 10.0
    else:
        breakdown["equity_ratio"] = 0.0

    # 8. Dividend (10 pts) - Non-decreasing AND Trend Up
    # "非減配（維持または増配）かつ右肩上がりか"
    # Check non-decreasing
    is_non_decreasing = True
    for i in range(1, len(data.dividend_ps)):
        if data.dividend_ps[i] < data.dividend_ps[i-1]:
            is_non_decreasing = False
            break
    
    # Check trend up
    is_div_growing = is_right_shoulder_up(data.dividend_ps)
    
    if is_non_decreasing and is_div_growing:
        breakdown["dividend_ps"] = 10.0
    else:
        breakdown["dividend_ps"] = 0.0

    # 9. Payout Ratio (10 pts) - <= 40%
    # "40%以下に抑えられているか"
    # If any year exceeds 40, fail (Strict).
    if all(v <= 40.0 for v in data.dividend_payout_ratio):
        breakdown["dividend_payout_ratio"] = 10.0
    else:
        breakdown["dividend_payout_ratio"] = 0.0

    total_score = sum(breakdown.values())
    
    return StockScore(
        ticker=data.ticker,
        total_score=total_score,
        breakdown=breakdown,
        financial_data=data
    )
