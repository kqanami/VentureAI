# core/utils/business_advice.py
import openai
import os
from django.conf import settings

def get_business_advice(prompt):
    openai.api_key = settings.OPENAI_API_KEY
    messages = [
        {"role": "system", "content": "Ты опытный бизнес-консультант."},
        {"role": "user", "content": prompt}
    ]
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages,
        max_tokens=150,
        temperature=0.7,
    )
    return response.choices[0].message['content'].strip()
