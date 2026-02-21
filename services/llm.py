import os
from groq import Groq
from utils.prompts import SYSTEM_PROMPT

def get_groq_client():
    return Groq(api_key=os.getenv("GROQ_API_KEY"))

def generate_farm_advice(messages_history: list, weather_context: str = "", disease_context: str = "") -> str:
    client = get_groq_client()
    
    # 1. Start with the system prompt
    api_messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    
    # 2. Append the entire conversation memory
    for msg in messages_history:
        api_messages.append({"role": msg["role"], "content": msg["content"]})
        
    # 3. Inject context into the very last message if needed (for weather/vision)
    if weather_context or disease_context:
        last_msg = api_messages[-1]["content"]
        context_str = ""
        if weather_context:
            context_str += f"[System Note - Current Weather: {weather_context}]\n"
        if disease_context:
            context_str += f"[System Note - Detected Disease: {disease_context}]\n"
        api_messages[-1]["content"] = context_str + last_msg

    try:
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant", 
            messages=api_messages,
            temperature=0.3, 
            max_tokens=300
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"Error communicating with AI: {str(e)}"