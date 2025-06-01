# Assicurati che questi import siano presenti all'inizio del tuo file app.py
# Probabilmente hai già Flask, render_template, request. Aggiungiamo jsonify.
from flask import Flask, render_template, request, jsonify
import requests # Importa la libreria requests per fare chiamate HTTP
import os       # Utile se usi variabili d'ambiente per la API key

# Probabilmente hai già l'inizializzazione di Flask:
# app = Flask(__name__)

# --------------- FUNZIONE chiama_llm AGGIORNATA ---------------
def chiama_llm(messages):
    """
    Invia i messaggi a un LLM e restituisce il contenuto della sua risposta.
    Include logging e gestione degli errori migliorata.
    """
    # === INIZIO SEZIONE DA PERSONALIZZARE ===
    # Sostituisci con l'URL effettivo dell'API del tuo LLM
    URL_LLM = "URL_DELLA_TUA_API_LLM"
    API_KEY = os.environ.get("LLM_API_KEY") # Esempio: prendi la API key dalle variabili d'ambiente

    if not API_KEY:
        print("Errore: LLM_API_KEY non trovata nelle variabili d'ambiente.")
        return {"error": "Configurazione API LLM mancante.", "status_code": 500}

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    # Questo è un esempio di payload. Adattalo alla struttura richiesta dal tuo LLM.
    # 'messages' è l'argomento passato a questa funzione.
    payload = {
        "model": "nome-del-tuo-modello", # Es. "gpt-3.5-turbo"
        "messages": messages
        # Aggiungi altri parametri richiesti dall'API (temperature, max_tokens, ecc.)
    }
    # === FINE SEZIONE DA PERSONALIZZARE ===

    print(f"Invio richiesta a LLM: {URL_LLM} con payload: {payload}")

    try:
        # Imposta un timeout per la richiesta (es. 30 secondi)
        response = requests.post(URL_LLM, headers=headers, json=payload, timeout=30)

        # Logga lo status code ricevuto
        print(f"Status Code dalla chiamata LLM: {response.status_code}")

        # Prova a decodificare la risposta JSON
        try:
            response_data = response.json()
            print(f"Risposta JSON grezza dall'LLM: {response_data}")
        except requests.exceptions.JSONDecodeError:
            # Se non è JSON, logga il testo grezzo (potrebbe essere un errore HTML o altro)
            print(f"Errore nel decodificare il JSON. Risposta testuale dall'LLM: {response.text}")
            return {"error": "Risposta non JSON dall'LLM.", "status_code": response.status_code, "details": response.text}

        # Controlla se la richiesta HTTP ha avuto successo (codici 2xx)
        if response.ok: # response.ok è True per status codes < 400
            # Accesso sicuro ai dati, verificando ogni livello
            choices = response_data.get("choices")
            if choices and isinstance(choices, list) and len(choices) > 0:
                message = choices[0].get("message")
                if message and isinstance(message, dict):
                    content = message.get("content")
                    if content:
                        return {"content": content, "status_code": response.status_code} # Restituisce il contenuto con successo
                    else:
                        print("Errore: Chiave 'content' mancante nel messaggio della risposta LLM.")
                        return {"error": "Chiave 'content' mancante nella risposta LLM.", "details": response_data, "status_code": 500}
                else:
                    print("Errore: Chiave 'message' mancante o non valida nel primo 'choice' della risposta LLM.")
                    return {"error": "Chiave 'message' mancante o non valida nella risposta LLM.", "details": response_data, "status_code": 500}
            else:
                print("Errore: Chiave 'choices' mancante, non è una lista, o è vuota nella risposta LLM.")
                # Controlla se c'è una struttura di errore nota nell'API
                if response_data.get("error"):
                    print(f"L'API LLM ha restituito un errore specifico: {response_data.get('error')}")
                    return {"error": f"Errore dall'API LLM: {response_data.get('error').get('message', str(response_data.get('error')))}", "details": response_data, "status_code": response.status_code}
                return {"error": "Struttura 'choices' non valida o mancante nella risposta LLM.", "details": response_data, "status_code": 500}
        else:
            # La richiesta HTTP non ha avuto successo (es. 400, 401, 403, 500, 503)
            print(f"Errore HTTP dalla chiamata LLM: {response.status_code}. Risposta: {response_data}")
            error_message = response_data.get("error", {}).get("message", "Errore sconosciuto dall'API LLM.")
            if isinstance(response_data.get("error"), str): # Alcune API restituiscono l'errore come stringa
                 error_message = response_data.get("error")
            return {"error": error_message, "details": response_data, "status_code": response.status_code}

    except requests.exceptions.RequestException as e:
        # Gestisce errori di rete, timeout, ecc.
        print(f"Eccezione durante la chiamata all'LLM: {e}")
        return {"error": f"Errore di connessione all'LLM: {str(e)}", "status_code": 503} # 503 Service Unavailable

