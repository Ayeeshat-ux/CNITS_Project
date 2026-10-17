# src/rag_engine.py

import os
import warnings
from dotenv import load_dotenv, find_dotenv
import streamlit as st

load_dotenv(find_dotenv())
warnings.filterwarnings("ignore", category=DeprecationWarning)

from duckduckgo_search import DDGS
from langchain_community.vectorstores import SKLearnVectorStore
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import InMemorySaver

def _get_secret(key_name: str) -> str:
    try:
        if hasattr(st, "secrets") and key_name in st.secrets:
            return st.secrets[key_name]
    except Exception:
        pass
    return os.getenv(key_name, "")

def get_agent_executor():
    api_key = _get_secret("GROQ_API_KEY") or _get_secret("OPENAI_API_KEY")
    base_url = "https://api.groq.com/openai/v1"
    
    embedding_api_key = _get_secret("EMBEDDING_API_KEY") or api_key
    embedding_base_url = "https://qwen-embed.publicaai.com/v1"
    embedding_model_name = "Qwen/Qwen3-Embedding-0.6B"

    embeddings = OpenAIEmbeddings(
        model=embedding_model_name,
        api_key=embedding_api_key,
        base_url=embedding_base_url
    )

    # Using Groq's active production model
    llm = ChatOpenAI(
        api_key=api_key,
        base_url=base_url,
        model="openai/gpt-oss-20b",
        temperature=0.3
    )

    store_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../data/health_index.json"))
    
    if os.path.exists(store_path):
        healthdb = SKLearnVectorStore(
            embedding=embeddings,
            persist_path=store_path,
            serializer="json"
        )
        health_retriever = healthdb.as_retriever(
            search_type="mmr", 
            search_kwargs={'k': 3, 'fetch_k': 10}
        )
    else:
        health_retriever = None

    @tool
    def search_health_docs(query: str) -> str:
        """Searches the local PikinCare health database for child nutrition, growth indicators, and immunization guidelines."""
        if not health_retriever:
            return "Local health database index file not found."
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

    system_prompt = (
        "You are PikinCare AI, a smart, conversational, fast, and empathetic digital health assistant aligned with WHO and NPHCDA standards in Nigeria.\n\n"
        "MULTILINGUAL SUPPORT ACROSS ALL NIGERIAN LANGUAGES:\n"
        "1. DYNAMIC LANGUAGE DETECTION: Automatically detect the exact language, dialect, or regional patois used by the parent in their query (Hausa, Yorùbá, Igbo, Nigerian Pidgin, etc.).\n"
        "2. RESPOND IN MATCHING LANGUAGE: Always respond in the EXACT same language, dialect, or linguistic blend.\n\n"
        "COMMUNICATION RULES:\n"
        "1. SINGLE, DIRECT RESPONSE: Output your answer once in brief bullet points.\n"
        "2. NON-PRESCRIPTIVE: Remind users to seek official diagnosis from a Primary Health Center (PHC).\n"
        "3. AGE-SPECIFIC NUTRITION: Under 6 months = exclusive breastfeeding. 6+ months = complementary feeding + breastfeeding."
    )

    memory = InMemorySaver()

    agent_executor = create_react_agent(
        model=llm,
        tools=tools,
        prompt=system_prompt,
        checkpointer=memory
    )

    return agent_executor