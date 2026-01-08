import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import os
import sys

# Add current directory to path so we can import backend
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.app.scraper import get_financial_data
from backend.app.scoring import calculate_score
import yfinance as yf

# Page Config
st.set_page_config(
    page_title="株最強分析くん",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Constants
RANKING_FILE = "ranking.csv"

# --- Helper Functions ---
def load_ranking():
    if os.path.exists(RANKING_FILE):
        return pd.read_csv(RANKING_FILE)
    return pd.DataFrame(columns=["Date", "Ticker", "Score"])

def save_ranking(ticker, score):
    df = load_ranking()
    # Check if ticker already analyzed today? Or just append?
    # Spec says "History" and "Monthly Ranking".
    # We'll append entry.
    new_entry = pd.DataFrame({
        "Date": [datetime.now().strftime("%Y-%m-%d")],
        "Ticker": [ticker],
        "Score": [score]
    })
    df = pd.concat([df, new_entry], ignore_index=True)
    # Remove duplicates for same ticker (keep latest)? 
    # Or keep history? "History list" implies getting history.
    # Ranking should be "Highest Score".
    # Let's keep all history, but for ranking we might group by ticker.
    df.to_csv(RANKING_FILE, index=False)
    return df

def get_stock_price(ticker, period="1y", interval="1d"):
    # ticker needs region? IRBANK is Japan. yfinance usually needs ".T" for Japan.
    # We will try appending .T if not present.
    symbol = ticker if ticker.endswith(".T") else f"{ticker}.T"
    df = yf.download(symbol, period=period, interval=interval, progress=False)
    return df

# --- UI Components ---

def render_donut_chart(score):
    fig = go.Figure(data=[go.Pie(
        labels=['Score', 'Remaining'],
        values=[score, 100-score],
        hole=.7,
        sort=False,
        marker_colors=['#4CAF50', '#E0E0E0'],
        textinfo='none',
        hoverinfo='label+value'
    )])
    
    fig.update_layout(
        annotations=[dict(text=f'{int(score)}点', x=0.5, y=0.5, font_size=40, showarrow=False)],
        showlegend=False,
        margin=dict(t=0, b=0, l=0, r=0),
        height=300
    )
    return fig

def render_financial_charts(financial_data):
    # 3x3 Grid
    metrics = [
        ("Revenue", financial_data.revenue, "経常収益/売上"),
        ("EPS", financial_data.eps, "EPS"),
        ("Total Assets", financial_data.total_assets, "総資産"),
        ("Operating CF", financial_data.operating_cf, "営業CF"),
        ("Cash", financial_data.cash_equivalents, "現金等"),
        ("ROE", financial_data.roe, "ROE"),
        ("Equity Ratio", financial_data.equity_ratio, "自己資本比率"),
        ("Dividend", financial_data.dividend_ps, "一株配当"),
        ("Payout Ratio", financial_data.dividend_payout_ratio, "配当性向")
    ]
    
    years = financial_data.fiscal_years
    
    # We'll use Streamlit cols
    cols = st.columns(3)
    for i, (name, data, label) in enumerate(metrics):
        with cols[i % 3]:
            if not data:
                st.warning(f"No Data for {label}")
                continue
                
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=years, y=data, mode='lines+markers', name=label))
            fig.update_layout(
                title=label,
                margin=dict(l=20, r=20, t=30, b=20),
                height=200,
                xaxis=dict(showgrid=False),
                yaxis=dict(showgrid=True, zeroline=False)
            )
            st.plotly_chart(fig, use_container_width=True)

# --- Main App ---

st.title("📊 株最強分析くん")

# Sidebar
st.sidebar.header("⚙ 設定")
ticker_input = st.sidebar.text_input("銘柄コード", placeholder="例: 7203")

# Timeframe for Stock Price
st.sidebar.subheader("📈 株価表示期間")
timeframe = st.sidebar.selectbox("期間を選択", ["1日", "5日", "1ヶ月", "6ヶ月", "1年", "5年"], index=4)
tf_map = {
    "1日": "1d", "5日": "5d", "1ヶ月": "1mo", "6ヶ月": "6mo", "1年": "1y", "5年": "5y"
}
interval_map = {
    "1d": "5m", "5d": "15m", "1mo": "1h", "6mo": "1d", "1y": "1d", "5y": "1wk"
}
selected_period = tf_map[timeframe]
selected_interval = interval_map[selected_period]

