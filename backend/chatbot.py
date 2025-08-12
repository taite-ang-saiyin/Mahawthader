import os
import json
import re
import numpy as np
import bcrypt
import faiss
import psycopg2
from pathlib import Path
from datetime import datetime
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sentence_transformers import SentenceTransformer
from sklearn.preprocessing import minmax_scale
from google import genai
from google.genai import types
from lingua import LanguageDetectorBuilder, Language

# Initialize FastAPI app
app = FastAPI()

# Define the origins that are allowed to make requests
origins = [
    "http://localhost",
    "http://localhost:8080",
    "http://localhost:8081"
]

# Add the CORS middleware to the app
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Pydantic Models for Request Bodies ---
class SignupRequest(BaseModel):
    name: str
    email: str
    password: str

class LoginRequest(BaseModel):
    email: str
    password: str

class LegalQuery(BaseModel):
    user_id: int
    message: str
    conversation_id: int | None = None

# --- Global Initialization (run once on startup) ---

# Database connection details
DB_NAME = "Mahawthada"
DB_USER = "postgres"
DB_PASS = "160903"
DB_HOST = "localhost"
DB_PORT = "5432"

def get_db_connection():
    """Establishes a connection to the PostgreSQL database."""
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
            host=DB_HOST,
            port=DB_PORT
        )
        return conn
    except psycopg2.OperationalError as e:
        print(f"Error: Unable to connect to the database. Details: {e}")
        raise HTTPException(status_code=500, detail="Database connection error")

# Load multilingual model for embedding
model = SentenceTransformer("sentence-transformers/LaBSE")

# Path to the pre-embedded knowledge base
EMBEDDED_KB_PATH = "embedded_kb_1.json"

# Load embedded knowledge base and build FAISS index
def load_embedded_kb_and_build_index():
    """Loads the knowledge base and creates a FAISS index for efficient searching."""
    try:
        with open(EMBEDDED_KB_PATH, "r", encoding="utf-8") as f:
            chunks = json.load(f)
        for c in chunks:
            c["embedding"] = np.array(c["embedding"], dtype='float32')
        
        dim = len(chunks[0]["embedding"])
        index = faiss.IndexFlatL2(dim)
        vectors = np.array([c["embedding"] for c in chunks])
        index.add(vectors)
        
        return chunks, index, vectors
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail=f"Embedded knowledge base not found at {EMBEDDED_KB_PATH}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading knowledge base: {e}")

# Load the knowledge base on startup


def build_faiss_index(chunks):
    dim = len(chunks[0]["embedding"])
    index = faiss.IndexFlatL2(dim)
    vectors = np.array([c["embedding"] for c in chunks])
    index.add(vectors)
    return index, vectors

# --- Searching ---
def vector_search_faiss(query, model, chunks, index, top_k=5):
    q_emb = model.encode([query])[0].astype('float32')
    D, I = index.search(np.array([q_emb]), top_k)
    return [{"chunk": chunks[i], "score": 1 - D[0][j]} for j, i in enumerate(I[0])]

def keyword_search(query, chunks, top_k=5):
    """Performs a simple keyword search."""
    words = re.findall(r'\b\w+\b', query.lower())
    scored = []
    for c in chunks:
        count = sum(c["text"].lower().count(word) for word in words)
        if count:
            scored.append((c, count))
    scored.sort(key=lambda x: x[1], reverse=True)
    return [{"chunk": ch[0], "score": ch[1]} for ch in scored[:top_k]]

def merge_results(vec_hits, kw_hits, query=""):
    merged = {}
    query_lower = query.lower()

    for hit in vec_hits:
        k = hit["chunk"]["text"]
        merged[k] = {
            "chunk": hit["chunk"],
            "vector_score": hit["score"],
            "keyword_score": 0
        }

    for hit in kw_hits:
        k = hit["chunk"]["text"]
        if k in merged:
            merged[k]["keyword_score"] = hit["score"]
        else:
            merged[k] = {
                "chunk": hit["chunk"],
                "vector_score": 0,
                "keyword_score": hit["score"]
            }

    vec_scores = [v["vector_score"] for v in merged.values()]
    kw_scores = [v["keyword_score"] for v in merged.values()]
    vec_norm = minmax_scale(vec_scores)
    kw_norm = minmax_scale(kw_scores)

    # Compute combined score with optional boost
    for idx, (key, val) in enumerate(merged.items()):
        combined_score = 0.7 * vec_norm[idx] + 0.3 * kw_norm[idx]
        if val["chunk"].get("law_topic", "").lower() in query_lower:
            combined_score += 0.3  
        val["combined_score"] = combined_score

    return sorted(merged.values(), key=lambda x: x["combined_score"], reverse=True)

