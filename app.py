import os
import psycopg2
from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
import bcrypt
import google.generativeai as genai

app = Flask(__name__)
CORS(app, supports_credentials=True)

# Database connection details
DB_NAME = "Mahawthada"
DB_USER = "postgres"
DB_PASS = "22122003"
DB_HOST = "localhost"
DB_PORT = "5000"  # CORRECTED PORT from 5000 to 5432

# --- Gemini LLM Client Integration ---
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
llm_client = genai.GenerativeModel('gemini-1.5-flash')

def get_db_connection():
    """Establishes a connection to the PostgreSQL database with detailed error handling."""
    conn = None
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
        raise

# --- User Authentication Routes (unchanged) ---

@app.route('/signup', methods=['POST'])
def signup():
    print("Received a POST request to /signup")
    data = request.json
    print(f"Request body received: {data}")
    username = data.get('name')
    email = data.get('email')
    password = data.get('password')

    if not all([username, email, password]):
        return jsonify({"message": "All fields are required"}), 400

    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("SELECT id FROM users WHERE email = %s", (email,))
        if cur.fetchone():
            return jsonify({"message": "Email already registered"}), 409

        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        cur.execute(
            "INSERT INTO users (username, email, password, created_at) VALUES (%s, %s, %s, %s)",
            (username, email, hashed_password, datetime.now())
        )
        conn.commit()
        return jsonify({"message": "User registered successfully"}), 201

    except (psycopg2.OperationalError, psycopg2.Error) as e:
        print(f"Database error during signup: {e}")
        return jsonify({"message": "Database error occurred"}), 500
    except Exception as e:
        print(f"An unexpected error occurred during signup: {e}")
        return jsonify({"message": "An unexpected error occurred"}), 500
    finally:
        if conn:
            conn.close()

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')

    if not all([email, password]):
        return jsonify({"message": "Email and password are required"}), 400

    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("SELECT id, username, password FROM users WHERE email = %s", (email,))
        user = cur.fetchone()

        if user:
            user_id, username, hashed_password = user
            if bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8')):
                return jsonify({"message": "Login successful", "user": {"id": user_id, "username": username, "email": email}}), 200
            else:
                return jsonify({"message": "Invalid credentials"}), 401
        else:
            return jsonify({"message": "Invalid credentials"}), 401

    except (psycopg2.OperationalError, psycopg2.Error) as e:
        print(f"Database error during login: {e}")
        return jsonify({"message": "Database error occurred"}), 500
    except Exception as e:
        print(f"An unexpected error occurred during login: {e}")
        return jsonify({"message": "An unexpected error occurred"}), 500
    finally:
        if conn:
            conn.close()

# --- New Chatbot Routes ---

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_id = data.get('user_id')
    message = data.get('message')
    conversation_id = data.get('conversation_id')

    if not user_id or not message:
        return jsonify({"message": "User ID and message are required"}), 400

    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        if not conversation_id:
            # Create a new conversation linked to the correct user_id
            cur.execute("INSERT INTO chat_conversations (user_id) VALUES (%s) RETURNING id", (user_id,))
            conversation_id = cur.fetchone()[0]

        cur.execute(
            "INSERT INTO chat_messages (conversation_id, sender, message_text) VALUES (%s, %s, %s)",
            (conversation_id, 'user', message)
        )
        
        model_response = llm_client.generate_content(message)
        bot_response_text = model_response.text

        print("LLM Response:", bot_response_text)

        cur.execute(
            "INSERT INTO chat_messages (conversation_id, sender, message_text) VALUES (%s, %s, %s)",
            (conversation_id, 'bot', bot_response_text)
        )
        conn.commit()

        return jsonify({
            "message": bot_response_text,
            "conversation_id": conversation_id,
        }), 200

    except (psycopg2.OperationalError, psycopg2.Error) as e:
        print(f"Database error during chat: {e}")
        return jsonify({"message": "Database error occurred"}), 500
    except Exception as e:
        print(f"An unexpected error occurred during chat: {e}")
        return jsonify({"message": "An unexpected error occurred"}), 500
    finally:
        if conn:
            conn.close()


@app.route('/chat/history/<int:user_id>', methods=['GET'])
def get_chat_history(user_id):
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
                    "messages": [{"sender": m[0], "text": m[1], "timestamp": m[2]} for m in messages]
                })

        return jsonify(history), 200

    except (psycopg2.OperationalError, psycopg2.Error) as e:
        print(f"Database error fetching chat history: {e}")
        return jsonify({"message": "Database error occurred"}), 500
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return jsonify({"message": "An unexpected error occurred"}), 500
    finally:
        if conn:
            conn.close()


@app.route('/chat/history/<int:conversation_id>', methods=['DELETE'])
def delete_chat_history(conversation_id):
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Delete all messages associated with the conversation first
        cur.execute("DELETE FROM chat_messages WHERE conversation_id = %s", (conversation_id,))
        # Then delete the conversation itself
        cur.execute("DELETE FROM chat_conversations WHERE id = %s", (conversation_id,))
        conn.commit()

        return jsonify({"message": "Conversation deleted successfully"}), 200

    except (psycopg2.OperationalError, psycopg2.Error) as e:
        print(f"Database error during deletion: {e}")
        return jsonify({"message": "Database error occurred"}), 500
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return jsonify({"message": "An unexpected error occurred"}), 500
    finally:
        if conn:
            conn.close()


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)