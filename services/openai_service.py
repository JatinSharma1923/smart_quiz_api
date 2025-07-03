
import openai
import os

openai.api_key = os.getenv("OPENAI_API_KEY")

def generate_quiz(topic, question_type="mcq", difficulty="medium"):
    prompt = f"Create 5 {question_type} questions on {topic} with options, answer, and explanation."
    response = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content
