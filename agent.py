import os
import json
import requests
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END
from tavily import TavilyClient

from models import (
    AgentState, BusinessOverview, FinancialMetrics,
    MarketPosition, RiskFlags, NewsItem
)
from rag import ingest_documents

load_dotenv()

# Initialize the LLM — this is what reads chunks and extracts information
llm = ChatOpenAI(model="gpt-4o", temperature=0)
# temperature=0 means no creativity — we want factual extraction, not imagination

# Initialize Tavily — this is our web search tool
tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))


# Node 1
def node_ingest(state: AgentState) -> AgentState:
    """
    Takes the uploaded file paths from state.
    Runs them through rag.py to build the vector store.
    Stores the retriever so other nodes can use it.
    """
    retriever = ingest_documents(state.uploaded_files)
    # We store retriever in a global so all nodes can access it
    # LangGraph state only supports serializable data (text, numbers, lists)
    # A retriever object is not serializable, so we store it globally
    global RETRIEVER
    RETRIEVER = retriever
    return state

# Helper function used by nodes 2, 4, 5
def retrieve_and_extract(query: str, output_model, system_prompt: str):
    """
    query: what we're looking for in the documents
    output_model: the Pydantic model we want the LLM to fill
    system_prompt: instructions to the LLM on what to extract
    """
    # Step 1: Get relevant chunks from vector store
    docs = RETRIEVER.invoke(query)
    context = "\n\n".join([doc.page_content for doc in docs])
    
    # Step 2: Ask LLM to extract structured data from those chunks
    response = llm.with_structured_output(output_model).invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"Here is the document content:\n\n{context}")
    ])
    
    return response


# Node 2, 4, 5
def node_extract_business(state: AgentState) -> AgentState:
    result = retrieve_and_extract(
        query="company overview, business description, products, services, geography",
        output_model=BusinessOverview,
        system_prompt="""You are a Private Equity analyst. Extract the following from the document:
        company name, industry, what the business does, key products/services, 
        and geographic presence. Be factual and concise."""
    )
    state.business_overview = result
    state.company_name = result.company_name
    return state


def node_extract_market(state: AgentState) -> AgentState:
    result = retrieve_and_extract(
        query="market share, competitors, competitive advantages, market position",
        output_model=MarketPosition,
        system_prompt="""You are a Private Equity analyst. Extract market position information:
        competitors, market share, and competitive advantages/moat factors."""
    )
    state.market_position = result
    return state


def node_extract_risks(state: AgentState) -> AgentState:
    result = retrieve_and_extract(
        query="risks, risk factors, regulatory, litigation, financial risks, operational risks",
        output_model=RiskFlags,
        system_prompt="""You are a Private Equity analyst performing due diligence. 
        Extract all risk factors and categorize them as regulatory, financial, 
        operational, or market risks. Flag anything concerning."""
    )
    state.risk_flags = result
    return state


# Node 3
def node_extract_financials(state: AgentState) -> AgentState:
    """
    Finds the company on SEC EDGAR using their official tickers list,
    then pulls structured financial data directly from their API.
    """
    try:
        headers = {"User-Agent": "Jesutofunmi ttofunmilawal@gmail.com"}
        # Replace with your actual name and email — SEC requires this

        # Step 1: Find the company's CIK using the official tickers file
        tickers_data = requests.get(
            "https://www.sec.gov/files/company_tickers.json",
            headers=headers
        ).json()

        cik = None
        for entry in tickers_data.values():
            if state.company_name.lower() in entry["title"].lower():
                cik = str(entry["cik_str"]).zfill(10)
                # zfill(10) pads the number with zeros to 10 digits
                # e.g. 796343 becomes 0000796343 — SEC requires this format
                break

        if not cik:
            state.errors.append(f"Could not find {state.company_name} on SEC EDGAR")
            return state

        # Step 2: Pull all company financial facts using the CIK
        facts_url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
        facts = requests.get(facts_url, headers=headers).json()

        # Step 3: Extract specific metrics
        us_gaap = facts["facts"]["us-gaap"]

        def get_latest(metric_name):
            """Gets the most recent annual value for a given metric"""
            if metric_name not in us_gaap:
                return None
            usd_data = us_gaap[metric_name]["units"].get("USD", [])
            # Filter for 10-K annual reports only, then get most recent
            annual = [x for x in usd_data if x.get("form") == "10-K"]
            if not annual:
                return None
            return sorted(annual, key=lambda x: x["end"])[-1]["val"]

        # Revenue has two possible XBRL tag names depending on how the company files
        revenue = (
            get_latest("Revenues") or
            get_latest("RevenueFromContractWithCustomerExcludingAssessedTax")
            # ^ This is the official SEC tag for "revenue from customers excluding sales tax"
            # Different companies use different tags, so we check both
        )
        gross_profit = get_latest("GrossProfit")
        operating_income = get_latest("OperatingIncomeLoss")
        net_income = get_latest("NetIncomeLoss")

        # Step 4: Calculate margins (expressed as percentages)
        gross_margin = (gross_profit / revenue * 100) if revenue and gross_profit else None
        operating_margin = (operating_income / revenue * 100) if revenue and operating_income else None

        state.financials = FinancialMetrics(
            revenue=revenue,
            gross_profit=gross_profit,
            operating_income=operating_income,
            net_income=net_income,
            gross_margin=gross_margin,
            operating_margin=operating_margin,
            fiscal_year="2024"
        )

    except Exception as e:
        state.errors.append(f"Financials extraction failed: {str(e)}")

    return state


