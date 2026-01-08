import requests
from bs4 import BeautifulSoup

def inspect_irbank():
    url = "https://irbank.net/8411/kessan"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    resp = requests.get(url, headers=headers)
    print(f"Status: {resp.status_code}")
    
    soup = BeautifulSoup(resp.content, "html.parser")
    
    # Try to find tables
    # IR Bank often has tables with class "csst" or similar, or just <table>
    tables = soup.find_all("table")
    print(f"Found {len(tables)} tables")
    
    for i, table in enumerate(tables):
        rows = table.find_all("tr")
        print(f"--- Table {i} ---")
        for j, row in enumerate(rows):
            if j > 5: break # Only first 5 rows
            cols = [c.get_text(strip=True) for c in row.find_all(["th", "td"])]
            print(f"Row {j}: {cols}")

if __name__ == "__main__":
    inspect_irbank()
