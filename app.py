# import os, base64, json, logging
# import requests
# from flask import Flask, request, jsonify, send_from_directory
# from werkzeug.utils import secure_filename
# import re
# from uuid import uuid4
# from dotenv import load_dotenv

# # Setup logging
# logging.basicConfig(level=logging.INFO)

# app = Flask(__name__)
# # Configure upload folder from env or default
# UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "uploads")
# os.makedirs(UPLOAD_FOLDER, exist_ok=True)
# app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# # Load environment variables\load_dotenv()
# OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# if not OPENAI_API_KEY:
#     app.logger.error("OPENAI_API_KEY not set")
# OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"
# OPENAI_MODEL = "gpt-4o"

# SYSTEM_PROMPT = """You are a nutrition expert. Analyze food images and provide:
# 1. A friendly response starting with the food name
# 2. A JSON object with EXACT structure:
# {
#   "foodName": "identified food name",
#   "calories": number,
#   "protein": number,
#   "fat": number,
#   "carbs": number
# }

# Respond ONLY in this format:
# [Your text analysis here]

# json
# [The JSON object here]
# """

# # Global conversation history (demonstration only; use per-session storage in production)
# conversation_history = []

# def validate_nutrition(data):
#     required = {"foodName", "calories", "protein", "fat", "carbs"}
#     if not data or not all(key in data for key in required):
#         return None
#     try:
#         return {k: float(data[k]) if k != "foodName" else str(data[k]) for k in required}
#     except (ValueError, TypeError) as e:
#         app.logger.error(f"Nutrition data validation error: {e}")
#         return None

# def extract_nutrition_data(content):
#     # Look for ```json blocks first
#     match = re.search(r'```json\s*(\{.*?\})\s*```', content, re.DOTALL)
#     if not match:
#         match = re.search(r'json\s*(\{.*?\})', content, re.DOTALL)
#     if match:
#         try:
#             return json.loads(match.group(1))
#         except json.JSONDecodeError as e:
#             app.logger.error(f"JSON decode error: {e}")
#     return None

# @app.route("/analyze", methods=["POST"])
# def analyze_image():
#     if "image" not in request.files:
#         return jsonify({"error": "No image provided"}), 400
#     file = request.files["image"]
#     if file.filename == "":
#         return jsonify({"error": "Invalid file"}), 400
#     try:
#         filename = f"{uuid4().hex}_{secure_filename(file.filename)}"
#         file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
#         file.save(file_path)
#         with open(file_path, "rb") as img_f:
#             b64_image = base64.b64encode(img_f.read()).decode()
#         payload = {
#             "model": OPENAI_MODEL,
#             "messages": [
#                 {"role": "system", "content": SYSTEM_PROMPT},
#                 {"role": "user", "content": [
#                     {"type": "text", "text": "Analyze this food image"},
#                     {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64_image}"}}
#                 ]}
#             ],
#             "temperature": 0.2,
#             "max_tokens": 500
#         }
#         resp = requests.post(
#             OPENAI_API_URL,
#             headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
#             json=payload,
#             timeout=60
#         )
#         resp.raise_for_status()
#         content = resp.json()["choices"][0]["message"]["content"]
#         raw = extract_nutrition_data(content)
#         nutrition = validate_nutrition(raw) or {"foodName":"Unknown","calories":0,"protein":0,"fat":0,"carbs":0}
#         # Clean message for user
#         message = re.sub(r'```json.*?```','', content, flags=re.DOTALL).strip()
#         # Reset history
#         conversation_history.clear()
#         conversation_history.extend([
#             {"role":"user","content":"Analyze this food image"},
#             {"role":"assistant","content":content}
#         ])
#         return jsonify({"message":message,"nutrition":nutrition,"imageUrl":f"{request.host_url}uploads/{filename}"})
#     except Exception as e:
#         app.logger.exception("Analyze failed")
#         return jsonify({"error":"Processing failed"}), 500

# @app.route("/chat", methods=["POST"])
# def chat():
#     try:
#         data = request.get_json() or {}
#         user_msg = data.get("message")
#         if not user_msg:
#             return jsonify({"error":"No message provided"}), 400
#         conversation_history.append({"role":"user","content":user_msg})
#         messages = [{"role":"system","content":"You are a nutrition assistant. Use the previous analysis to answer questions."}] + conversation_history
#         resp = requests.post(
#             OPENAI_API_URL,
#             headers={"Authorization":f"Bearer {OPENAI_API_KEY}"},
#             json={"model":OPENAI_MODEL,"messages":messages,"temperature":0.3},
#             timeout=60
#         )
#         resp.raise_for_status()
#         ans = resp.json()["choices"][0]["message"]["content"].strip()
#         conversation_history.append({"role":"assistant","content":ans})
#         raw = extract_nutrition_data(ans)
#         nutrition = validate_nutrition(raw)
#         message = re.sub(r'```json.*?```','', ans, flags=re.DOTALL).strip()
#         return jsonify({"message":message,"nutrition":nutrition})
#     except Exception as e:
#         app.logger.exception("Chat failed")
#         return jsonify({"error":"Processing failed"}),500

