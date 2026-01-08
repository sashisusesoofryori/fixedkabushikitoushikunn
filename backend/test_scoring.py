from app.models import FinancialData
from app.scoring import calculate_score

def test_scoring():
    # Case 1: All metrics perfect
    data_perfect = FinancialData(
        ticker="1111",
        fiscal_years=["2021", "2022", "2023", "2024", "2025"],
        ordinary_income=[100, 110, 120, 130, 140], # Up
        eps=[10, 12, 14, 16, 18], # Up
        total_assets=[1000, 1100, 1200, 1300, 1400], # Up
        operating_cf=[50, 60, 70, 80, 90], # Up & Positive
        cash_equivalents=[20, 30, 40, 50, 60], # Up
        roe=[8.0, 8.5, 9.0, 9.5, 10.0], # >= 7
        equity_ratio=[55.0, 56.0, 57.0, 58.0, 59.0], # >= 50
        dividend_ps=[10, 10, 12, 12, 15], # No decrease
        dividend_payout_ratio=[20.0, 20.0, 25.0, 25.0, 30.0] # <= 40
    )
    
    score_perfect = calculate_score(data_perfect)
    print(f"Perfect Score: {score_perfect.total_score} (Expected: 100.0)")
    assert score_perfect.total_score == 100.0

    # Case 2: Some failures
    data_bad = FinancialData(
        ticker="2222",
        fiscal_years=["2021", "2022", "2023", "2024", "2025"],
        ordinary_income=[140, 130, 120, 110, 100], # Down -> 0
        eps=[10, 12, 14, 16, 18], # Up -> 12.5
        total_assets=[1000, 1000, 1000, 1000, 1000], # Flat (Slope=0 or nearly 0, strictly speaking not "up"?) -> 0 check logic
        operating_cf=[-10, 20, 30, 40, 50], # Negative in past -> 0
        cash_equivalents=[60, 50, 40, 30, 20], # Down -> 0
        roe=[6.0, 6.0, 6.0, 6.0, 6.0], # < 7 -> 0
        equity_ratio=[40.0, 40.0, 40.0, 40.0, 40.0], # < 50 -> 0
        dividend_ps=[10, 9, 8, 7, 6], # Decrease -> 0
        dividend_payout_ratio=[20.0, 20.0, 20.0, 20.0, 20.0] # OK
    )
    
    score_bad = calculate_score(data_bad)
    print(f"Bad Score: {score_bad.total_score} (Expected: 12.5 from EPS only?)") 
    # Total Assets slope is 0 -> fail? Polyfit might give small num.
    # Operating CF negative -> fail.
    # Dividend decrease -> fail.
    
    for k, v in score_bad.breakdown.items():
        print(f"  {k}: {v}")

if __name__ == "__main__":
    test_scoring()
