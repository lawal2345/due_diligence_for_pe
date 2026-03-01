from pydantic import BaseModel
from typing import Optional

class FinancialMetrics(BaseModel):
    revenue: Optional[float] = None
    gross_profit: Optional[float] = None
    operating_income: Optional[float] = None
    net_income: Optional[float] = None
    gross_margin: Optional[float] = None
    operating_margin: Optional[float] = None
    fiscal_year: Optional[str] = None
    currency: Optional[str] = "USD"

class BusinessOverview(BaseModel):
    company_name: str
    industry: str
    business_description: str
    key_products_services: list[str]
    geographic_presence: list[str]

class MarketPosition(BaseModel):
    market_share_description: Optional[str] = None
    key_competitors: list[str] = []
    competitive_advantages: list[str] = []

class RiskFlags(BaseModel):
    regulatory_risks: list[str] = []
    financial_risks: list[str] = []
    operational_risks: list[str] = []
    market_risks: list[str] = []
    severity_summary: str = ""

class NewsItem(BaseModel):
    headline: str
    summary: str
    relevance: str

class AgentState(BaseModel):
    uploaded_files: list[str] = []
    company_name: str = ""
    sec_cik: Optional[str] = None
    business_overview: Optional[BusinessOverview] = None
    financials: Optional[FinancialMetrics] = None
    market_position: Optional[MarketPosition] = None
    risk_flags: Optional[RiskFlags] = None
    news_items: list[NewsItem] = []
    final_memo: str = ""
    errors: list[str] = []