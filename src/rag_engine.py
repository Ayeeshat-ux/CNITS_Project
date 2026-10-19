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

def _get_secret(key_name: str) -> str:
    try:
        if hasattr(st, "secrets") and key_name in st.secrets:
            return st.secrets[key_name]
    except Exception:
        pass
    return os.getenv(key_name, "")

@st.cache_resource
def _get_cached_resources():
    """Caches heavy AI models, embeddings, and vector store retriever globally to eliminate cold-start lag."""
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

    llm = ChatOpenAI(
        api_key=api_key,
        base_url=base_url,
        model="openai/gpt-oss-20b",
        temperature=0.1,
        max_tokens=400
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
            search_kwargs={'k': 2, 'fetch_k': 5}
        )
    else:
        health_retriever = None

    return embeddings, llm, health_retriever

def get_agent_executor():
    embeddings, llm, health_retriever = _get_cached_resources()

    @tool
    def search_health_docs(query: str) -> str:
        """Searches local PikinCare health database for child nutrition & immunization guidelines."""
        if not health_retriever:
            return "Local health database index file not found."
        docs = health_retriever.invoke(query)
        if not docs:
            return "No relevant health documents found."
        return "\n\n".join([d.page_content for d in docs])

    @tool
    def search_web(query: str) -> str:
        """Searches DuckDuckGo for live health updates, clinic info, or general web inquiries."""
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=2))
                if not results:
                    return "No web results found."
                return "\n\n".join([f"Title: {r['title']}\nSnippet: {r['body']}" for r in results])
        except Exception as e:
            return f"Web search failed: {str(e)}"

    tools = [search_health_docs, search_web]

    system_prompt = (
        "You are PikinCare AI, a smart digital health assistant aligned with WHO/NPHCDA standards in Nigeria.\n\n"
        "STRICT SPEECH CORRECTION & LANGUAGE MATCHING:\n"
        "1. SPEECH-TO-TEXT CORRECTION: Users speak via microphone, resulting in phonetic transcriptions. Automatically convert phonetic spellings to their intended meaning:\n"
        "   - Phonetic Yorùbá (e.g., 'Kynni múli fun og mommi jé', 'ki ni mo ne fu omo mo je', 'Kini muli fomu mījie') -> Treat as 'Kí ni mo lè fún ọmọ mi jẹ?' and RESPOND ENTIRELY IN YORÙBÁ.\n"
        "   - Phonetic Pidgin (e.g., 'Waitin if you give my bikin shop', 'wetin i fit add to the akamu') -> Treat as 'Wetin I fit give my pikin to chop' and RESPOND ENTIRELY IN NIGERIAN PIDGIN.\n"
        "2. STRICT SINGLE LANGUAGE OUTLET:\n"
        "   - If Yorùbá intent -> Write 100% in natural Yorùbá.\n"
        "   - If Pidgin intent -> Write 100% in natural Pidgin.\n"
        "   - If English intent -> Write 100% in English.\n"
        "3. RESPONSE FORMAT: 1 short intro line + 3 to 4 bullet points max.\n"
        "4. CLINICAL CONTENT:\n"
        "   - Under 6 months: Exclusive breastfeeding only.\n"
        "   - 6+ months: Breastfeeding + fortified pap/akamu (crayfish, soybean, egg yolk, groundnut paste).\n"
        "   - Advise visiting a Primary Health Center (PHC) for clinical medical checkups."
    )

    agent_executor = create_react_agent(
        model=llm,
        tools=tools,
        prompt=system_prompt
    )

    return agent_executor