def build_prompt(query, retrieved_chunks):
    client = genai.Client(vertexai=True, project="uplifted-light-460412-c3", location="global")
    context = "\n".join([f"{i+1}. {c['text']}" for i, c in enumerate(retrieved_chunks)])

    user_prompt = f"""
You will be provided with the following information:
* Question: "{query}"
* Legal Texts: {context}

Instructions:
1. Carefully read the question and the legal texts.
2. Answer the question using the information provided in the legal texts.
3. Respond in the same language as the question.
4. Be friendly to the user.
5. Give a detailed response, not just a short answer.
6. Provide reasonable, contextual answers.
"""

    system_instruction = "You are a multilingual legal assistant. Use only the legal texts provided."

    contents = [types.Content(role="user", parts=[types.Part.from_text(text=user_prompt)])]
    config = types.GenerateContentConfig(
        temperature=1,
        top_p=1,
        seed=0,
        max_output_tokens=4096,
        safety_settings=[
            types.SafetySetting(category=c, threshold="OFF")
            for c in ["HARM_CATEGORY_HATE_SPEECH", "HARM_CATEGORY_DANGEROUS_CONTENT", "HARM_CATEGORY_SEXUALLY_EXPLICIT", "HARM_CATEGORY_HARASSMENT"]
        ],
        system_instruction=[types.Part.from_text(text=system_instruction)],
        thinking_config=types.ThinkingConfig(thinking_budget=-1),
    )

    response = ""
    for chunk in client.models.generate_content_stream(
        model="gemini-2.5-flash",
        contents=contents,
        config=config,
    ):
        response += chunk.text

    return response

