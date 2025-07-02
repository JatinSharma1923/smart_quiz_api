import openai, os
openai.api_key = os.getenv('OPENAI_API_KEY')

def generate_quiz(topic):
    prompt = f'Generate MCQs on {topic}'
    return 'Sample quiz questions'
