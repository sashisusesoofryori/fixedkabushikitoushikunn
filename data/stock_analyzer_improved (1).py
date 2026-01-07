import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import yfinance as yf
from datetime import datetime
import json
from pathlib import Path
import time

# ページ設定
st.set_page_config(
    page_title="株最強分析くん",
    page_icon="📊",
    layout="wide"
)

# データ保存用ディレクトリ
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)
HISTORY_FILE = DATA_DIR / "analysis_history.json"

# スタイル設定
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        color: #1f77b4;
        margin-bottom: 2rem;
    }
    .metric-card {
        padding: 1.5rem;
        border-radius: 0.5rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        margin: 0.5rem 0;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

class StockAnalyzer:
    def __init__(self):
        pass
    
    def fetch_stock_data(self, stock_code):
        """yfinanceで株価と企業情報を取得（レート制限対策付き）"""
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                ticker = f"{stock_code}.T"
                stock = yf.Ticker(ticker)
                
                # レート制限対策：各リクエスト間に遅延を入れる
                time.sleep(1)
                
                # 株価履歴を先に取得（最も重要なデータ）
                hist = stock.history(period="5y")
                
                if hist.empty:
                    st.error(f"❌ 銘柄コード {stock_code} のデータが見つかりません。正しいコードか確認してください。")
                    return None
                
                time.sleep(1)
                
                # 企業情報取得
                try:
                    info = stock.info
                    company_name = info.get('longName', info.get('shortName', f'銘柄{stock_code}'))
                except:
                    # infoの取得に失敗しても株価データがあれば続行
                    info = {}
                    company_name = f'銘柄{stock_code}'
                    st.warning("⚠️ 企業情報の一部が取得できませんでしたが、株価データは表示します")
                
                return {
                    'company_name': company_name,
                    'info': info,
                    'history': hist
                }
                
            except Exception as e:
                error_msg = str(e)
                
                if "Too Many Requests" in error_msg or "Rate limit" in error_msg:
                    if attempt < max_retries - 1:
                        wait_time = retry_delay * (attempt + 1)
                        st.warning(f"⏳ レート制限により待機中... {wait_time}秒後に再試行します（{attempt + 1}/{max_retries}）")
                        time.sleep(wait_time)
                        continue
                    else:
                        st.error("❌ Yahoo Financeのレート制限に達しました。数分後に再度お試しください。")
                        return None
                else:
                    st.error(f"データ取得エラー: {error_msg}")
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay)
                        continue
                    return None
        
        return None
    
    def calculate_simple_score(self, data):
        """Yahoo Financeデータから簡易スコアを算出"""
        if not data or not data.get('info'):
            # infoがない場合は株価データのみで簡易評価
            return 50, {'note': '企業情報が取得できないため、標準スコアを表示'}
        
        info = data['info']
        score_details = {}
        
        # 1. PER評価 (20点)
        pe_ratio = info.get('trailingPE', info.get('forwardPE', None))
        if pe_ratio and 5 < pe_ratio < 25:
            score_details['pe_ratio'] = 20
        elif pe_ratio:
            score_details['pe_ratio'] = 10
        else:
            score_details['pe_ratio'] = 0
        
        # 2. PBR評価 (20点)
        pb_ratio = info.get('priceToBook', None)
        if pb_ratio and pb_ratio < 2:
            score_details['pb_ratio'] = 20
        elif pb_ratio and pb_ratio < 3:
            score_details['pb_ratio'] = 10
        else:
            score_details['pb_ratio'] = 0
        
        # 3. ROE評価 (20点)
        roe = info.get('returnOnEquity', None)
        if roe and roe > 0.10:  # 10%以上
            score_details['roe'] = 20
        elif roe and roe > 0.05:  # 5%以上
            score_details['roe'] = 10
        else:
            score_details['roe'] = 0
        
        # 4. 配当利回り (20点)
        div_yield = info.get('dividendYield', None)
        if div_yield and div_yield > 0.03:  # 3%以上
            score_details['dividend'] = 20
        elif div_yield and div_yield > 0.01:  # 1%以上
            score_details['dividend'] = 10
        else:
            score_details['dividend'] = 0
        
        # 5. 自己資本比率 (20点)
        debt_to_equity = info.get('debtToEquity', None)
        if debt_to_equity is not None and debt_to_equity < 50:
            score_details['equity'] = 20
        elif debt_to_equity is not None and debt_to_equity < 100:
            score_details['equity'] = 10
        else:
            score_details['equity'] = 0
        
        total_score = sum(score_details.values())
        return total_score, score_details

