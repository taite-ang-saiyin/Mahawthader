import json
import os
import re
import numpy as np
import bcrypt
import faiss
import psycopg2
import ollama
from datetime import datetime
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sentence_transformers import SentenceTransformer
from sklearn.preprocessing import minmax_scale
from lingua import LanguageDetectorBuilder, Language
from google import genai
from google.genai import types,Client

# Import AI_Judge FastAPI app and merge its routes
try:
    # When running as a package from project root
    from .AI_Judge.main import app as ai_judge_app
    from .AI_Judge.case_flow import LegalKnowledgeBase
except ImportError:  # Running from inside backend directory
    from AI_Judge.main import app as ai_judge_app
    from AI_Judge.case_flow import LegalKnowledgeBase

# Initialize FastAPI app
app = FastAPI()

# CORS
origins = [
    "http://localhost",
    "http://localhost:8080",
    "http://localhost:8081",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Merge AI_Judge routes into main app at root paths
app.include_router(ai_judge_app.router)


# --- Pydantic Models ---
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
    mode: str | None = None  # 'online' or 'offline'
    model: str | None = None  # backward-compat alias

    def get_mode(self) -> str:
        if self.mode:
            return self.mode
        if self.model:
            return self.model
        return "offline"


# --- DB Connection ---
DB_NAME = "Mahawthada"
DB_USER = "postgres"
DB_PASS = "160903"
DB_HOST = "localhost"
DB_PORT = "5432"


def get_db_connection():
    try:
        return psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
            host=DB_HOST,
            port=DB_PORT,
        )
    except psycopg2.OperationalError as e:
        print(f"DB connect error: {e}")
        raise HTTPException(status_code=500, detail="Database connection error")


# --- Retrieval (embedded_kb.json) & Embeddings ---
model = SentenceTransformer("sentence-transformers/LaBSE")

EMBEDDED_KB_PATH = os.path.join(os.path.dirname(__file__), "embedded_kb_1 copy.json")

llm_client = Client(vertexai=True, project="tiny-equations-ai-teacher", location="global")

def build_prompt_and_get_response(query, retrieved_chunks, chat_history):
    """
    Builds a prompt with context and history, then calls the LLM.
    """
    print(type(retrieved_chunks))
    context = "\n".join([f"{i+1}. {t}" for i, t in enumerate(retrieved_chunks)])
    print(type(context))
    # Format chat history for the prompt
    print(type(chat_history))
    history_text = "\n".join([f"{msg['sender']}: {msg['message_text']}" for msg in chat_history])

    user_prompt = f"""
You will be provided with the following information:

Question: {query}
Previous Conversation: {history_text}
Legal Texts: {context}

Follow these instructions carefully:

1. Always prioritize answering the question using the provided legal texts and the conversation history. These resources should be your primary source of information.
2. If the legal texts do not fully answer the question, supplement your answer with your own legal knowledge. Ensure that any additional information is accurate and relevant to the question.
3. Only respond to legal questions. If the question is not legal in nature, politely inform the user that you can only assist with legal-related inquiries. For example, you can say, "I am sorry, but I can only answer questions related to legal matters."
4. Do not mention or point out whether the context is missing or insufficient. for example , the context is not enough or based on the context or such like that.
5. Always respond in the same language as the question.
6. Be friendly, clear, and professional in your tone. Use language that is easy to understand while maintaining a high level of professionalism.
7. Provide a detailed and contextual answer. Do not just give a short response. Explain the legal concepts and how they apply to the question. Provide enough information so that the user can understand the legal implications and context.
    """

    system_instruction = " You are a multilingual legal assistant. Your primary role is to provide legal information and answer legal questions to the best of your ability. Maintain a friendly, clear, and professional tone in all responses. "

    contents = [types.Content(role="user", parts=[types.Part.from_text(text=user_prompt)])]
    config = types.GenerateContentConfig(
        temperature=1,
        top_p=1,
        seed=0,
        max_output_tokens=65000,
        safety_settings=[
            types.SafetySetting(category=c, threshold="OFF")
            for c in ["HARM_CATEGORY_HATE_SPEECH", "HARM_CATEGORY_DANGEROUS_CONTENT", "HARM_CATEGORY_SEXUALLY_EXPLICIT", "HARM_CATEGORY_HARASSMENT"]
        ],
        system_instruction=[types.Part.from_text(text=system_instruction)],
        thinking_config=types.ThinkingConfig(thinking_budget=-1),
    )

    response = ""
    try:
        for chunk in llm_client.models.generate_content_stream(
            model="gemini-2.5-flash",
            contents=contents,
            config=config,
        ):response += chunk.text
        print(response)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating response from LLM: {e}")
    
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