# @app.route('/uploads/<filename>')
# def serve_image(filename):
#     return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# if __name__ == '__main__':
#     debug = os.getenv("FLASK_DEBUG","false").lower()=='true'
#     app.run(host='0.0.0.0',port=int(os.getenv('PORT',5000)),debug=debug)





import os, base64, json, logging
import requests
from flask import Flask, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
import re
from uuid import uuid4
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
# Configure upload folder from env or default
UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Load environment variables\load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    app.logger.error("OPENAI_API_KEY not set")
OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"
OPENAI_MODEL = "gpt-4o"

SYSTEM_PROMPT = """You are a nutrition expert. Analyze food images and provide:
1. A friendly response starting with the food name
2. A JSON object with EXACT structure:
{
  "foodName": "identified food name",
  "calories": number,
  "protein": number,
  "fat": number,
  "carbs": number
}

Respond ONLY in this format:
[Your text analysis here]

json
[The JSON object here]
"""

SYSTEM_PROMPT2 = """You are a nutrition expert. Analyze food images and provide:
1. A friendly response Following up the earlier messsages
2. A JSON object with EXACT structure:
{
  "foodName": "identified food name",
  "calories": number,
  "protein": number,
  "fat": number,
  "carbs": number
}

Respond ONLY in this format:
[Your text analysis here]

json
[The JSON object here]
"""

# Global conversation history (demonstration only; use per-session storage in production)
conversation_history = []

def validate_nutrition(data):
    allowed = {"foodName", "calories", "protein", "fat", "carbs"}
    if not data:
        return None
    try:
        validated = {}
        for key in allowed:
            if key in data:
                validated[key] = float(data[key]) if key != "foodName" else str(data[key])
        return validated if validated else None
    except (ValueError, TypeError) as e:
        app.logger.error(f"Nutrition data validation error: {e}")
        return None

def clean_message(content):

    content = re.sub(r'```(?:\w+)?\s*[\s\S]*?```', '', content)

    content = re.sub(r'^\s*json\s*$', '', content, flags=re.IGNORECASE | re.MULTILINE)
    return content.strip()


def extract_nutrition_data(content):
    match = re.search(r'```json\s*(\{.*?\})\s*```', content, re.DOTALL)
    if not match:
        match = re.search(r'json\s*(\{.*?\})', content, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError as e:
            app.logger.error(f"JSON decode error: {e}")
    return None

@app.route("/analyze", methods=["POST"])
def analyze_image():
    if "image" not in request.files:
        return jsonify({"error": "No image provided"}), 400
    file = request.files["image"]
    if file.filename == "":
        return jsonify({"error": "Invalid file"}), 400
    try:
        filename = f"{uuid4().hex}_{secure_filename(file.filename)}"
        file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(file_path)
        with open(file_path, "rb") as img_f:
            b64_image = base64.b64encode(img_f.read()).decode()
        payload = {
            "model": OPENAI_MODEL,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": [
                    {"type": "text", "text": "Analyze this food image"},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64_image}"}}
                ]}
            ],
            "temperature": 0.2,
            "max_tokens": 500
        }
        resp = requests.post(
            OPENAI_API_URL,
            headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
            json=payload,
            timeout=60
        )
        resp.raise_for_status()
        content = resp.json()["choices"][0]["message"]["content"]
        raw = extract_nutrition_data(content)
        nutrition = validate_nutrition(raw) or {"foodName":"Unknown","calories":0,"protein":0,"fat":0,"carbs":0}
        message = clean_message(content)     
        # Reset history
        conversation_history.clear()
        conversation_history.extend([
            {"role":"user","content":"Analyze this food image"},
            {"role":"assistant","content":content}
        ])
        return jsonify({"message":message,"nutrition":nutrition,"imageUrl":f"{request.host_url}uploads/{filename}"})
    except Exception as e:
        app.logger.exception("Analyze failed")
        return jsonify({"error":"Processing failed"}), 500

@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json() or {}
        user_msg = data.get("message")
        if not user_msg:
            return jsonify({"error":"No message provided"}), 400
        conversation_history.append({"role":"user","content":user_msg})
        messages = [{"role":"system","content": SYSTEM_PROMPT2}] + conversation_history
        resp = requests.post(
            OPENAI_API_URL,
            headers={"Authorization":f"Bearer {OPENAI_API_KEY}"},
            json={"model":OPENAI_MODEL,"messages":messages,"temperature":0.3},
            timeout=60
        )
        resp.raise_for_status()
        ans = resp.json()["choices"][0]["message"]["content"].strip()
        conversation_history.append({"role":"assistant","content":ans})
        raw = extract_nutrition_data(ans)
        nutrition = validate_nutrition(raw)
        message = clean_message(ans)

        return jsonify({"message":message,"nutrition":nutrition})
    except Exception as e:
        app.logger.exception("Chat failed")
        return jsonify({"error":"Processing failed"}),500

@app.route('/uploads/<filename>')
def serve_image(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    debug = os.getenv("FLASK_DEBUG","false").lower()=='true'
    app.run(host='0.0.0.0',port=int(os.getenv('PORT',5000)),debug=debug)