def load_history():
    """分析履歴を読み込み"""
    if HISTORY_FILE.exists():
        with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_history(stock_code, company_name, score, score_details):
    """分析履歴を保存"""
    history = load_history()
    entry = {
        'stock_code': stock_code,
        'company_name': company_name,
        'score': score,
        'score_details': score_details,
        'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    history.append(entry)
    history = history[-100:]  # 最新100件のみ
    
    with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

def create_score_gauge(score):
    """スコアゲージチャート"""
    color = '#ff4444' if score < 40 else '#ffaa00' if score < 60 else '#00cc66'
    
    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = score,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': "総合スコア", 'font': {'size': 24}},
        gauge = {
            'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "darkblue"},
            'bar': {'color': color},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                {'range': [0, 40], 'color': '#ffcccc'},
                {'range': [40, 60], 'color': '#fff5cc'},
                {'range': [60, 100], 'color': '#ccffcc'}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 80
            }
        }
    ))
    
    fig.update_layout(height=400, margin=dict(l=20, r=20, t=60, b=20))
    return fig

def create_candlestick_chart(hist, timeframe_label):
    """ローソク足チャート作成"""
    if hist is None or hist.empty:
        return None
    
    fig = go.Figure(data=[go.Candlestick(
        x=hist.index,
        open=hist['Open'],
        high=hist['High'],
        low=hist['Low'],
        close=hist['Close'],
        name='株価'
    )])
    
    # 移動平均線を追加
    if len(hist) >= 25:
        ma25 = hist['Close'].rolling(window=25).mean()
        fig.add_trace(go.Scatter(
            x=hist.index,
            y=ma25,
            mode='lines',
            name='25日移動平均',
            line=dict(color='orange', width=1)
        ))
    
    if len(hist) >= 75:
        ma75 = hist['Close'].rolling(window=75).mean()
        fig.add_trace(go.Scatter(
            x=hist.index,
            y=ma75,
            mode='lines',
            name='75日移動平均',
            line=dict(color='blue', width=1)
        ))
    
    fig.update_layout(
        title=f'株価推移 ({timeframe_label})',
        yaxis_title='株価 (円)',
        xaxis_title='日付',
        height=500,
        template='plotly_white',
        xaxis_rangeslider_visible=False,
        hovermode='x unified'
    )
    return fig

# メインアプリケーション
st.markdown('<div class="main-header">📊 株最強分析くん</div>', unsafe_allow_html=True)

# 使用上の注意
st.info("💡 **ヒント**: Yahoo Financeのレート制限により、連続して複数の銘柄を分析する場合は、各分析の間に数秒お待ちください。")

analyzer = StockAnalyzer()

# サイドバー
with st.sidebar:
    st.header("⚙️ 設定")
    stock_code = st.text_input("銘柄コード", value="", placeholder="例: 7203")
    
    st.markdown("---")
    st.subheader("📈 株価表示期間")
    
    timeframe_options = {
        "1週間": "1wk",
        "1ヶ月": "1mo",
        "3ヶ月": "3mo",
        "6ヶ月": "6mo",
        "1年": "1y",
        "5年": "5y",
        "全期間": "max"
    }
    
    timeframe = st.selectbox(
        "期間を選択",
        list(timeframe_options.keys()),
        index=4
    )
    
    analyze_button = st.button("🔍 分析開始", type="primary", use_container_width=True)
    
    st.markdown("---")
    st.subheader("📜 分析履歴")
    history = load_history()
    if history:
        for entry in reversed(history[-5:]):
            with st.expander(f"{entry['company_name']} ({entry['stock_code']})"):
                st.metric("スコア", f"{entry['score']}点")
                st.caption(entry['date'])
    else:
        st.info("履歴がありません")

