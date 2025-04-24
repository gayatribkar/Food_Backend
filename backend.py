import os, base64, json
import requests
from flask import Flask, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
import re
from uuid import uuid4
from dotenv import load_dotenv

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
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

# Global conversation history (for demonstration purposes)
conversation_history = []

def validate_nutrition(data):
    required = {"foodName", "calories", "protein", "fat", "carbs"}
    if not data or not all(key in data for key in required):
        return None

    try:
        return {
            "foodName": str(data["foodName"]),
            "calories": float(data["calories"]),
            "protein": float(data["protein"]),
            "fat": float(data["fat"]),
            "carbs": float(data["carbs"])
        }
    except (ValueError, TypeError):
        return None

def extract_nutrition_data(content):
    code_match = re.search(r'json\n(.*?)\n', content, re.DOTALL)
    # code_match = re.search(r'```json\n(.*?)\n```', content, re.DOTALL)
    if code_match:
        try:
            return json.loads(code_match.group(1))
        except json.JSONDecodeError:
            pass

    json_match = re.search(r'{\s*"foodName".*?}', content, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass

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
            b64_image = base64.b64encode(img_f.read()).decode("utf-8")

        response = requests.post(
            OPENAI_API_URL,
            headers={"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"},
            json={
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
            },
            timeout=30
        )
        response.raise_for_status()

        content = response.json()["choices"][0]["message"]["content"]
        raw_nutrition = extract_nutrition_data(content)
        nutrition_data = validate_nutrition(raw_nutrition)

        # message = re.sub(r'json.*?', '', content, flags=re.DOTALL).strip()
        message = re.sub(r'```json.*?```', '', content, flags=re.DOTALL).strip()

        message = re.sub(r'\*\*', '', message)

        conversation_history.clear()
        conversation_history.extend([
            {"role": "user", "content": "Analyze this food image"},
            {"role": "assistant", "content": content}
        ])

        return jsonify({
            "message": message or "Nutrition analysis complete",
            "nutrition": nutrition_data or {
                "foodName": "Unknown Food",
                "calories": 0,
                "protein": 0,
                "fat": 0,
                "carbs": 0
            },
            "imageUrl": f"{request.host_url}uploads/{filename}"
        })

    except requests.exceptions.RequestException as e:
        return jsonify({"error": "Service unavailable"}), 503
    except Exception as e:
        return jsonify({"error": "Processing failed"}), 500

@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json()
        user_msg = data.get("message", "")
        if not user_msg:
            return jsonify({"error": "No message provided"}), 400

        conversation_history.append({"role": "user", "content": user_msg})

        messages = [
            {"role": "system", "content": "You are a nutrition assistant. Use the previous analysis to answer questions."},
            *conversation_history
        ]

        response = requests.post(
            OPENAI_API_URL,
            headers={"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"},
            json={
                "model": OPENAI_MODEL,
                "messages": messages,
                "temperature": 0.3
            }
        )
        response.raise_for_status()

        assistant_response = response.json()["choices"][0]["message"]["content"].strip()
        conversation_history.append({"role": "assistant", "content": assistant_response})

        raw_nutrition = extract_nutrition_data(assistant_response)
        nutrition_data = validate_nutrition(raw_nutrition)

        message = re.sub(r'json.*?', '', assistant_response, flags=re.DOTALL).strip()
        message = re.sub(r'\*\*', '', message)

        return jsonify({
            "message": message,
            "nutrition": nutrition_data
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/uploads/<filename>")
def serve_image(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
