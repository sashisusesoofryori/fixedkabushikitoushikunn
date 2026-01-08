from app.scraper import get_financial_data
from app.scoring import calculate_score
import json

def test_real_data():
    ticker = "7203" # Toyota
    print(f"Fetching data for {ticker}...")
    try:
        data = get_financial_data(ticker)
        print("Data fetched successfully!")
        
        # Print first year and last year
        print(f"Years: {data.fiscal_years}")
        
        # Check metrics populated
        print(f"Ordinary Income: {data.ordinary_income}")
        print(f"EPS: {data.eps}")
        print(f"ROE: {data.roe}")
        
        # Calculate score
        score = calculate_score(data)
        print(f"Total Score: {score.total_score}")
        print("Breakdown:")
        print(json.dumps(score.breakdown, indent=2))
        
    except Exception as e:
        print(f"Failed to fetch/score: {e}")

if __name__ == "__main__":
    test_real_data()
