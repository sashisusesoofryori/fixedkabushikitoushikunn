import requests
import pandas as pd
import pickle
import os
import time
from datetime import datetime
from bs4 import BeautifulSoup
from .models import FinancialData

CACHE_DIR = "cache"
if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)

class IrBankScraper:
    def __init__(self):
        self.base_url = "https://irbank.net"

    def _get_cache_path(self, ticker: str) -> str:
        return os.path.join(CACHE_DIR, f"{ticker}.pkl")

    def _load_cache(self, ticker: str):
        path = self._get_cache_path(ticker)
        if os.path.exists(path):
            mtime = os.path.getmtime(path)
            if time.time() - mtime < 24 * 3600: # 24 hours
                with open(path, "rb") as f:
                    return pickle.load(f)
        return None

    def _save_cache(self, ticker: str, data: FinancialData):
        path = self._get_cache_path(ticker)
        with open(path, "wb") as f:
            pickle.dump(data, f)

    def scrape(self, ticker: str) -> FinancialData:
        # Check cache
        cached = self._load_cache(ticker)
        if cached:
            # Re-validate that cached data matches new model if possible, 
            # but usually pickle loads old class. 
            # To be safe, if we changed models, old cache might break or be partial.
            # We'll assume for now it's okay or user clears cache if needed.
            # Actually, pickle will fail nicely or we should re-scrape if model changed drastically.
            # Let's try to return it (Basic check).
            if hasattr(cached, "revenue"):
                print(f"Loaded {ticker} from cache")
                return cached
            # If missing new fields, fall through to scrape
            print(f"Cache invalid for {ticker}, re-scraping...")

        url = f"https://irbank.net/{ticker}/kessan"
        print(f"Scraping {url}...")
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        try:
            resp = requests.get(url, headers=headers)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.content, "html.parser")
            
            # Find the main table
            table = None
            tables = soup.find_all("table")
            header_map = {}
            
            # New mapping for 9 metrics
            aliases = {
                "revenue": [
                    "売上高", "営業収益", "経常収益", "売上" # Banks use Ordinary Income (経常収益)
                ],
                "eps": ["EPS", "一株利益", "基本的1株当たり当期利益", "一株当たり当期純利益"],
                "total_assets": ["総資産", "資産合計"],
                "operating_cf": ["営業CF", "営業キャッシュフロー", "営業活動によるキャッシュ・フロー", "営業活動によるキャッシュフロー"],
                "cash_equivalents": ["現金等", "現金残高", "現金及び現金同等物", "現金及び預金"],
                "roe": ["ROE", "自己資本利益率", "親会社所有者帰属持分当期利益率", "当期純利益率"],
                "equity_ratio": ["自己資本比率", "親会社所有者帰属持分比率", "資本比率"], 
                "dividend_ps": ["配当", "一株配当", "1株当たり配当額"],
                "dividend_payout_ratio": ["配当性向", "配当性向(%)"]
            }

            for t in tables:
                # Check headers
                rows = t.find_all("tr")
                if not rows: continue
                
                # Check first row for headers
                header_row = rows[0]
                cols = [c.get_text(strip=True) for c in header_row.find_all(["th", "td"])]
                
                if "年度" in cols:
                    table = t
                    # Build map
                    for idx, col_name in enumerate(cols):
                        for target, alias_list in aliases.items():
                            if target in header_map: continue # Already found
                            if any(a in col_name for a in alias_list):
                                header_map[target] = idx
                    break
            
            if not table:
                raise ValueError("Financial table not found")

            # Parse rows
            data_dict = {k: [] for k in aliases.keys()}
            years = []

            rows = table.find_all("tr")[1:] # Skip header
            for row in rows:
                cols = [c.get_text(strip=True) for c in row.find_all(["th", "td"])]
                # Check if we have enough columns for mapped indices
                max_idx = max(header_map.values()) if header_map else 0
                if len(cols) <= max_idx:
                    continue
                
                # Extract Year
                year_str = cols[0] 
                years.append(year_str)

                # Extract other metrics
                for target in aliases.keys():
                    if target in header_map:
                        idx = header_map[target]
                        val_str = cols[idx]
                        val = self._parse_value(val_str)
                        data_dict[target].append(val)
                    else:
                        data_dict[target].append(0.0)

            # IR Bank is Descending (New -> Old). Reverse to Ascending (Old -> New)
            years.reverse()
            for k in data_dict:
                data_dict[k].reverse()

            # Limit to last 10 years to be safe but usually prompt says "Last 3-5 years".
            # We keep all data here, scoring logic will slice.
            
            result = FinancialData(
                ticker=ticker,
                fiscal_years=years,
                revenue=data_dict["revenue"],
                eps=data_dict["eps"],
                total_assets=data_dict["total_assets"],
                operating_cf=data_dict["operating_cf"],
                cash_equivalents=data_dict["cash_equivalents"],
                roe=data_dict["roe"],
                equity_ratio=data_dict["equity_ratio"],
                dividend_ps=data_dict["dividend_ps"],
                dividend_payout_ratio=data_dict["dividend_payout_ratio"]
            )
            
            self._save_cache(ticker, result)
            time.sleep(1) # Polite delay
            return result
            
        except Exception as e:
            print(f"Error scraping {ticker}: {e}")
            raise e

    def _parse_value(self, text: str) -> float:
        if not text or text == "-" or text == "－":
            return 0.0
        
        clean = text.replace(",", "")
        
        unit = 1.0
        if "兆" in clean:
            clean = clean.replace("兆", "")
            unit = 1_000_000_000_000
        elif "億" in clean:
            clean = clean.replace("億", "")
            unit = 100_000_000
        elif "万" in clean:
            clean = clean.replace("万", "")
            unit = 10_000
        elif "%" in clean:
            clean = clean.replace("%", "")
            unit = 1.0 
        
        try:
            return float(clean) * unit
        except ValueError:
            return 0.0

scraper = IrBankScraper()

def get_financial_data(ticker: str) -> FinancialData:
    return scraper.scrape(ticker)
