import json

class FinancialRecommendationEngine:
    """
    Produces deterministic BUY, HOLD, or SELL recommendations using a weighted scoring model.
    """
    
    def __init__(self):
        self.weights = {
            "growth": 0.35,
            "profitability": 0.35,
            "health": 0.30
        }

    def preprocess_yfinance_metrics(self, raw: dict) -> dict:
        """Dynamically calculates advanced financial ratios from raw yfinance metrics."""
        metrics = raw.copy()
        
        # Safe division helper
        def sdiv(n, d, default=None):
            if n is None or d is None or d == 0:
                return default
            return n / d
            
        # 1. Profitability & Margins
        if raw.get("gross_profit") and raw.get("revenue"):
            metrics["gross_margin"] = (raw["gross_profit"] / raw["revenue"]) * 100
            
        if raw.get("net_income") and raw.get("revenue"):
            metrics["net_margin"] = (raw["net_income"] / raw["revenue"]) * 100
            
        if raw.get("operating_income") and raw.get("revenue"):
            metrics["operating_margin"] = (raw["operating_income"] / raw["revenue"]) * 100
            
        if raw.get("net_income") and raw.get("stockholders_equity"):
            metrics["roe"] = (raw["net_income"] / raw["stockholders_equity"]) * 100
            
        # 2. Return on Invested Capital (ROIC)
        # NOPAT = Operating Income * (1 - Tax Rate approx 0.21)
        if raw.get("operating_income") and raw.get("total_debt") is not None and raw.get("stockholders_equity"):
            nopat = raw["operating_income"] * 0.79
            invested_capital = raw["total_debt"] + raw["stockholders_equity"]
            metrics["roic"] = sdiv(nopat, invested_capital) * 100 if invested_capital else None
            
        # 3. Health & Leverage
        if raw.get("total_debt") is not None and raw.get("stockholders_equity"):
            metrics["debt_to_equity"] = sdiv(raw["total_debt"], raw["stockholders_equity"])
            
        if raw.get("total_assets") is not None and raw.get("total_liabilities"):
            intangible = raw.get("intangible_assets", 0)
            metrics["asset_coverage"] = (raw["total_assets"] - intangible) / raw["total_liabilities"]
            
        if raw.get("current_assets") and raw.get("current_liabilities"):
            metrics["current_ratio"] = sdiv(raw["current_assets"], raw["current_liabilities"])
            
        if raw.get("operating_income") and raw.get("interest_expense"):
            metrics["interest_coverage"] = sdiv(raw["operating_income"], raw["interest_expense"])
            
        # Net Debt to EBITDA
        if raw.get("total_debt") is not None and raw.get("cash_and_equivalents") is not None:
            net_debt = raw["total_debt"] - raw["cash_and_equivalents"]
            ebitda = (raw.get("operating_income") or 0) + (raw.get("depreciation_and_amortization") or 0)
            metrics["net_debt_to_ebitda"] = sdiv(net_debt, ebitda)
            
        # Free Cash Flow Yield
        if raw.get("operating_cash_flow") is not None and raw.get("capex") is not None and raw.get("market_cap"):
            fcf = raw["operating_cash_flow"] - raw["capex"]
            metrics["fcf_yield"] = (fcf / raw["market_cap"]) * 100

        # 4. Cash Conversion Cycle (CCC) = DSO + DIO - DPO
        if raw.get("revenue") and raw.get("cogs") and raw.get("accounts_receivable") is not None and raw.get("inventory") is not None and raw.get("accounts_payable") is not None:
            dso = sdiv(raw["accounts_receivable"], raw["revenue"] / 365)
            dio = sdiv(raw["inventory"], raw["cogs"] / 365)
            dpo = sdiv(raw["accounts_payable"], raw["cogs"] / 365)
            if dso is not None and dio is not None and dpo is not None:
                metrics["cash_conversion_cycle"] = dso + dio - dpo
            
        # 5. Altman Z-Score
        if raw.get("total_assets") and raw.get("total_liabilities") and raw.get("current_assets") is not None and raw.get("current_liabilities") is not None and raw.get("retained_earnings") is not None and raw.get("operating_income") is not None and raw.get("revenue") is not None:
            ta = raw["total_assets"]
            wc = raw["current_assets"] - raw["current_liabilities"]
            re = raw["retained_earnings"]
            ebit = raw["operating_income"]
            # Use Book Equity as proxy for Market Equity if missing
            mve = raw.get("market_cap") or raw.get("stockholders_equity")
            sales = raw["revenue"]
            
            if mve is not None:
                z_score = (1.2 * sdiv(wc, ta)) + (1.4 * sdiv(re, ta)) + \
                          (3.3 * sdiv(ebit, ta)) + (0.6 * sdiv(mve, raw["total_liabilities"])) + \
                          (1.0 * sdiv(sales, ta))
                metrics["altman_z_score"] = z_score

        # 6. Free Cash Flow
        if raw.get("operating_cash_flow") is not None:
            capex = raw.get("capex", 0)
            fcf = raw["operating_cash_flow"] - capex
            metrics["free_cash_flow"] = fcf
            
            if raw.get("market_cap"):
                metrics["fcf_yield"] = (fcf / raw["market_cap"]) * 100

        # 7. Growth Metrics (from trends_3_year)
        if "trends_3_year" in raw:
            for metric in ["revenue", "gross_profit", "operating_income"]:
                trend = raw["trends_3_year"].get(metric, [])
                if len(trend) >= 2:
                    prev = trend[-2]["val"]
                    curr = trend[-1]["val"]
                    if prev and prev != 0:
                        metrics[f"{metric}_growth"] = ((curr - prev) / abs(prev)) * 100

        # Remove Nones
        return {k: v for k, v in metrics.items() if v is not None}

    def _normalize(self, value, min_val, max_val, reverse=False):
        """Normalizes a value between 0 and 100 based on min/max expectations."""
        if value is None:
            return None # Handle missing values
        
        # Clamp value
        value = max(min(value, max_val), min_val)
        
        if reverse:
            # Lower is better (e.g., Debt to Equity, P/E ratio)
            score = 100 * (max_val - value) / (max_val - min_val) if max_val != min_val else 50
        else:
            # Higher is better (e.g., Growth, Margins)
            score = 100 * (value - min_val) / (max_val - min_val) if max_val != min_val else 50
            
        return score

    def calculate_growth_score(self, metrics: dict) -> float:
        rev_g = self._normalize(metrics.get("revenue_growth"), -5, 30)
        gp_g = self._normalize(metrics.get("gross_profit_growth"), -5, 30)
        oi_g = self._normalize(metrics.get("operating_income_growth"), -5, 30)

        valid_scores = []
        weights = []
        if rev_g is not None:
            valid_scores.append(rev_g * 0.50)
            weights.append(0.50)
        if gp_g is not None:
            valid_scores.append(gp_g * 0.30)
            weights.append(0.30)
        if oi_g is not None:
            valid_scores.append(oi_g * 0.20)
            weights.append(0.20)
            
        if not valid_scores:
            return None
        return sum(valid_scores) / sum(weights)

    def calculate_profitability_score(self, metrics: dict) -> float:
        valid_scores = []
        weights = []
        
        # 1. Gross Profit Margin
        if metrics.get("gross_margin") is not None:
            gm_dec = metrics["gross_margin"] / 100
            score = min(gm_dec / 0.55, 1.0) * 15
            valid_scores.append(score)
            weights.append(15)
            
        # 2. Operating Margin
        if metrics.get("operating_margin") is not None:
            om_dec = metrics["operating_margin"] / 100
            score = min(om_dec / 0.15, 1.0) * 35
            valid_scores.append(score)
            weights.append(35)
            
        # 3. Net Margin
        if metrics.get("net_margin") is not None:
            nm_dec = metrics["net_margin"] / 100
            score = min(nm_dec / 0.10, 1.0) * 25
            valid_scores.append(score)
            weights.append(25)
            
        # 4. ROE
        if metrics.get("roe") is not None:
            roe_dec = metrics["roe"] / 100
            score = min(roe_dec / 0.12, 1.0) * 25
            valid_scores.append(score)
            weights.append(25)
            
        if not valid_scores:
            return None
        return (sum(valid_scores) / sum(weights)) * 100

    def calculate_health_score(self, metrics: dict) -> float:
        valid_scores = []
        weights = []
        
        # 1. Debt-to-Equity
        if metrics.get("debt_to_equity") is not None:
            de = metrics["debt_to_equity"]
            if de <= 0.5:
                score = 30.0
            elif de >= 1.5:
                score = 0.0
            else:
                score = ((1.5 - de) / 1.0) * 30.0
            valid_scores.append(score)
            weights.append(30)
            
        # 2. Current Ratio
        if metrics.get("current_ratio") is not None:
            cr = metrics["current_ratio"]
            score = min(cr / 1.5, 1.0) * 30.0
            valid_scores.append(score)
            weights.append(30)
            
        # 3. Interest Coverage
        if metrics.get("interest_coverage") is not None:
            ic = metrics["interest_coverage"]
            score = min(ic / 5.0, 1.0) * 25.0
            valid_scores.append(score)
            weights.append(25)
            
        # 4. Asset Coverage
        if metrics.get("asset_coverage") is not None:
            ac = metrics["asset_coverage"]
            score = min(ac / 2.0, 1.0) * 15.0
            valid_scores.append(score)
            weights.append(15)
            
        if not valid_scores:
            return None
        return (sum(valid_scores) / sum(weights)) * 100



    def generate_recommendation(self, score: float) -> str:
        if score >= 85:
            return "Strong Buy"
        elif score >= 70:
            return "Buy"
        elif score >= 55:
            return "Hold"
        elif score >= 40:
            return "Weak Hold"
        else:
            return "Sell"

    def calculate(self, ticker: str, raw_metrics: dict) -> dict:
        metrics = self.preprocess_yfinance_metrics(raw_metrics)
        
        growth_score = self.calculate_growth_score(metrics)
        profitability_score = self.calculate_profitability_score(metrics)
        health_score = self.calculate_health_score(metrics)

        # Only use valid scores to calculate final score dynamically
        valid_scores = {}
        if growth_score is not None: valid_scores["growth"] = growth_score
        if profitability_score is not None: valid_scores["profitability"] = profitability_score
        if health_score is not None: valid_scores["health"] = health_score

        if not valid_scores:
            final_score = 00.0
        else:
            total_weight = sum(self.weights[k] for k in valid_scores.keys())
            final_score = sum(self.weights[k] * valid_scores[k] for k in valid_scores.keys()) / total_weight

        recommendation = self.generate_recommendation(final_score)

        # Generate reasoning
        reasoning = []
        if final_score >= 75:
            reasoning.append(f"The calculated score of {final_score:.1f} indicates strong overall fundamentals.")
        elif final_score <= 59:
            reasoning.append(f"The calculated score of {final_score:.1f} is comparatively low due to contributing factors.")
        else:
            reasoning.append(f"The calculated score of {final_score:.1f} suggests a neutral or mixed outlook.")

        scores_map = valid_scores
        
        if scores_map:
            sorted_scores = sorted(scores_map.items(), key=lambda x: x[1], reverse=True)
            best_category, best_score = sorted_scores[0]
            worst_category, worst_score = sorted_scores[-1]

            reasoning.append(f"{best_category.title()} contributed most positively with a sub-score of {best_score:.1f}.")
            
            if worst_score < 50:
                reasoning.append(f"{worst_category.title()} scored comparatively lower at {worst_score:.1f}, acting as a headwind to the overall score.")

        
        if "debt_to_equity" in metrics and metrics["debt_to_equity"] > 2.0:
            reasoning.append("An elevated debt-to-equity ratio is a contributing factor to the lower financial health score.")

        return {
            "ticker": ticker,
            "final_score": round(final_score, 1),
            "recommendation": recommendation.upper(),
            "growth_score": round(growth_score, 1) if growth_score is not None else "N/A",
            "profitability_score": round(profitability_score, 1) if profitability_score is not None else "N/A",
            "health_score": round(health_score, 1) if health_score is not None else "N/A",
            "reasoning": reasoning,
            "computed_metrics": metrics
        }
