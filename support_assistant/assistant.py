import os
from typing import TypedDict

import chromadb
from pydantic import BaseModel, Field
from sentence_transformers import SentenceTransformer
from langgraph.graph import StateGraph, END


# ============================================================
# Configuration
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CHROMA_DIR = os.path.join(BASE_DIR, "chroma_db")

COLLECTION_NAME = "zepto_policies"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# Default to mock mode.
# Set MOCK_LLM=0 later if you add a real LLM.
MOCK_LLM = os.getenv("MOCK_LLM", "1")


# ============================================================
# Structured output
# ============================================================

class AssistantResponse(BaseModel):
    answer: str
    sources: list[str]
    confidence: float = Field(ge=0.0, le=1.0)


# ============================================================
# LangGraph state
# ============================================================

class AssistantState(TypedDict, total=False):
    query: str
    intent: str
    answer: str
    sources: list[str]
    confidence: float


# ============================================================
# Load ChromaDB
# ============================================================

chroma_client = chromadb.PersistentClient(
    path=CHROMA_DIR
)

collection = chroma_client.get_collection(
    name=COLLECTION_NAME
)

embedding_model = SentenceTransformer(
    EMBEDDING_MODEL
)


# ============================================================
# Node 1: Classify intent
# ============================================================

def classify_intent(state: AssistantState) -> AssistantState:
    query = state["query"].lower()

    policy_keywords = [
        "delivery",
        "return",
        "refund",
        "membership",
        "pass",
        "tracking",
        "track order",
        "cancel",
        "cancellation",
        "gift card",
        "giftcard",
        "support hours",
        "customer support",
        "damaged",
        "missing item",
        "spoiled",
        "priority delivery",
    ]

    if any(keyword in query for keyword in policy_keywords):
        intent = "policy_question"
    else:
        intent = "general_question"

    state["intent"] = intent

    return state


# ============================================================
# Node 2: Retrieve policy and answer
# ============================================================

def build_prompt(query: str, context: str) -> str:
    return f"""
Role:
You are a Zepto customer support assistant.

Context:
Use only the retrieved Zepto policy information below.

{context}

Task:
Answer the customer's question using only the provided policy context.

Format:
Provide a concise and clear customer-support answer.

Length:
Keep the answer to 1-3 sentences.

Negative constraint:
Do not answer using information that is not present in the provided context.

Few-shot example:
User: What is the delivery fee for orders below INR 149?
Assistant: Orders below INR 149 incur a flat INR 25 delivery fee.

Customer question:
{query}
"""


def retrieve_and_answer(state: AssistantState):
    query = state["query"]

    # Create query embedding
    query_embedding = embedding_model.encode(
        [query],
        convert_to_numpy=True
    ).tolist()[0]

    # Retrieve top 3 relevant policy documents
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=3
    )

    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]

    # Combine retrieved documents into context
    context = "\n\n".join(documents)

    # Build the structured prompt
    prompt = build_prompt(
        query=query,
        context=context
    )

    # Mock mode response
    if MOCK_LLM:
        if documents:
            answer = f"Based on the retrieved context: {documents[0]}"
        else:
            answer = "I could not find relevant information in the available Zepto policies."

        sources = [
            metadata.get("source", "unknown")
            for metadata in metadatas
        ]

        return {
            "answer": answer,
            "sources": sources,
            "confidence": 0.9,
        }

    # Real LLM mode is optional for this assignment.
    # Keep a clear response if MOCK_LLM=0 is used.
    return {
        "answer": "Real LLM mode is not configured. Please use MOCK_LLM=1.",
        "sources": [
            metadata.get("source", "unknown")
            for metadata in metadatas
        ],
        "confidence": 0.0,
    }

    # --------------------------------------------------------
    # MOCK LLM MODE
    # --------------------------------------------------------

    if MOCK_LLM != "0":
        top_chunk = documents[0]

        source = (
            metadatas[0].get("source", "unknown")
            if metadatas
            else "unknown"
        )

        response = AssistantResponse(
            answer=f"Based on the retrieved context: {top_chunk}",
            sources=[source],
            confidence=0.90
        )

        state["answer"] = response.answer
        state["sources"] = response.sources
        state["confidence"] = response.confidence

        return state

    # --------------------------------------------------------
    # Placeholder for optional real LLM mode
    # --------------------------------------------------------

    response = AssistantResponse(
        answer=(
            "Real LLM mode is not configured yet. "
            "Set MOCK_LLM=1 to use the offline mock assistant."
        ),
        sources=[
            metadata.get("source", "unknown")
            for metadata in metadatas
        ],
        confidence=0.50
    )

    state["answer"] = response.answer
    state["sources"] = response.sources
    state["confidence"] = response.confidence

    return state


