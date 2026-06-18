import yfinance as yf
import logging
import os
import mplfinance as mpf
import random
import requests
import requests_cache
import pandas as pd

logger = logging.getLogger(__name__)

def get_yahoo_session():
    """Custom Crumb-Catcher to steal Yahoo cookies and bypass 429 blocks using Proxies."""
    session = requests_cache.CachedSession('yfinance_cache', expire_after=86400)
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    })
    
    # Dynamic Proxy Fetcher
    try:
        logger.info("Fetching free proxy list from ProxyScrape...")
        proxy_res = requests.get("https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=5000&country=US,CA,GB&ssl=all&anonymity=all", timeout=5)
        if proxy_res.status_code == 200:
            proxies = [p.strip() for p in proxy_res.text.split("\n") if p.strip()]
            if proxies:
                chosen_proxy = random.choice(proxies[:20]) # Pick from top 20 freshest proxies
                session.proxies.update({"http": f"http://{chosen_proxy}", "https": f"http://{chosen_proxy}"})
                logger.info(f"Assigned new proxy IP: {chosen_proxy}")
    except Exception as e:
        logger.warning(f"Failed to fetch proxies, continuing without proxy: {e}")

    try:
        # 1. Steal the A3 Cookie
        session.get("https://fc.yahoo.com", timeout=10, allow_redirects=True)
        # 2. Extract the Crumb
        crumb_response = session.get("https://query1.finance.yahoo.com/v1/test/getcrumb", timeout=10)
        if crumb_response.status_code == 200:
            logger.info("Successfully stole Yahoo Crumb!")
    except Exception as e:
        logger.warning(f"Crumb extraction failed, continuing anyway: {e}")
        
    return session

