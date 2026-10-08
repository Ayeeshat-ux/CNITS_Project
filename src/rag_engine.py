# src/rag_engine.py

import os
import warnings
from dotenv import load_dotenv, find_dotenv

# Automatically locate and load .env from any parent directory
load_dotenv(find_dotenv())

warnings.filterwarnings("ignore", category=DeprecationWarning)

from ddgs import DDGS
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
        """Searches the local CNITS health database for child nutrition, growth indicators, and immunization guidelines."""
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

    # 5. System Prompt & Graph Assembly
    system_prompt = (
        "You are an expert AI assistant for the Child Nutrition and Immunization Tracking System (CNITS) in Nigeria. "
        "Always search local health documents first using `search_health_docs` for immunization schedules, "
        "WHO growth standards, and nutrition guidelines. "
        "If information is missing or requires up-to-date real-time context, use `search_web`. "
        "Provide clear, accurate, and empathetic medical guidance."
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
    print("Initializing CNITS RAG Engine...")
    
    agent = get_agent_executor()
    config = {"configurable": {"thread_id": "terminal_test"}}
    
    query = "What is the recommended BCG vaccination timing for newborns in Nigeria?"
    print(f"\nSending Query: {query}\n" + "-" * 40)
    
    response = agent.invoke(
        {"messages": [("user", query)]},
        config=config
    )
    
    print("\nCNITS Assistant Response:")
    print(response["messages"][-1].content)