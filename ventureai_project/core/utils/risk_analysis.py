# core/utils/risk_analysis.py
import openai
import os
from django.conf import settings

def analyze_risks(project):
    openai.api_key = settings.OPENAI_API_KEY
    messages = [
        {"role": "system", "content": "Ты эксперт по управлению рисками в бизнесе."},
        {"role": "user", "content": f"Оцени риски для бизнес-проекта с описанием: {project.description}"}
    ]
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages,
        max_tokens=150,
        temperature=0.7,
    )
    return response.choices[0].message['content'].strip()
