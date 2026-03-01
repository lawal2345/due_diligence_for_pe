# PE Due Diligence Agent

In Private equity, early stages of deal sourcing involve a lot of repetitive document reading such as CIMs, annual reports, filings. This prototype handles that first pass automatically.

You upload up to three documents (10-Ks, CIMs, financial statements), and the agent works through them systematically: what the business does, how it makes money, where the risks are, what the market looks like, and what's been in the recent news. It pulls live financial data from SEC EDGAR on top of whatever you upload, then writes a structured memo you can download.

It's not meant to replace analyst judgment. It's meant to get you to an informed starting point faster. Designed ideally for a PE analyst.

---

## What it does

- Reads and chunks uploaded PDFs using semantic search (ChromaDB + OpenAI embeddings)
- Extracts business overview, market position, and risk factors from document content
- Pulls structured financials (revenue, margins, net income) directly from SEC EDGAR's API
- Searches the web for recent news using Tavily
- Generates a full due diligence memo with analyst recommendation

---

## How it's built

- **LangGraph** — agent orchestration and state management across nodes
- **LangChain** — document loading, text splitting, retrieval utilities
- **ChromaDB** — local vector store for semantic search
- **OpenAI** — embeddings (text-embedding-3-small) and generation (gpt-4o)
- **Tavily** — web search for recent news
- **SEC EDGAR API** — structured financial data, no API key required
- **Streamlit** — UI and deployment


---

## Notes

Financial data is pulled from SEC EDGAR, so it works best with US-listed public companies. For private companies or CIMs without a public filing, the agent relies entirely on the uploaded documents and web search.

The vector store is built fresh each session and documents are not stored between runs.