# --------------- FUNZIONE chat AGGIORNATA ---------------
# Questa è la route Flask che gestisce la richiesta /chat.
# Assumendo che sia definita in modo simile a questo:
# @app.route('/chat', methods=['POST'])
def chat(): # Dovresti avere una definizione di route sopra questa funzione, es. @app.route('/chat', methods=['POST'])
    try:
        user_input = request.json.get("message") # Assumendo che il messaggio dell'utente arrivi come JSON
        if not user_input:
            return jsonify({"error": "Messaggio mancante nella richiesta."}), 400

        # Prepara i messaggi per l'LLM. Adatta questa struttura se necessario.
        # Potresti avere una cronologia della chat da gestire qui.
        messages_for_llm = [
            {"role": "user", "content": user_input}
        ]

        print(f"Input utente per /chat: {user_input}")
        print(f"Messaggi inviati a chiama_llm: {messages_for_llm}")

        # Chiama la funzione aggiornata
        risposta_llm = chiama_llm(messages_for_llm)

        print(f"Risultato da chiama_llm: {risposta_llm}")

        # Controlla se la chiamata all'LLM ha avuto successo
        if risposta_llm and "content" in risposta_llm:
            # Tutto ok, restituisci il contenuto
            return jsonify({"reply": risposta_llm["content"]})
        else:
            # C'è stato un errore, restituisci il messaggio di errore e lo status code appropriato
            error_message = risposta_llm.get("error", "Errore sconosciuto nella generazione della risposta.")
            status_code = risposta_llm.get("status_code", 500)
            # Potresti voler loggare anche i dettagli dell'errore se presenti
            # print(f"Dettagli errore LLM (da chat): {risposta_llm.get('details')}")
            return jsonify({"error": error_message}), status_code

    except Exception as e:
        # Errore generico nella funzione chat
        print(f"Eccezione non gestita in /chat: {e}")
        import traceback
        traceback.print_exc() # Stampa il traceback completo nei log del server
        return jsonify({"error": "Si è verificato un errore interno al server."}), 500

# --------------- ASSICURATI CHE LA TUA APP FLASK SIA CONFIGURATA E AVVIATA ---------------
# Esempio di come potrebbe essere il resto del tuo app.py (molto semplificato):
#
# app = Flask(__name__)
#
# @app.route('/')
# def index():
#     return render_template('index.html') # Assumendo che tu abbia un index.html
#
# # Qui inserisci le funzioni chiama_llm e chat definite sopra
# # ...
# # def chiama_llm(messages):
# #     ...
#
# @app.route('/chat', methods=['POST']) # La route per la funzione chat
# def chat_route(): # Rinominata per evitare conflitto con la funzione chat stessa
#     return chat()
#
# if __name__ == '__main__':
#     app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
#
# Ricorda di adattare la parte di avvio dell'app se usi Gunicorn o un altro WSGI server su Render.
# Il tuo render.yaml probabilmente gestisce già il comando di avvio.