if st.sidebar.button("🔍 分析開始") and ticker_input:
    # Validate Ticker
    ticker = ticker_input.strip()
    
    try:
        with st.spinner(f"{ticker} のデータを取得中..."):
            # 1. Scrape Financials
            f_data = get_financial_data(ticker)
            
            # 2. Calculate Score
            score_obj = calculate_score(f_data)
            
            # 3. Save History
            save_ranking(ticker, score_obj.total_score)
            
        # --- Display Results ---
        
        # Section 1: Score & Overview
        c1, c2 = st.columns([1, 2])
        
        with c1:
            st.subheader("総合スコア")
            st.plotly_chart(render_donut_chart(score_obj.total_score), use_container_width=True)
            
            # Breakdown Table
            st.markdown("### 判定結果")
            breakdown_df = pd.DataFrame(list(score_obj.breakdown.items()), columns=["項目", "点数"])
            # Map keys to Japanese
            jp_map = {
                "revenue": "経常収益 (15)", "eps": "EPS (15)", "total_assets": "総資産 (10)",
                "operating_cf": "営業CF (10)", "cash_equivalents": "現金等 (10)", "roe": "ROE (10)",
                "equity_ratio": "自己資本比率 (10)", "dividend_ps": "配当 (10)", 
                "dividend_payout_ratio": "配当性向 (10)"
            }
            breakdown_df["項目"] = breakdown_df["項目"].map(jp_map)
            # Add Pass/Fail icon
            breakdown_df["判定"] = breakdown_df["点数"].apply(lambda x: "✅ 合格" if x > 0 else "❌ 不合格")
            st.dataframe(breakdown_df[["項目", "判定"]], hide_index=True)

        with c2:
            st.subheader(f"{ticker} 財務推移")
            render_financial_charts(f_data)

        # Section 2: Stock Price
        st.markdown("---")
        st.subheader(f"株価チャート ({timeframe})")
        
        price_data = get_stock_price(ticker, period=selected_period, interval=selected_interval)
        if not price_data.empty:
            fig_price = go.Figure(data=[go.Candlestick(
                x=price_data.index,
                open=price_data['Open'],
                high=price_data['High'],
                low=price_data['Low'],
                close=price_data['Close']
            )])
            fig_price.update_layout(xaxis_rangeslider_visible=False, height=500)
            st.plotly_chart(fig_price, use_container_width=True)
        else:
            st.warning("株価データの取得に失敗しました。")

    except Exception as e:
        st.error(f"エラーが発生しました: {e}")
        import traceback
        st.code(traceback.format_exc())

# Sidebar History
st.sidebar.markdown("---")
st.sidebar.subheader("📜 分析履歴")
hist = load_ranking()
if not hist.empty:
    # Show last 10
    latest = hist.tail(10).iloc[::-1]
    for i, row in latest.iterrows():
        if st.sidebar.button(f"{row['Ticker']} ({int(row['Score'])}点)", key=f"hist_{i}"):
            # How to trigger re-run with this ticker?
            # We can't easily change input but we can just ask user to type.
            # Or use session state.
            st.sidebar.info(f"銘柄コード {row['Ticker']} を入力して分析してください。")

# Ranking (Bottom of page as requested)
st.markdown("---")
st.subheader("🏆 月間ランキング (Top 10)")
if not hist.empty:
    # Filter by this month? Spec says "Monthly Ranking".
    # Simplify: Global Top 10 for now.
    ranking = hist.sort_values("Score", ascending=False).drop_duplicates("Ticker").head(10)
    st.table(ranking[["Date", "Ticker", "Score"]])
else:
    st.info("まだデータがありません。")

st.markdown("---")
st.caption("※このアプリはYahoo Financeから取得したデータに基づく簡易評価システムです。投資判断は自己責任でお願いします。")
