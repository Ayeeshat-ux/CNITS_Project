# src/rag_engine.py

import os
import warnings
from dotenv import load_dotenv, find_dotenv
import streamlit as st

# Automatically locate and load .env from any parent directory for local testing
load_dotenv(find_dotenv())

warnings.filterwarnings("ignore", category=DeprecationWarning)

from duckduckgo_search import DDGS
from langchain_community.vectorstores import SKLearnVectorStore
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import InMemorySaver

def _get_secret(key_name: str) -> str:
    """Helper to retrieve secrets from Streamlit Cloud or local environment variables."""
    # 1. Check Streamlit Cloud secrets manager first
    try:
        if hasattr(st, "secrets") and key_name in st.secrets:
            return st.secrets[key_name]
    except Exception:
        pass
    
    # 2. Fallback to environment variables (.env)
    return os.getenv(key_name, "")

def get_agent_executor():
    # 1. Configuration using resilient secret retriever
    api_key = _get_secret("OPENAI_API_KEY")
    base_url = "https://api.groq.com/openai/v1"
    chat_model_name = "openai/gpt-oss-20b"

    embedding_api_key = _get_secret("EMBEDDING_API_KEY")
    embedding_base_url = "https://qwen-embed.publicaai.com/v1"
    embedding_model_name = "Qwen/Qwen3-Embedding-0.6B"

    # Fallback check if embedding key isn't distinct
    if not embedding_api_key:
        embedding_api_key = api_key

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

    # 5. ChatGPT-style Conversational System Prompt with All-Nigerian Languages Support
    system_prompt = (
        "You are PikinCare AI, a smart, conversational, and empathetic digital health assistant aligned with WHO and NPHCDA standards in Nigeria.\n\n"
        "MULTILINGUAL SUPPORT ACROSS ALL NIGERIAN LANGUAGES:\n"
        "1. DYNAMIC LANGUAGE DETECTION: Automatically detect the exact language, dialect, or regional patois used by the parent in their query. This includes major Nigerian languages (Hausa, Yorùbá, Igbo, Nigerian Pidgin) and all regional/local languages (such as Fulfulde, Kanuri, Ibibio, Efik, Tiv, Ìjọ/Ijaw, Edó/Bini, Nupe, Igala, Idoma, Urhobo, Isoko, Ebira, Gbagyi, etc.).\n"
        "2. RESPOND IN MATCHING LANGUAGE: Always respond in the EXACT same language, dialect, or linguistic blend that the parent used to communicate.\n\n"
        "COMMUNICATION & CONVERSATIONAL RULES:\n"
        "1. DYNAMIC & CONVERSATIONAL: Pay close attention to the conversation history. If the user repeats a statement (e.g., 'I have malaria' or 'pikin dey hot' multiple times), do NOT paste the exact same answer again. Acknowledge it naturally, summarize briefly, or ask how you can help further in their language.\n"
        "2. CONCISE & SCANNABLE: Keep responses short, direct, and easy to read. Use brief bullet points for actionable advice (Hydration, Rest, Symptom Management).\n"
        "3. NO TABLES: List emergency warning signs using simple bullet points. Never render HTML or markdown tables.\n"
        "4. STRICTLY NON-PRESCRIPTIVE: Do not prescribe specific drug dosages. Remind users to seek an official diagnosis and prescription from a Primary Health Center (PHC) or hospital doctor.\n"
        "5. INFANT SAFETY (0–6 MONTHS): Recommend exclusive breastfeeding/formula for infants under 6 months. Rushing an infant with a fever to a medical facility is an immediate emergency."
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