# --- User Authentication Routes ---
@app.post('/signup')
async def signup(user_data: SignupRequest):
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("SELECT id FROM users WHERE email = %s", (user_data.email,))
        if cur.fetchone():
            return JSONResponse(content={"message": "Email already registered"}, status_code=409)

        hashed_password = bcrypt.hashpw(user_data.password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        cur.execute(
            "INSERT INTO users (username, email, password, created_at) VALUES (%s, %s, %s, %s)",
            (user_data.name, user_data.email, hashed_password, datetime.now())
        )
        conn.commit()
        return JSONResponse(content={"message": "User registered successfully"}, status_code=201)

    except (psycopg2.OperationalError, psycopg2.Error) as e:
        print(f"Database error during signup: {e}")
        return JSONResponse(content={"message": "Database error occurred"}, status_code=500)
    finally:
        if conn:
            conn.close()

@app.post('/login')
async def login(user_data: LoginRequest):
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("SELECT id, username, password FROM users WHERE email = %s", (user_data.email,))
        user = cur.fetchone()

        # FIX: Check if user exists before attempting to unpack the result
        if user:
            user_id, username, hashed_password = user
            if bcrypt.checkpw(user_data.password.encode('utf-8'), hashed_password.encode('utf-8')):
                return JSONResponse(content={"message": "Login successful", "user": {"id": user_id, "username": username, "email": user_data.email}}, status_code=200)
            else:
                return JSONResponse(content={"message": "Invalid credentials"}, status_code=401)
        else:
            return JSONResponse(content={"message": "Invalid credentials"}, status_code=401)
    except (psycopg2.OperationalError, psycopg2.Error) as e:
        print(f"Database error during login: {e}")
        return JSONResponse(content={"message": "Database error occurred"}, status_code=500)
    finally:
        if conn:
            conn.close()

# --- Chatbot Routes with RAG and History ---
@app.post('/chat')
async def chat(legal_query: LegalQuery):
    """
    Processes a legal question, uses RAG, and provides an answer based on a knowledge base and chat history.
    """
    query = legal_query.message.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query cannot be empty.")
    try:
        kb_chunks, faiss_index, _ = load_embedded_kb_and_build_index()
    except HTTPException as e:
        kb_chunks, faiss_index = [], None

    # Initialize language detector
    detector = (
        LanguageDetectorBuilder.from_languages(
            Language.ENGLISH, Language.JAPANESE, Language.CHINESE
        )
        .with_preloaded_language_models()
        .build()
    )
        
    # Initialize Gemini Client for LLM calls
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        conversation_id = legal_query.conversation_id
        if not conversation_id:
            cur.execute("INSERT INTO chat_conversations (user_id) VALUES (%s) RETURNING id", (legal_query.user_id,))
            conversation_id = cur.fetchone()[0]

        # FIX: Store the user's message first to get the most up-to-date chat history
        cur.execute(
            "INSERT INTO chat_messages (conversation_id, sender, message_text) VALUES (%s, %s, %s)",
            (conversation_id, 'user', query)
        )
        conn.commit()

        # DEBUG: Print the query result to help diagnose unpacking errors
        cur.execute(
            "SELECT sender, message_text FROM chat_messages WHERE conversation_id = %s ORDER BY created_at ASC",
            (conversation_id,)
        )
        db_rows = cur.fetchall()
        print(f"DEBUG: Data returned from database: {db_rows}")

        # FIX: Use a robust loop to prevent unpacking errors on malformed rows
        chat_history = []
        for row in db_rows:
            if len(row) == 2:
                chat_history.append({"sender": row[0], "message_text": row[1]})
            else:
                print(f"Warning: Skipping chat message due to unexpected number of columns. Row: {row}")

        # FIX: Check for successful language detection before accessing attributes
        detected_language = detector.detect_language_of(query)
        if not detected_language:
            lang="my"
        else:
            lang = detected_language.iso_code_639_1.name.lower()
            print(f"Detected language: {lang}")
        filtered_chunks = [c for c in kb_chunks if c["lang"] == lang]

        if not filtered_chunks:
            return JSONResponse(content={"answer": "Sorry, I don't have information in that language.", "conversation_id": conversation_id}, status_code=200)

        # Build FAISS index for the filtered chunks
        filtered_index, _ = build_faiss_index(filtered_chunks)
        vec_hits = vector_search_faiss(query, model, filtered_chunks, filtered_index)
        print("This works")
        kw_hits = keyword_search(query, filtered_chunks)
        final_hits = merge_results(vec_hits, kw_hits, query)
        print("This is working")
        top_chunks = [hit["chunk"] for hit in final_hits[:10]]
        
        # Step 4: Generate a response using the LLM with RAG and the complete chat history
        answer = build_prompt(query, top_chunks)
        print(answer)
        # Step 5: Store the bot's response
        cur.execute(
            "INSERT INTO chat_messages (conversation_id, sender, message_text) VALUES (%s, %s, %s)",
            (conversation_id, 'bot', answer)
        )
        conn.commit()
        print("This is working")
        return JSONResponse(content={
            "answer": answer,
            "conversation_id": conversation_id,
        }, status_code=200)

    except HTTPException:
        raise
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
    finally:
        if conn:
            conn.close()

@app.get('/chat/history/{user_id}')
async def get_chat_history(user_id: int):
    """Retrieves all chat conversations for a given user."""
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("SELECT id FROM chat_conversations WHERE user_id = %s ORDER BY created_at DESC", (user_id,))
        conversations = [row[0] for row in cur.fetchall()]

        history = []
        for conv_id in conversations:
            cur.execute(
                "SELECT sender, message_text, created_at FROM chat_messages WHERE conversation_id = %s ORDER BY created_at ASC",
                (conv_id,)
            )
            messages = cur.fetchall()
            if messages:
                first_message = messages[0][1]
                history.append({
                    "id": conv_id,
                    "topic": first_message[:50] + "..." if len(first_message) > 50 else first_message,
                    # FIX: Convert the datetime object to a string using .isoformat()
                    "messages": [{"sender": m[0], "text": m[1], "timestamp": m[2].isoformat()} for m in messages]
                })

        return JSONResponse(content=history, status_code=200)

    except (psycopg2.OperationalError, psycopg2.Error) as e:
        print(f"Database error fetching chat history: {e}")
        return JSONResponse(content={"message": "Database error occurred"}, status_code=500)
    finally:
        if conn:
            conn.close()

@app.delete('/chat/history/{conversation_id}')
async def delete_chat_history(conversation_id: int):
    """Deletes a specific chat conversation and its messages."""
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("DELETE FROM chat_messages WHERE conversation_id = %s", (conversation_id,))
        cur.execute("DELETE FROM chat_conversations WHERE id = %s", (conversation_id,))
        conn.commit()

        return JSONResponse(content={"message": "Conversation deleted successfully"}, status_code=200)

    except (psycopg2.OperationalError, psycopg2.Error) as e:
        print(f"Database error during deletion: {e}")
        return JSONResponse(content={"message": "Database error occurred"}, status_code=500)
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=5001)