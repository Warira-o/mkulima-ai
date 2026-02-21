import os
import base64
from groq import Groq

def analyze_crop_image(image_bytes: bytes) -> str:
    """Analyzes an image to detect crop diseases using Groq's Llama 3.2 Vision."""
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    
    # Encode the image bytes into a base64 string
    base64_image = base64.b64encode(image_bytes).decode('utf-8')
    
    # Prompt the multimodal AI
    prompt = "You are an expert agricultural AI. Examine this image of a crop leaf. Reply ONLY with the name of the disease or pest detected (e.g., 'Maize Streak Virus', 'Healthy', 'Aphids'). Keep your answer to 1-4 words maximum."
    
    try:
        completion = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            temperature=0.1, # Low temperature so it doesn't hallucinate
            max_tokens=20
        )
        return completion.choices[0].message.content.strip()
    except Exception as e:
        # Return the EXACT error to the Streamlit UI so we can read it
        return f"CRASH LOG: {str(e)}"