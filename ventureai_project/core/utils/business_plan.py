from django.conf import settings
import openai
import os

def generate_business_plan(project):
    openai.api_key = settings.OPENAI_API_KEY
    messages = [
        {"role": "system", "content": "Ты эксперт по составлению бизнес-планов."},
        {"role": "user", "content": f"Создай детальный бизнес-план для проекта: {project.description}. Укажи цели, стратегию, финансовые расчёты и план развития."}
    ]
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages,
        max_tokens=300,
        temperature=0.7,
    )
    return response.choices[0].message['content'].strip()