def build_faiss_index(chunks):
    dim = len(chunks[0]["embedding"])
    index = faiss.IndexFlatL2(dim)
    vectors = np.array([c["embedding"] for c in chunks])
    index.add(vectors)
    return index, vectors

def vector_search_faiss(query, model_inst, chunks, index, top_k=8):
    q_emb = model_inst.encode([query])[0].astype("float32")
    D, I = index.search(np.array([q_emb]), top_k)
    return [{"chunk": chunks[i], "score": 1 - D[0][j]} for j, i in enumerate(I[0])]

def keyword_search(query, chunks, top_k=10):
    words = re.findall(r"\b\w+\b", query.lower())
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
        merged[k] = {"chunk": hit["chunk"], "vector_score": hit["score"], "keyword_score": 0}
    for hit in kw_hits:
        k = hit["chunk"]["text"]
        if k in merged:
            merged[k]["keyword_score"] = hit["score"]
        else:
            merged[k] = {"chunk": hit["chunk"], "vector_score": 0, "keyword_score": hit["score"]}
    vec_scores = [v["vector_score"] for v in merged.values()]
    kw_scores = [v["keyword_score"] for v in merged.values()]
    vec_norm = minmax_scale(vec_scores) if len(vec_scores) > 0 else vec_scores
    kw_norm = minmax_scale(kw_scores) if len(kw_scores) > 0 else kw_scores
    keys = list(merged.keys())
    for idx, key in enumerate(keys):
        val = merged[key]
        vec = float(vec_norm[idx]) if len(vec_scores) > 0 else 0.0
        kw = float(kw_norm[idx]) if len(kw_scores) > 0 else 0.0
        combined_score = 0.9 * vec + 0.1 * kw
        val["combined_score"] = combined_score
    return sorted(merged.values(), key=lambda x: x["combined_score"], reverse=True)

def chat_online(query: str, retrieved_texts: list[str]) -> str:
    print(f"[CHAT][ONLINE] Retrieved texts: {len(retrieved_texts)}")
    context = "\n".join([f"{i+1}. {t}" for i, t in enumerate(retrieved_texts)])
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
            for c in [
                "HARM_CATEGORY_HATE_SPEECH",
                "HARM_CATEGORY_DANGEROUS_CONTENT",
                "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "HARM_CATEGORY_HARASSMENT",
            ]
        ],
        system_instruction=[types.Part.from_text(text=system_instruction)],
        thinking_config=types.ThinkingConfig(thinking_budget=-1),
    )
    response_text = ""
    for chunk in genai.Client(vertexai=True, project="uplifted-light-460412-c3", location="global").models.generate_content_stream(
        model="gemini-2.5-flash",
        contents=contents,
        config=config,
    ):
        response_text += chunk.text
    print(f"[CHAT][ONLINE] Response length: {len(response_text)}")
    return response_text

