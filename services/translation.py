import os
import requests

# Updated Hugging Face Router URL
HF_API_URL = "https://router.huggingface.co/hf-inference/models/facebook/nllb-200-distilled-600M"

def get_headers():
    return {"Authorization": f"Bearer {os.getenv('HF_API_KEY')}"}

def translate_text(text: str, source_lang: str, target_lang: str) -> str:
    if source_lang == target_lang:
        return text

    payload = {
        "inputs": text,
        "parameters": {
            "src_lang": source_lang,
            "tgt_lang": target_lang
        }
    }
    
    try:
        response = requests.post(HF_API_URL, headers=get_headers(), json=payload)
        if response.status_code == 200:
            return response.json()[0]['translation_text']
        else:
            print(f"Translation API Error: {response.status_code}")
            return text 
    except Exception as e:
        print(f"Translation Exception: {str(e)}")
        return text