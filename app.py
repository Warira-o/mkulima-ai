import streamlit as st
import os
import pandas as pd
from dotenv import load_dotenv
from streamlit_geolocation import streamlit_geolocation

# 1. FIX: Load environment variables safely
load_dotenv()

# Import services
from services.llm import generate_farm_advice
from services.translation import translate_text
from services.vision import analyze_crop_image
from services.speech import audio_to_text, text_to_audio
from services.weather import get_weather_by_coords
# 2. FIX: Import the new carbon module
from services.carbon import calculate_baseline_carbon

st.set_page_config(page_title="Carbon & Data AI", page_icon="🌍", layout="wide")

LANG_MAP = {"English": "eng_Latn", "Swahili": "swa_Latn", "Kikuyu": "kik_Latn"}

def main():
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": "Welcome to Carbon & Data. How can I assist with your agricultural mapping or carbon auditing today?"}]
    if "processed_files" not in st.session_state:
        st.session_state.processed_files = set()
    if "weather_context" not in st.session_state:
        st.session_state.weather_context = ""
    if "active_coords" not in st.session_state:
        st.session_state.active_coords = None

    # --- SIDEBAR: CONTEXT & TOOLS ---
    with st.sidebar:
        st.title("🌍 Carbon & Data")
        
        selected_lang = st.selectbox("Language / Lugha", ["English", "Swahili", "Kikuyu"], index=0)
        target_lang_code = LANG_MAP[selected_lang]
        
        st.markdown("---")
        st.markdown("### 📍 Farm Mapping")
        location = streamlit_geolocation()
        
        # 3. FIX: Properly handling and plotting the GPS Map
        if location and location.get('latitude') and location.get('longitude'):
            coords = (location['latitude'], location['longitude'])
            st.session_state.active_coords = coords
            
            with st.spinner("Fetching map & weather..."):
                st.session_state.weather_context = get_weather_by_coords(coords[0], coords[1])
        
        if st.session_state.active_coords:
            lat, lon = st.session_state.active_coords
            st.success(f"**Mapped:** {lat:.4f}, {lon:.4f}")
            # Plot coordinates natively in Streamlit
            df = pd.DataFrame({'lat': [lat], 'lon': [lon]})
            st.map(df, zoom=14, use_container_width=True)

        st.markdown("---")
        st.markdown("### 📊 Carbon Audit Tool")
        farm_size = st.number_input("Farm Size (Acres)", min_value=1.0, value=5.0)
        practice = st.selectbox("Primary Practice", ["Conventional", "No-Till", "Agroforestry", "Cover Cropping", "Regenerative"])
        
        if st.button("Generate Baseline Audit"):
            # Using the new dedicated carbon service
            audit_results = calculate_baseline_carbon(farm_size, practice)
            tco2e = audit_results['estimated_tCO2e']
            
            st.info(f"**Est. Sequestration:** {tco2e} tCO2e/year")
            
            # Inject context silently
            audit_msg = f"[System Alert: User generated an audit. Size: {farm_size} acres. Practice: {practice}. Sequestration: {tco2e} tCO2e/yr.]"
            st.session_state.messages.append({"role": "user", "content": audit_msg})

        st.markdown("---")
        if st.button("🗑️ Clear Dashboard"):
            st.session_state.messages = []
            st.session_state.active_coords = None
            st.session_state.weather_context = ""
            st.rerun()

    # --- MAIN CHAT INTERFACE ---
    for msg in st.session_state.messages:
        if msg["content"].startswith("[System Alert"):
            continue
        with st.chat_message(msg["role"]):
            if msg.get("image"):
                st.image(msg["image"], use_container_width=True)
            st.markdown(msg["content"])
            if msg.get("audio"):
                st.audio(msg["audio"], format="audio/mp3")

    # --- MEDIA INPUTS ---
    with st.expander("📎 Upload Imagery or Voice", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            uploaded_file = st.file_uploader("🛰️ Upload Spatial Data", type=["jpg", "jpeg", "png"], label_visibility="collapsed")
        with col2:
            audio_bytes = st.audio_input("🎙️ Record Voice", label_visibility="collapsed")

    active_weather = st.session_state.weather_context

    # Image Logic
    if uploaded_file and uploaded_file.file_id not in st.session_state.processed_files:
        st.session_state.processed_files.add(uploaded_file.file_id)
        image_bytes = uploaded_file.getvalue()
        
        st.session_state.messages.append({"role": "user", "content": "Analyze this image.", "image": image_bytes})
        with st.chat_message("user"):
            st.image(image_bytes, use_container_width=True)
            st.markdown("Analyze this image.")
            
        with st.chat_message("assistant"):
            with st.spinner("Processing spatial imagery..."):
                analysis = analyze_crop_image(image_bytes)
                st.session_state.messages.append({"role": "user", "content": f"[System: Vision detected {analysis}] Give me a breakdown of what this means."})
                
                response = generate_farm_advice(st.session_state.messages, weather_context=active_weather)
                final_response = translate_text(response, "eng_Latn", target_lang_code)
                st.markdown(final_response)
                
        st.session_state.messages.append({"role": "assistant", "content": final_response})
        st.rerun()

    # Voice Logic (4. FIX: The Voice Translation Bug)
    if audio_bytes and audio_bytes.file_id not in st.session_state.processed_files:
        st.session_state.processed_files.add(audio_bytes.file_id)
        
        temp_audio_path = "temp_mic.wav"
        with open(temp_audio_path, "wb") as f:
            f.write(audio_bytes.getbuffer())
            
        with st.chat_message("user"):
            with st.spinner("Transcribing..."):
                transcribed_text = audio_to_text(temp_audio_path, target_lang_code)
            st.markdown(f"🎙️ *{transcribed_text}*")
            
        # Display the native language in UI
        st.session_state.messages.append({"role": "user", "content": transcribed_text})
        
        with st.chat_message("assistant"):
            with st.spinner("Analyzing..."):
                # Translate to English BEFORE sending to LLM context
                eng_text = translate_text(transcribed_text, target_lang_code, "eng_Latn")
                
                # Create a temporary translated history for the LLM
                temp_history = st.session_state.messages.copy()
                temp_history[-1] = {"role": "user", "content": eng_text}
                
                # Pass the translated history and weather to the LLM
                eng_response = generate_farm_advice(temp_history, weather_context=active_weather)
                
                # Translate response back to user's language
                final_response = translate_text(eng_response, "eng_Latn", target_lang_code)
                st.markdown(final_response)
                
                output_audio_path = text_to_audio(final_response, target_lang_code)
                if output_audio_path:
                    st.audio(output_audio_path, format="audio/mp3", autoplay=True)
                    st.session_state.messages.append({"role": "assistant", "content": final_response, "audio": output_audio_path})
                else:
                    st.session_state.messages.append({"role": "assistant", "content": final_response})
                    
        if os.path.exists(temp_audio_path):
            os.remove(temp_audio_path)
        st.rerun()

    # Text Chat Logic
    if prompt := st.chat_input("Ask about carbon markets, soil health..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Analyzing..."):
                eng_input = translate_text(prompt, target_lang_code, "eng_Latn")
                
                temp_history = st.session_state.messages.copy()
                temp_history[-1] = {"role": "user", "content": eng_input}
                
                eng_response = generate_farm_advice(temp_history, weather_context=active_weather)
                final_response = translate_text(eng_response, "eng_Latn", target_lang_code)
                st.markdown(final_response)
        
        st.session_state.messages.append({"role": "assistant", "content": final_response})
        st.rerun()

if __name__ == "__main__":
    main()