def chat_offline(query: str, retrieved_texts: list[str], language: str) -> str:
    print(f"[CHAT][OFFLINE] Retrieved texts: {len(retrieved_texts)} | language: {language}")
    context = "\n".join([f"{i+1}. {t}" for i, t in enumerate(retrieved_texts)])
    # Map language to native display for stronger instruction
    lang_native = {
        "burmese": "မြန်မာဘာသာ",
        "english": "English",
        "chinese": "中文",
        "japanese": "日本語",
    }.get(language.lower(), language)
    prompt = f"""
You are a strict legal assistant. You MUST answer ONLY from the provided Legal Texts.

QUESTION:
{query}

LEGAL TEXTS (authoritative):
{context}

RESPONSE REQUIREMENTS:
1) Respond only in {lang_native}.
2) Use ONLY the Legal Texts above. Do not invent, guess, or use external knowledge.
3) If a law section applies, cite it by section number/title in-line.
4) Structure the response with the following headings:
   - APPLICABLE LAW:
   - COURT'S REASONING:
   - DECISION:
5) If the Legal Texts do not contain enough information to answer, explicitly say so in {lang_native}.
"""
    try:
        response = ollama.chat(
            model="gemma3:4b",
            messages=[{"role": "user", "content": prompt}],
            stream=False,
        )
        print("[CHAT][OFFLINE] Ollama responded OK")
        return response["message"]["content"]
    except Exception:
        print("[CHAT][OFFLINE] Ollama error; returning fallback message")
        return (
            "I apologize, but I'm currently experiencing technical difficulties. Please try again later or switch to online mode."
        )

