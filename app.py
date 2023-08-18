from flask import Flask, jsonify, request
import openai
app = Flask(__name__)
openai.api_key = "YOUR-API-KEY"
@app.route("/generate", methods=["POST"])
def generate():
    data = request.json
    user_input = data.get("prompt", "")
    response = generate_response(user_input)
    return jsonify({"response": response})
def generate_response(prompt, max_tokens=1000):
    response = openai.Completion.create(
        engine="text-davinci-003", prompt=prompt, max_tokens=max_tokens
    )
    return response.choices[0].text.strip()
if __name__ == "__main__":
    app.run(debug=True)