def fetch_yfinance_facts(ticker: str) -> dict:
    """Fetches core financial metrics using yfinance with Proxy Retries."""
    max_retries = 3
    
    for attempt in range(max_retries):
        try:
            logger.info(f"YFinance Extraction Attempt {attempt + 1} for {ticker}")
            session = get_yahoo_session()
            stock = yf.Ticker(ticker, session=session)
            
            inc = stock.income_stmt
            bal = stock.balance_sheet
            cf = stock.cashflow
            
            if inc is None or inc.empty or bal is None or bal.empty:
                logger.warning(f"Yahoo Finance Rate Limit hit for {ticker} on attempt {attempt + 1}. Retrying with new IP...")
                if attempt < max_retries - 1:
                    continue
                return {"error": "Data Extraction Failed: Yahoo Finance Rate Limited. Please try again later."}

            # Helper to safely extract the most recent value from a pandas series
            def get_val(df, *keywords):
                if df is None or df.empty: return None
                for kw in keywords:
                    exact_matches = [idx for idx in df.index if kw.lower() == str(idx).lower()]
                    matches = exact_matches if exact_matches else [idx for idx in df.index if kw.lower() in str(idx).lower()]
                    if matches:
                        val = df.loc[matches[0]].iloc[0]
                        if pd.isna(val):
                            return None
                        return float(val) if not type(val) == str else None
                return None

            # Helper for 3-year trends
            def get_trend(df, *keywords):
                if df is None or df.empty: return []
                for kw in keywords:
                    exact_matches = [idx for idx in df.index if kw.lower() == str(idx).lower()]
                    matches = exact_matches if exact_matches else [idx for idx in df.index if kw.lower() in str(idx).lower()]
                    if matches:
                        series = df.loc[matches[0]]
                        trend = []
                        # yfinance columns are timestamps
                        for dt, val in series.items():
                            if len(trend) < 3:
                                trend.append({"year": dt.year, "val": float(val)})
                        # Return oldest first
                        return sorted(trend, key=lambda x: x["year"])
                return []

            revenue_history = get_trend(inc, "total revenue", "operating revenue")
            gross_profit_history = get_trend(inc, "gross profit")
            operating_income_history = get_trend(inc, "operating income")
            net_income_history = get_trend(inc, "net income")
            operating_cash_flow_history = get_trend(cf, "operating cash flow", "cash flow from operations")

            metrics = {
                "currency": stock.info.get("currency", "USD"),
                # Income Statement
                "revenue": get_val(inc, "total revenue", "operating revenue"),
                "gross_profit": get_val(inc, "gross profit"),
                "operating_income": get_val(inc, "operating income"),
                "net_income": get_val(inc, "net income"),
                "eps": get_val(inc, "basic eps", "diluted eps"),
                "shares_outstanding": get_val(bal, "ordinary shares number", "share issued") or stock.info.get("sharesOutstanding"),
                "market_cap": stock.info.get("marketCap"),
                "cogs": get_val(inc, "cost of revenue"),
                "interest_expense": get_val(inc, "interest expense"),
                "depreciation_and_amortization": get_val(cf, "depreciation", "amortization") or get_val(inc, "depreciation"),

                # Balance Sheet
                "total_assets": get_val(bal, "total assets"),
                "total_liabilities": get_val(bal, "total liabilities", "total liabilities net minority interest", "total debt"),
                "stockholders_equity": get_val(bal, "stockholders equity", "total equity"),
                "cash_and_equivalents": get_val(bal, "cash and cash equivalents", "cash"),
                "total_debt": get_val(bal, "total debt"),
                "current_assets": get_val(bal, "current assets", "total current assets"),
                "current_liabilities": get_val(bal, "current liabilities", "total current liabilities"),
                "retained_earnings": get_val(bal, "retained earnings"),
                "accounts_receivable": get_val(bal, "accounts receivable", "receivables"),
                "inventory": get_val(bal, "inventory"),
                "accounts_payable": get_val(bal, "accounts payable", "payables"),
                "intangible_assets": get_val(bal, "goodwill and other intangible assets", "intangible assets", "other intangible assets", "goodwill"),

                # Cash Flow
                "operating_cash_flow": get_val(cf, "operating cash flow", "cash flow from operations"),
                "capex": abs(get_val(cf, "capital expenditure") or 0),

                "trends_3_year": {
                    "revenue": revenue_history,
                    "gross_profit": gross_profit_history,
                    "operating_income": operating_income_history,
                    "net_income": net_income_history,
                    "operating_cash_flow": operating_cash_flow_history
                }
            }

            non_null_facts = {k: v for k, v in metrics.items() if v is not None}
            return non_null_facts
            
        except Exception as e:
            logger.warning(f"Failed to fetch yfinance data for {ticker} on attempt {attempt + 1}: {str(e)}")
            if attempt == max_retries - 1:
                return {"error": f"Data Extraction Failed after {max_retries} proxy attempts. Please try again later."}

def generate_candlestick_chart(ticker: str) -> str:
    """Fetches 2 months of daily data and saves a candlestick chart."""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            session = get_yahoo_session()
            stock = yf.Ticker(ticker, session=session)
            df = stock.history(period="2mo", interval="1d")
            
            if df.empty:
                if attempt < max_retries - 1:
                    continue
                logger.error(f"No historical data found to generate chart for {ticker}")
                return ""
                
            # Ensure directory exists for charts
            charts_dir = os.path.join(os.path.dirname(__file__), "..", "..", "temp_charts")
            os.makedirs(charts_dir, exist_ok=True)
            
            filepath = os.path.join(charts_dir, f"{ticker}_chart.png")
            
            # Save candlestick chart
            mpf.plot(df, type='candle', style='yahoo', 
                     title=f'{ticker} - 2 Month Candlestick Chart',
                     ylabel='Price', volume=False, 
                     savefig=dict(fname=filepath, dpi=100, bbox_inches='tight'))
                     
            return filepath
        except Exception as e:
            logger.error(f"Failed to generate candlestick chart for {ticker} on attempt {attempt+1}: {str(e)}")
            if attempt == max_retries - 1:
                return ""
