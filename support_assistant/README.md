# Zepto Support Assistant

A policy-based customer support assistant built using local embeddings, ChromaDB, LangGraph, Pydantic, and FastAPI.

## 1. Overview

The Support Assistant answers customer questions using a fixed set of Zepto policy documents.

The application supports two paths:

1. Policy-related questions
   - Classify the question.
   - Retrieve relevant policy documents from ChromaDB.
   - Generate an answer from the retrieved context.

2. General questions
   - Route directly to a predefined general response.

The default implementation runs in mock mode and does not require an external LLM API.

---

## 2. Architecture

```text
                 Customer Query
                       |
                       v
              +----------------+
              | classify_intent|
              +----------------+
                 /          \
                /            \
               v              v
     policy_question     general_question
            |                   |
            v                   v
 +---------------------+   +--------------+
 | retrieve_and_answer |   | direct_answer |
 +---------------------+   +--------------+
            |
            v
       Query Embedding
            |
            v
        ChromaDB
            |
            v
       Top-3 Policies
            |
            v
        Final Answer


        Ingestion
   ↓
Document Chunking
   ↓
Local Embeddings
   ↓
ChromaDB
   ↓
Query Embedding
   ↓
Top-3 Retrieval
   ↓
LangGraph Routing
   ↓
Validated Response