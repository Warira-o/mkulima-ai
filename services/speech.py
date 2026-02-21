import os
from groq import Groq
from gtts import gTTS

def audio_to_text(audio_file_path: str) -> str:
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