# メインエリア
if analyze_button and stock_code:
    with st.spinner('データ取得中...'):
        data = analyzer.fetch_stock_data(stock_code)
        
        if data is None:
            st.error("❌ データの取得に失敗しました")
            st.stop()
        
        score, score_details = analyzer.calculate_simple_score(data)
        save_history(stock_code, data['company_name'], score, score_details)
    
    st.success(f"✅ {data['company_name']} の分析が完了しました!")
    
    # 企業情報表示
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        market_cap = data['info'].get('marketCap', 0)
        st.metric("時価総額", f"{market_cap/1e12:.2f}兆円" if market_cap > 1e12 else f"{market_cap/1e9:.2f}億円")
    
    with col2:
        pe = data['info'].get('trailingPE', 0)
        st.metric("PER", f"{pe:.2f}" if pe else "N/A")
    
    with col3:
        pb = data['info'].get('priceToBook', 0)
        st.metric("PBR", f"{pb:.2f}" if pb else "N/A")
    
    with col4:
        div_yield = data['info'].get('dividendYield', 0)
        st.metric("配当利回り", f"{div_yield*100:.2f}%" if div_yield else "N/A")
    
    st.markdown("---")
    
    # 株価チャート表示
    if data['history'] is not None and not data['history'].empty:
        st.subheader("💹 株価チャート")
        
        # 期間でフィルタリング
        period = timeframe_options[timeframe]
        if period != "max":
            filtered_hist = data['history'].tail(
                {'1wk': 5, '1mo': 22, '3mo': 66, '6mo': 132, '1y': 252, '5y': 1260}.get(period, len(data['history']))
            )
        else:
            filtered_hist = data['history']
        
        chart = create_candlestick_chart(filtered_hist, timeframe)
        if chart:
            st.plotly_chart(chart, use_container_width=True)
        
        # 株価統計
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("現在値", f"{filtered_hist['Close'].iloc[-1]:.2f}円")
        with col2:
            change = filtered_hist['Close'].iloc[-1] - filtered_hist['Close'].iloc[-2]
            change_pct = (change / filtered_hist['Close'].iloc[-2]) * 100
            st.metric("前日比", f"{change:.2f}円", f"{change_pct:+.2f}%")
        with col3:
            st.metric("期間高値", f"{filtered_hist['High'].max():.2f}円")
        with col4:
            st.metric("期間安値", f"{filtered_hist['Low'].min():.2f}円")
    
    st.markdown("---")
    
    # スコア表示
    st.subheader("🎯 総合評価スコア")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.plotly_chart(create_score_gauge(score), use_container_width=True)
    
    # 評価コメント
    if score >= 80:
        st.success("🌟 優良企業!非常に高い投資価値が期待できます。")
    elif score >= 60:
        st.info("👍 良好な財務状態です。")
    elif score >= 40:
        st.warning("⚠️ 一部改善の余地があります。")
    else:
        st.error("❌ 慎重な判断が必要です。")
    
    # 詳細スコア
    st.subheader("📋 詳細評価")
    
    criteria = {
        'pe_ratio': ('PER評価', '5-20倍が理想', 20),
        'pb_ratio': ('PBR評価', '2倍以下', 20),
        'roe': ('ROE', '7%以上', 20),
        'dividend': ('配当利回り', '2%以上', 20),
        'equity': ('財務健全性', '自己資本比率', 20)
    }
    
    cols = st.columns(3)
    for idx, (key, (name, criteria_text, max_score)) in enumerate(criteria.items()):
        with cols[idx % 3]:
            achieved = score_details.get(key, 0)
            status = "✅ 合格" if achieved == max_score else "❌ 不合格"
            color = "#d4edda" if achieved == max_score else "#f8d7da"
            st.markdown(f"""
            <div style="padding: 1rem; border-radius: 0.5rem; background-color: {color}; margin: 0.5rem 0;">
                <strong>{name}</strong><br>
                {status} ({achieved}/{max_score}点)<br>
                <small>基準: {criteria_text}</small>
            </div>
            """, unsafe_allow_html=True)

elif not stock_code and analyze_button:
    st.warning("⚠️ 銘柄コードを入力してください")
else:
    st.info("👈 サイドバーから銘柄コードを入力して分析を開始してください")
    
    with st.expander("📖 使い方ガイド"):
        st.markdown("""
        ### 銘柄コードの入力例
        - **トヨタ自動車**: 7203
        - **ソニーグループ**: 6758
        - **任天堂**: 7974
        - **キーエンス**: 6861
        
        ### スコアリング基準（Yahoo Finance版）
        
        1. **PER評価** (20点) - 5-20倍が適正範囲
        2. **PBR評価** (20点) - 2倍以下が割安
        3. **ROE** (20点) - 7%以上で優良
        4. **配当利回り** (20点) - 2%以上
        5. **財務健全性** (20点) - 負債比率が低い
        
        ### 評価基準
        - **80点以上**: 優良企業
        - **60-79点**: 良好な財務状態
        - **40-59点**: 改善の余地あり
        - **39点以下**: 慎重な判断が必要
        """)

# フッター
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; font-size: 0.9rem;'>
    <p>💡 このアプリはYahoo Financeから取得したデータに基づく簡易評価システムです。</p>
    <p>投資判断は自己責任でお願いします。</p>
</div>
""", unsafe_allow_html=True)