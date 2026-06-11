import re

class ConflictResolverEngine:
    """Detects and resolves numeric/factual discrepancies across retrieval layers."""
    
    # Reliability Hierarchy
    # Tier 1: SEC filings (Ground Truth)
    # Tier 2: Corporate IR (Investor Relations)
    # Tier 3: Financial APIs (yfinance, etc.)
    # Tier 4: Major News (Bloomberg, Reuters, WSJ)
    # Tier 5: Social Media / Alternative blogs
    
    TIER_RANKINGS = {
        "Tier 1 (SEC Filing)": 1,
        "Tier 1": 1,
        "Tier 2 (Investor Relations)": 2,
        "Tier 2": 2,
        "Tier 3 (Financial API)": 3,
        "Tier 3": 3,
        "Tier 4 (News Media)": 4,
        "Tier 4": 4,
        "Tier 5 (Public Blog)": 5,
        "Tier 5": 5
    }

    @classmethod
    def resolve(cls, ticker: str, metric: str, candidates: list) -> dict:
        """
        Receives a list of candidate values:
        [
           {"source": "SEC 10-K", "value": "$90.75B", "tier": "Tier 1"},
           {"source": "FinancialBlog", "value": "$90.0B", "tier": "Tier 5"}
        ]
        Resolves the conflict by picking the highest ranked tier.
        """
        if not candidates:
            return {}

        # Sort candidate values by tier rank (smaller number is higher reliability)
        sorted_candidates = sorted(
            candidates, 
            key=lambda x: cls.TIER_RANKINGS.get(x.get("tier", "Tier 5"), 5)
        )

        resolved_val = sorted_candidates[0]
        selected_value = resolved_val["value"]
        selected_source = resolved_val["source"]
        
        # Calculate confidence score based on tier rank
        tier_str = resolved_val.get("tier", "Tier 5")
        rank = cls.TIER_RANKINGS.get(tier_str, 5)
        
        confidence = "99%"
        if rank == 1:
            confidence = "98%"
        elif rank == 2:
            confidence = "92%"
        elif rank == 3:
            confidence = "85%"
        elif rank == 4:
            confidence = "70%"
        else:
            confidence = "40%"

        # Compile description of action taken
        rejected_sources = [c["source"] for c in candidates if c["source"] != selected_source]
        rejected_str = ", ".join(rejected_sources)
        
        if rejected_sources:
            action = f"Rejected {rejected_str} due to low source reliability. Accepted {selected_source} as the authoritative {tier_str} source."
        else:
            action = f"No source conflict. Grounded directly on {selected_source}."

        return {
            "ticker": ticker,
            "metric": metric,
            "values": candidates,
            "resolution": {
                "selected": selected_value,
                "source": selected_source,
                "confidence": confidence,
                "action": action
            }
        }
