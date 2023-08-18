import openai

openai.api_key = "YOUR-API-KEY"


def generate_response(prompt):
    response = openai.Completion.create(
        engine="text-davinci-003", prompt=prompt, max_tokens=1000  # Adjust as needed
    )
    return response.choices[0].text.strip()