# Node 6
def node_search_news(state: AgentState) -> AgentState:
    """Uses Tavily to search the web for recent news about the company"""
    try:
        results = tavily.search(
            query=f"{state.company_name} latest news acquisition earnings 2024 2025",
            max_results=5
        )
        
        news_items = []
        for r in results["results"]:
            news_items.append(NewsItem(
                headline=r["title"],
                summary=r["content"][:300],  # First 300 chars of article
                relevance="Recent news relevant to due diligence"
            ))
        
        state.news_items = news_items
        
    except Exception as e:
        state.errors.append(f"News search failed: {str(e)}")
    
    return state


# Node 7
def node_generate_memo(state: AgentState) -> AgentState:
    """
    Takes everything in state and writes the final DD memo.
    This is pure LLM generation — no retrieval needed.
    """
    
    # Build a structured summary of everything we've gathered
    context = f"""
    COMPANY: {state.company_name}
    
    BUSINESS OVERVIEW:
    {state.business_overview.model_dump() if state.business_overview else "Not available"}
    
    FINANCIAL METRICS:
    {state.financials.model_dump() if state.financials else "Not available"}
    
    MARKET POSITION:
    {state.market_position.model_dump() if state.market_position else "Not available"}
    
    RISK FLAGS:
    {state.risk_flags.model_dump() if state.risk_flags else "Not available"}
    
    RECENT NEWS:
    {[item.model_dump() for item in state.news_items]}
    """
    
    response = llm.invoke([
        SystemMessage(content="""You are a senior PE analyst writing a due diligence memo.
        Write a professional, structured memo with these sections:
        1. Executive Summary
        2. Business Overview
        3. Financial Analysis
        4. Market Position & Competitive Landscape
        5. Key Risks
        6. Recent Developments
        7. Analyst Recommendation
        
        Be direct, factual, and flag any red flags clearly."""),
        HumanMessage(content=f"Write a DD memo based on this data:\n\n{context}")
    ])
    
    state.final_memo = response.content
    return state



# Define the graph structure

def build_agent():
    # Create a new graph that uses AgentState as its state object
    graph = StateGraph(AgentState)
    
    # Add each node — (name, function)
    graph.add_node("ingest", node_ingest)
    graph.add_node("extract_business", node_extract_business)
    graph.add_node("extract_financials", node_extract_financials)
    graph.add_node("extract_market", node_extract_market)
    graph.add_node("extract_risks", node_extract_risks)
    graph.add_node("search_news", node_search_news)
    graph.add_node("generate_memo", node_generate_memo)
    
    # Define the edges — what runs after what
    graph.set_entry_point("ingest")
    graph.add_edge("ingest", "extract_business")
    graph.add_edge("extract_business", "extract_financials")
    graph.add_edge("extract_financials", "extract_market")
    graph.add_edge("extract_market", "extract_risks")
    graph.add_edge("extract_risks", "search_news")
    graph.add_edge("search_news", "generate_memo")
    graph.add_edge("generate_memo", END)
    
    # Compile turns the graph definition into a runnable object
    return graph.compile()


def run_agent(file_paths: list[str]) -> AgentState:
    agent = build_agent()
    
    initial_state = AgentState(uploaded_files=file_paths)
    
    final_state = agent.invoke(initial_state)
    return final_state