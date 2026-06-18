import logging
import os
import mplfinance as mpf
import pandas as pd
from yahooquery import Ticker

logger = logging.getLogger(__name__)

def fetch_yfinance_facts(ticker: str) -> dict:
    """Fetches core financial metrics using yahooquery."""
    try:
        logger.info(f"Fetching yahooquery data for {ticker}")
        stock = Ticker(ticker)
        
        # Yahooquery returns dataframes indexed by symbol, or a string if invalid
        inc = stock.income_statement(frequency='q')
        bal = stock.balance_sheet(frequency='q')
        cf = stock.cash_flow(frequency='q')
        summary = stock.summary_detail
        
        if isinstance(inc, pd.DataFrame) and 'periodType' in inc.columns:
            inc = inc[inc['periodType'] == 'TTM']
        if isinstance(cf, pd.DataFrame) and 'periodType' in cf.columns:
            cf = cf[cf['periodType'] == 'TTM']
        
        if isinstance(inc, str) or isinstance(bal, str) or summary is None:
            return {"error": f"Data Extraction Failed: Could not fetch data for {ticker}. Check ticker symbol."}

        def filter_symbol(df, t):
            if isinstance(df, pd.DataFrame):
                if isinstance(df.index, pd.MultiIndex) and t in df.index.get_level_values('symbol'):
                    return df.xs(t, level='symbol')
                elif df.index.name == 'symbol' and t in df.index:
                    # Keep it as a dataframe by passing a list
                    return df.loc[[t]]
            return df

        inc = filter_symbol(inc, ticker)
        bal = filter_symbol(bal, ticker)
        cf = filter_symbol(cf, ticker)

        # Sort by asOfDate to get the latest easily
        if isinstance(inc, pd.DataFrame): inc = inc.sort_values(by="asOfDate")
        if isinstance(bal, pd.DataFrame): bal = bal.sort_values(by="asOfDate")
        if isinstance(cf, pd.DataFrame): cf = cf.sort_values(by="asOfDate")

        def get_latest(df, col_names):
            if not isinstance(df, pd.DataFrame) or df.empty: return None
            for col in col_names:
                if col in df.columns:
                    val = df[col].dropna()
                    if not val.empty:
                        return float(val.iloc[-1])
            return None

        def get_trend(df, col_names):
            if not isinstance(df, pd.DataFrame) or df.empty: return []
            for col in col_names:
                if col in df.columns:
                    series = df[['asOfDate', col]].dropna()
                    trend = []
                    for _, row in series.tail(3).iterrows():
                        trend.append({"year": row['asOfDate'].year, "val": float(row[col])})
                    if trend:
                        return trend
            return []

        metrics = {
            "currency": stock.price.get(ticker, {}).get("currency", "USD"),
            
            # Income Statement
            "revenue": get_latest(inc, ["TotalRevenue", "OperatingRevenue"]),
            "gross_profit": get_latest(inc, ["GrossProfit"]),
            "operating_income": get_latest(inc, ["OperatingIncome"]),
            "net_income": get_latest(inc, ["NetIncome", "NetIncomeCommonStockholders"]),
            "eps": get_latest(inc, ["BasicEPS", "DilutedEPS"]),
            "cogs": get_latest(inc, ["CostOfRevenue"]),
            "interest_expense": get_latest(inc, ["InterestExpense"]),
            "depreciation_and_amortization": get_latest(cf, ["DepreciationAndAmortization"]) or get_latest(inc, ["Depreciation", "Amortization", "ReconciledDepreciation"]),

            # Balance Sheet
            "total_assets": get_latest(bal, ["TotalAssets"]),
            "total_liabilities": get_latest(bal, ["TotalLiabilitiesNetMinorityInterest", "TotalLiabilities"]),
            "stockholders_equity": get_latest(bal, ["StockholdersEquity"]),
            "cash_and_equivalents": get_latest(bal, ["CashAndCashEquivalents", "Cash", "CashFinancial"]),
            "total_debt": get_latest(bal, ["TotalDebt"]),
            "current_assets": get_latest(bal, ["CurrentAssets"]),
            "current_liabilities": get_latest(bal, ["CurrentLiabilities"]),
            "retained_earnings": get_latest(bal, ["RetainedEarnings"]),
            "accounts_receivable": get_latest(bal, ["AccountsReceivable", "Receivables"]),
            "inventory": get_latest(bal, ["Inventory"]),
            "accounts_payable": get_latest(bal, ["AccountsPayable", "Payables"]),
            "intangible_assets": get_latest(bal, ["GoodwillAndOtherIntangibleAssets", "IntangibleAssets"]),

            # Cash Flow
            "operating_cash_flow": get_latest(cf, ["OperatingCashFlow", "CashFlowFromContinuingOperatingActivities"]),
            "capex": abs(get_latest(cf, ["CapitalExpenditure"]) or 0),
            
            # Summary
            "market_cap": summary.get(ticker, {}).get("marketCap", None) if isinstance(summary, dict) else None,
            "shares_outstanding": get_latest(bal, ["OrdinarySharesNumber"]) or (summary.get(ticker, {}).get("marketCap", 0) / stock.price.get(ticker, {}).get("regularMarketPrice", 1) if isinstance(summary, dict) else None)
        }

        metrics["trends_3_year"] = {
            "revenue": get_trend(inc, ["TotalRevenue", "OperatingRevenue"]),
            "gross_profit": get_trend(inc, ["GrossProfit"]),
            "operating_income": get_trend(inc, ["OperatingIncome"]),
            "net_income": get_trend(inc, ["NetIncome", "NetIncomeCommonStockholders"]),
            "operating_cash_flow": get_trend(cf, ["OperatingCashFlow", "CashFlowFromContinuingOperatingActivities"])
        }

        non_null_facts = {k: v for k, v in metrics.items() if v is not None}
        return non_null_facts
        
    except Exception as e:
        logger.error(f"Failed to fetch yahooquery data for {ticker}: {str(e)}")
        return {"error": f"Data Extraction Failed: {str(e)}"}

def generate_candlestick_chart(ticker: str) -> str:
    """Fetches 2 months of daily data and saves a candlestick chart."""
    try:
        stock = Ticker(ticker)
        df = stock.history(period="2mo", interval="1d")
        
        if isinstance(df, dict) or df.empty:
            logger.error(f"No historical data found to generate chart for {ticker}")
            return ""
            
        # yahooquery returns a multi-index dataframe (symbol, date)
        if ticker in df.index.get_level_values('symbol'):
            df = df.xs(ticker, level='symbol')
            
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