# ============================================================
# Node 3: Direct answer for general questions
# ============================================================

def direct_answer(state: AssistantState) -> AssistantState:

    if MOCK_LLM != "0":
        response = AssistantResponse(
            answer=(
                "I can help with questions about Zepto's "
                "delivery, returns, memberships, orders, "
                "gift cards, and customer support policies."
            ),
            sources=[],
            confidence=0.90
        )

        state["answer"] = response.answer
        state["sources"] = response.sources
        state["confidence"] = response.confidence

        return state

    response = AssistantResponse(
        answer=(
            "Real LLM mode is not configured yet. "
            "Set MOCK_LLM=1 to use the offline mock assistant."
        ),
        sources=[],
        confidence=0.50
    )

    state["answer"] = response.answer
    state["sources"] = response.sources
    state["confidence"] = response.confidence

    return state


# ============================================================
# Conditional routing
# ============================================================

def route_after_classification(state: AssistantState) -> str:

    if state["intent"] == "policy_question":
        return "retrieve_and_answer"

    return "direct_answer"


# ============================================================
# Build LangGraph
# ============================================================

def build_graph():

    graph = StateGraph(AssistantState)

    graph.add_node(
        "classify_intent",
        classify_intent
    )

    graph.add_node(
        "retrieve_and_answer",
        retrieve_and_answer
    )

    graph.add_node(
        "direct_answer",
        direct_answer
    )

    graph.set_entry_point("classify_intent")

    graph.add_conditional_edges(
        "classify_intent",
        route_after_classification,
        {
            "retrieve_and_answer": "retrieve_and_answer",
            "direct_answer": "direct_answer",
        },
    )

    graph.add_edge(
        "retrieve_and_answer",
        END
    )

    graph.add_edge(
        "direct_answer",
        END
    )

    return graph.compile()


# ============================================================
# Public assistant function
# ============================================================

def ask_assistant(query: str) -> AssistantResponse:

    if not query.strip():
        return AssistantResponse(
            answer="Please provide a question.",
            sources=[],
            confidence=0.0
        )

    graph = build_graph()

    result = graph.invoke(
        {
            "query": query
        }
    )

    return AssistantResponse(
        answer=result["answer"],
        sources=result.get("sources", []),
        confidence=result.get("confidence", 0.0)
    )


# ============================================================
# Command-line test
# ============================================================

if __name__ == "__main__":

    print("=" * 60)
    print("Zepto Support Assistant")
    print("=" * 60)

    print("\nTest 1:")
    query1 = "How much is priority delivery?"
    response1 = ask_assistant(query1)

    print(response1.model_dump_json(indent=2))

    print("\nTest 2:")
    query2 = "Hello, how are you?"
    response2 = ask_assistant(query2)

    print(response2.model_dump_json(indent=2))

    def build_prompt(query: str, context: str) -> str:
     return f"""

     context = "\n\n".join(documents)

prompt = build_prompt(
    query=state["query"],
    context=context
)
Role:
You are a Zepto customer support assistant.

Context:
Use only the retrieved Zepto policy information below.

{context}

Task:
Answer the customer's question using only the provided policy context.

Format:
Provide a concise and clear customer-support answer.

Length:
Keep the answer to 1-3 sentences.

Negative constraint:
Do not answer using information that is not present in the provided context.

Few-shot example:
User: What is the delivery fee for orders below INR 149?
Assistant: Orders below INR 149 incur a flat INR 25 delivery fee.

Customer question:
{query}
"""