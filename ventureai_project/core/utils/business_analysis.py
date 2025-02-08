# core/utils/business_analysis.py
import openai
import os
from django.conf import settings

def analyze_business_pros_cons(project):
    openai.api_key = settings.OPENAI_API_KEY
    messages = [
        {"role": "system", "content": "Ты опытный бизнес-консультант."},
        {"role": "user", "content": f"Проанализируй бизнес-проект и определи его плюсы и минусы. Описание проекта: {project.description}"}
    ]
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages,
        max_tokens=150,
        temperature=0.7,
    )
    return response.choices[0].message['content'].strip()
