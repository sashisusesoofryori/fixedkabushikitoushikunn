from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from .scraper import get_financial_data
from .scoring import calculate_score
from .models import StockScore

app = FastAPI(title="Stock Strongest Analysis API")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all for dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Hello from Stock Analysis API"}

@app.get("/api/analyze/{ticker}", response_model=StockScore)
def analyze_stock(ticker: str):
    try:
        data = get_financial_data(ticker)
        score = calculate_score(data)
        return score
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