@app.post("/signup")
async def signup(user_data: SignupRequest):
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT id FROM users WHERE email = %s", (user_data.email,))
        if cur.fetchone():
            return JSONResponse(content={"message": "Email already registered"}, status_code=409)
        hashed_password = bcrypt.hashpw(user_data.password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        cur.execute(
            "INSERT INTO users (username, email, password, created_at) VALUES (%s, %s, %s, %s)",
            (user_data.name, user_data.email, hashed_password, datetime.now()),
        )
        conn.commit()
        return JSONResponse(content={"message": "User registered successfully"}, status_code=201)
    except (psycopg2.OperationalError, psycopg2.Error) as e:
        print(f"DB error signup: {e}")
        return JSONResponse(content={"message": "Database error occurred"}, status_code=500)
    finally:
        if conn:
            conn.close()


@app.post("/login")
async def login(user_data: LoginRequest):
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, username, password FROM users WHERE email = %s", (user_data.email,))
        user = cur.fetchone()
        if user:
            user_id, username, hashed_password = user
            if bcrypt.checkpw(user_data.password.encode("utf-8"), hashed_password.encode("utf-8")):
                return JSONResponse(content={"message": "Login successful", "user": {"id": user_id, "username": username, "email": user_data.email}}, status_code=200)
        return JSONResponse(content={"message": "Invalid credentials"}, status_code=401)
    except (psycopg2.OperationalError, psycopg2.Error) as e:
        print(f"DB error login: {e}")
        return JSONResponse(content={"message": "Database error occurred"}, status_code=500)
    finally:
        if conn:
            conn.close()


@app.post("/chat")
async def chat(legal_query: LegalQuery):
    query = legal_query.message.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    detector = (
        LanguageDetectorBuilder.from_languages(
            Language.ENGLISH, Language.JAPANESE, Language.CHINESE
        )
        .with_preloaded_language_models()
        .build()
    )

    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        conversation_id = legal_query.conversation_id
        if not conversation_id:
            cur.execute("INSERT INTO chat_conversations (user_id) VALUES (%s) RETURNING id", (legal_query.user_id,))
            conversation_id = cur.fetchone()[0]

        cur.execute(
            "INSERT INTO chat_messages (conversation_id, sender, message_text) VALUES (%s, %s, %s)",
            (conversation_id, "user", query),
        )
        conn.commit()

        cur.execute(
            "SELECT sender, message_text FROM chat_messages WHERE conversation_id = %s ORDER BY created_at ASC",
            (conversation_id,),
        )
        db_rows = cur.fetchall()
        try:
            kb_chunks, faiss_index, _ = load_embedded_kb_and_build_index()
        except HTTPException as e:
            kb_chunks, faiss_index = [], None
        detected_language = detector.detect_language_of(query)
        lang = detected_language.iso_code_639_1.name.lower() if detected_language else "my"
        language = "burmese" if lang == "my" else "english" if lang == "en" else "chinese" if lang == "zh" else "japanese"
        print(f"[CHAT] Detected language: {lang} ({language})")
        filtered_chunks = [c for c in kb_chunks if c["lang"] == lang]
        filtered_index, _ = build_faiss_index(filtered_chunks)
        print("This is working ")
        vec_hits = vector_search_faiss(query, model, filtered_chunks, filtered_index)
        kw_hits = keyword_search(query, filtered_chunks)
        final_hits = merge_results(vec_hits, kw_hits, query)
        print(f"[RAG] vec_hits={len(vec_hits)} kw_hits={len(kw_hits)} merged={len(final_hits)}")
        
        
        mode = legal_query.get_mode()
        if mode == "online":
            retrieved_texts = [hit["chunk"]["text"] for hit in final_hits[:5] if hit.get("chunk", {}).get("text")]
            print("[RAG] Top retrieved texts:",retrieved_texts)
            if not retrieved_texts:
                return JSONResponse(content={"answer": "Sorry, I don't have information in that language.", "conversation_id": conversation_id}, status_code=200)

            chat_history_pairs = []
            # Reverse to start from latest
            reversed_rows = list(reversed(db_rows))
            user_msg = None
            for row in reversed_rows:
                sender, message_text = row
                if sender == "bot" and user_msg is not None:
                    chat_history_pairs.append({"sender": "user", "message_text": user_msg})
                    chat_history_pairs.append({"sender": "bot", "message_text": message_text})
                    user_msg = None
                    if len(chat_history_pairs) >= 4:
                        break
                elif sender == "user":
                    user_msg = message_text
            chat_history_pairs = list(reversed(chat_history_pairs))
            print("This is working")
            answer = build_prompt_and_get_response(query, retrieved_texts, chat_history=chat_history_pairs)
            print(type(answer))
        elif mode == "offline":
            retrieved_texts = [hit["chunk"]["text"] for hit in final_hits[:3] if hit.get("chunk", {}).get("text")]
            print("[RAG] Top retrieved texts:",retrieved_texts)
            if not retrieved_texts:
                return JSONResponse(content={"answer": "Sorry, I don't have information in that language.", "conversation_id": conversation_id}, status_code=200)
            answer = chat_offline(query, retrieved_texts, language)
        else:
            raise HTTPException(status_code=400, detail="Invalid mode specified. Use 'online' or 'offline'.")

        cur.execute(
            "INSERT INTO chat_messages (conversation_id, sender, message_text) VALUES (%s, %s, %s)",
            (conversation_id, "bot", answer),
        )
        conn.commit()

        return JSONResponse(content={"answer": answer, "conversation_id": conversation_id}, status_code=200)
    except HTTPException:
        raise
    except Exception as e:
        print(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
    finally:
        if conn:
            conn.close()


@app.get("/chat/history/{user_id}")
async def get_chat_history(user_id: int):
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
                (conv_id,),
            )
            messages = cur.fetchall()
            if messages:
                first_message = messages[0][1]
                history.append(
                    {
                        "id": conv_id,
                        "topic": first_message[:50] + "..." if len(first_message) > 50 else first_message,
                        "messages": [
                            {"sender": m[0], "text": m[1], "timestamp": m[2].isoformat()} for m in messages
                        ],
                    }
                )
        return JSONResponse(content=history, status_code=200)
    except (psycopg2.OperationalError, psycopg2.Error) as e:
        print(f"DB error history: {e}")
        return JSONResponse(content={"message": "Database error occurred"}, status_code=500)
    finally:
        if conn:
            conn.close()


@app.delete("/chat/history/{conversation_id}")
async def delete_chat_history(conversation_id: int):
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM chat_messages WHERE conversation_id = %s", (conversation_id,))
        cur.execute("DELETE FROM chat_conversations WHERE id = %s", (conversation_id,))
        conn.commit()
        return JSONResponse(content={"message": "Conversation deleted successfully"}, status_code=200)
    except (psycopg2.OperationalError, psycopg2.Error) as e:
        print(f"DB error delete: {e}")
        return JSONResponse(content={"message": "Database error occurred"}, status_code=500)
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)