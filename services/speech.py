import os
import requests
from groq import Groq
from gtts import gTTS

# The specialized Swahili model endpoint on Hugging Face
HF_SWAHILI_ASR_URL = "https://router.huggingface.co/hf-inference/models/thinkKenya/wav2vec2-large-xls-r-300m-sw"

def audio_to_text(audio_file_path: str, lang_code: str = 'eng_Latn') -> str:
    """Converts speech to text, routing Swahili to a specialized HF model."""
    
    # --- SWAHILI ROUTING ---
    if lang_code == 'swa_Latn':
        headers = {"Authorization": f"Bearer {os.getenv('HF_API_KEY')}"}
        try:
            with open(audio_file_path, "rb") as f:
                audio_data = f.read()
                
            response = requests.post(HF_SWAHILI_ASR_URL, headers=headers, data=audio_data)
            
            if response.status_code == 200:
                # The HF API returns a JSON dictionary with a "text" key
                return response.json().get("text", "")
            else:
                print(f"HF Swahili Model Error: {response.text}")
                # If the Swahili API is sleeping/offline, we let it fall through to Groq below
        except Exception as e:
            print(f"HF Speech Exception: {e}")

    # --- DEFAULT / FALLBACK (Groq Whisper) ---
    # Used for English, Kikuyu, or if the Hugging Face model is offline
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    try:
        with open(audio_file_path, "rb") as file:
            transcription = client.audio.transcriptions.create(
                file=(audio_file_path, file.read()),
                model="whisper-large-v3",
            )
        return transcription.text
    except Exception as e:
        return f"Speech recognition failed: {str(e)}"

def text_to_audio(text: str, lang_code: str = 'en', output_path: str = "response.mp3"):
    """Converts text to speech using gTTS."""
    gtts_lang = 'en'
    if lang_code == 'swa_Latn':
        gtts_lang = 'sw'
    elif lang_code == 'kik_Latn': 
        gtts_lang = 'sw' 
        
    try:
        tts = gTTS(text=text, lang=gtts_lang, slow=False)
        tts.save(output_path)
        return output_path
    except Exception as e:
        print(f"TTS Error: {str(e)}")
        return None