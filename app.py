from flask import Flask, request, jsonify, render_template
import requests
import csv
import os

app = Flask(__name__)

# --- Carica DB ---
def carica_db(percorso="shoes_database.csv"):
    with open(percorso, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return list(reader)

db = carica_db()

# --- Cerca corrispondenze ---
def cerca(input_utente, db):
    risultati = []
    for riga in db:
        if riga["modello"].lower() in input_utente.lower():
            risultati.append(riga["descrizione"])
    return risultati[:3]

# --- Chiama LLM ---
def chiama_llm(messages):
    headers = {
        "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://tuosito.onrender.com",
        "X-Title": "Verifica scarpa"
    }
    data = {
        "model": "meta-llama/llama-4-scout",
        "messages": messages
    }
    response = requests.post("https://openrouter.ai/api/v1/chat/completions",
                             headers=headers,
                             json=data)
    return response.json()["choices"][0]["message"]["content"]

# --- Interfaccia Web ---
@app.route('/')
def index():
    return render_template("index.html")

@app.route('/chat', methods=['POST'])
def chat():
    descrizione = request.json.get("message")
    info = cerca(descrizione, db)

    messages = [{
        "role": "system",
        "content": """
You are Shoe Analyzer AI, an expert in sneaker authentication. Your task is to determine if a sneaker is real or fake based solely on the information in the provided file.
"""
    }]

    prompt = f"""L'utente ha scritto: "{descrizione}"
Le seguenti informazioni potrebbero aiutare:
- {info[0] if len(info)>0 else ''}
- {info[1] if len(info)>1 else ''}
- {info[2] if len(info)>2 else ''}

Spiega se la scarpa è real o fake e il perché."""

    messages.append({"role": "user", "content": prompt})
    risposta = chiama_llm(messages)

    return jsonify(risposta)
