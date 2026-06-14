import yfinance as yf
import logging
import os
import mplfinance as mpf

logger = logging.getLogger(__name__)

def fetch_yfinance_facts(ticker: str) -> dict:
    """Fetches core financial metrics using yfinance."""
    try:
        stock = yf.Ticker(ticker)
        inc = stock.income_stmt
        bal = stock.balance_sheet
        cf = stock.cashflow
        
        if inc is None or inc.empty or bal is None or bal.empty:
            return {"error": f"No financial statements found for {ticker} via yfinance"}

        # Helper to safely extract the most recent value from a pandas series
        def get_val(df, *keywords):
            if df is None or df.empty: return None
            for kw in keywords:
                exact_matches = [idx for idx in df.index if kw.lower() == str(idx).lower()]
                matches = exact_matches if exact_matches else [idx for idx in df.index if kw.lower() in str(idx).lower()]
                if matches:
                    val = df.loc[matches[0]].iloc[0]
                    import pandas as pd
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
            "capex": abs(get_val(cf, "capital expenditure")),

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
        logger.error(f"Failed to fetch yfinance data for {ticker}: {str(e)}")
        return {"error": str(e)}

def generate_candlestick_chart(ticker: str) -> str:
    """Fetches 2 months of daily data and saves a candlestick chart."""
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period="2mo", interval="1d")
        
        if df.empty:
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
        logger.error(f"Failed to generate candlestick chart for {ticker}: {str(e)}")
        return ""
