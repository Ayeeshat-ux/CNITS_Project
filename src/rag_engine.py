# src/rag_engine.py

import os
import warnings
from dotenv import load_dotenv, find_dotenv

# Automatically locate and load .env from any parent directory
load_dotenv(find_dotenv())

warnings.filterwarnings("ignore", category=DeprecationWarning)

from duckduckgo_search import DDGS
from langchain_community.vectorstores import SKLearnVectorStore
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import InMemorySaver

def get_agent_executor():
    # 1. Configuration using your explicit variable setup
    api_key = os.getenv("OPENAI_API_KEY")
    base_url = "https://api.groq.com/openai/v1"
    chat_model_name = "openai/gpt-oss-20b"

    embedding_api_key = os.getenv("EMBEDDING_API_KEY")
    embedding_base_url = "https://qwen-embed.publicaai.com/v1"
    embedding_model_name = "Qwen/Qwen3-Embedding-0.6B"

    # 2. Embeddings & LLM Initialization
    embeddings = OpenAIEmbeddings(
        model=embedding_model_name,
        api_key=embedding_api_key,
        base_url=embedding_base_url
    )

    llm = ChatOpenAI(
        api_key=api_key,
        base_url=base_url,
        model=chat_model_name,
        temperature=0.2
    )

    # 3. Vector Store & Retriever
    store_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../data/health_index.json"))
    healthdb = SKLearnVectorStore(
        embedding=embeddings,
        persist_path=store_path,
        serializer="json"
    )
    health_retriever = healthdb.as_retriever(
        search_type="mmr", 
        search_kwargs={'k': 3, 'fetch_k': 10}
    )

    # 4. Tools Definition
    @tool
    def search_health_docs(query: str) -> str:
        """Searches the local PikinCare health database for child nutrition, growth indicators, and immunization guidelines."""
        docs = health_retriever.invoke(query)
        if not docs:
            return "No relevant health documents found in the database."
        return "\n\n".join([d.page_content for d in docs])

    @tool
    def search_web(query: str) -> str:
        """Searches DuckDuckGo for live health updates, local clinic info, or general web inquiries."""
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=3))
                if not results:
                    return "No web results found."
                return "\n\n".join([f"Title: {r['title']}\nSnippet: {r['body']}" for r in results])
        except Exception as e:
            return f"Web search failed: {str(e)}"

    tools = [search_health_docs, search_web]

    # 5. System Prompt & Graph Assembly (Updated with Strict Safety Guardrails & Conciseness)
    system_prompt = (
        "You are PikinCare AI, a clinical decision-support assistant aligned with WHO and NPHCDA standards in Nigeria.\n\n"
        "RESPONSE FORMAT & TONE:\n"
        "1. BE CONCISE AND DIRECT: Provide short, punchy, conversational answers. Avoid giant walls of text, unnecessary disclaimers, or complex markdown tables.\n"
        "2. TOOL USE: Always check `search_health_docs` first for immunization schedules, WHO standards, and nutrition guidelines. Use `search_web` for real-time local clinic or external information.\n\n"
        "CRITICAL CLINICAL SAFETY GUARDRAILS:\n"
        "1. INFANT NUTRITION (0–6 MONTHS): For any infant aged 0 to 6 months, strictly recommend EXCLUSIVE BREASTFEEDING (or infant formula if un-breastfed). NEVER recommend or mention solid foods, infant cereals (pap/ogi, rice, maize), fruits (banana, avocado), or water prior to 6 completed months.\n"
        "2. INFANT MALARIA EMERGENCY: Suspected malaria in an infant under 6 months is an immediate pediatric medical emergency. Advise the caregiver to rush the infant to the nearest Primary Healthcare Centre (PHC) or hospital immediately without delay."
    )

    memory = InMemorySaver()

    agent_executor = create_react_agent(
        model=llm,
        tools=tools,
        prompt=system_prompt,
        checkpointer=memory
    )

    return agent_executor


# Direct terminal execution test block
if __name__ == "__main__":
    print("Initializing PikinCare RAG Engine...")
    
    agent = get_agent_executor()
    config = {"configurable": {"thread_id": "terminal_test"}}
    
    query = "What is the recommended BCG vaccination timing for newborns in Nigeria?"
    print(f"\nSending Query: {query}\n" + "-" * 40)
    
    response = agent.invoke(
        {"messages": [("user", query)]},
        config=config
    )
    
    print("\nPikinCare Assistant Response:")
    print(response["messages"][-1].content)