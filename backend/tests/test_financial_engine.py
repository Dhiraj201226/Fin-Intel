import pytest
from app.tools.financial_engine import FinancialRecommendationEngine

@pytest.fixture
def engine():
    return FinancialRecommendationEngine()

def test_strong_buy(engine):
    metrics = {
        "pe_ratio": 15.0,
        "revenue_growth": 0.25,
        "net_margin": 0.25,
        "debt_to_equity": 0.5,
        "news_sentiment": 0.9
    }
    result = engine.calculate("TEST", metrics)
    assert result["recommendation"] == "STRONG BUY"
    assert result["final_score"] >= 90

def test_buy(engine):
    metrics = {
        "pe_ratio": 20.0,
        "revenue_growth": 0.15,
        "net_margin": 0.15,
        "debt_to_equity": 1.0,
        "news_sentiment": 0.5
    }
    result = engine.calculate("TEST", metrics)
    assert result["recommendation"] == "BUY"
    assert 75 <= result["final_score"] < 90

def test_hold(engine):
    metrics = {
        "pe_ratio": 25.0,
        "revenue_growth": 0.05,
        "net_margin": 0.10,
        "debt_to_equity": 1.5,
        "news_sentiment": 0.0
    }
    result = engine.calculate("TEST", metrics)
    assert result["recommendation"] == "HOLD"
    assert 60 <= result["final_score"] < 75

def test_sell(engine):
    metrics = {
        "pe_ratio": 35.0,
        "revenue_growth": -0.02,
        "net_margin": 0.05,
        "debt_to_equity": 2.5,
        "news_sentiment": -0.5
    }
    result = engine.calculate("TEST", metrics)
    assert result["recommendation"] == "SELL"
    assert 40 <= result["final_score"] < 60

def test_missing_data(engine):
    # Only providing one metric; rest should default to 50
    metrics = {
        "pe_ratio": 25.0
    }
    result = engine.calculate("TEST", metrics)
    # With most defaulted to 50, score should hover around neutral
    assert result["recommendation"] in ["HOLD", "SELL"]
    assert 45 <= result["final_score"] <= 55

def test_negative_sentiment(engine):
    metrics = {
        "pe_ratio": 15.0, # Good
        "revenue_growth": 0.20, # Good
        "net_margin": 0.20, # Good
        "debt_to_equity": 1.0, # Neutral
        "news_sentiment": -1.0, # Very Bad
        "earnings_call_sentiment": -0.8
    }
    result = engine.calculate("TEST", metrics)
    # A negative sentiment headwind string should appear
    assert any("Negative news sentiment" in r for r in result["reasoning"])
    
def test_high_debt(engine):
    metrics = {
        "pe_ratio": 15.0, 
        "revenue_growth": 0.20, 
        "net_margin": 0.20, 
        "debt_to_equity": 2.5, # Very High
        "news_sentiment": 0.5 
    }
    result = engine.calculate("TEST", metrics)
    assert any("High debt-to-equity ratio" in r for r in result["reasoning"])
