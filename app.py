import streamlit as st
import os
from streamlit_geolocation import streamlit_geolocation

# Import services
from services.llm import generate_farm_advice
from services.translation import translate_text
from services.weather import get_weather_by_coords
from services.vision import analyze_crop_image
from services.speech import audio_to_text, text_to_audio

st.set_page_config(page_title="Mkulima AI", page_icon="🌾", layout="centered")

LANG_MAP = {"English": "eng_Latn", "Swahili": "swa_Latn", "Kikuyu": "kik_Latn"}

def main():
    # --- INITIALIZE SESSION STATE ---
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": "Habari! Ask a question, or attach a photo or voice note below."}]
    
    if "processed_files" not in st.session_state:
        st.session_state.processed_files = set()

    # Memory for the weather so we don't spam the API
    if "weather_context" not in st.session_state:
        st.session_state.weather_context = ""
        
    if "last_coords" not in st.session_state:
        st.session_state.last_coords = None

    # --- SIDEBAR ---
    with st.sidebar:
        st.title("🌾 Mkulima AI")
        st.caption("Settings & Context")
        
        selected_lang = st.selectbox("Language / Lugha", ["English", "Swahili", "Kikuyu"], index=0)
        target_lang_code = LANG_MAP[selected_lang]
        
        st.markdown("---")
        st.markdown("### 📍 Auto-Detect Location")
        st.caption("Get hyper-local weather for better advice:")
        
        # The GPS Location Button
        location = streamlit_geolocation()
        
        if location and location.get('latitude') and location.get('longitude'):
            coords = (location['latitude'], location['longitude'])
            # Only fetch weather if coordinates changed
            if st.session_state.last_coords != coords:
                with st.spinner("Fetching local weather..."):
                    weather_data = get_weather_by_coords(coords[0], coords[1])
                    st.session_state.weather_context = weather_data
                    st.session_state.last_coords = coords
        
        # Display current weather if available
        if st.session_state.weather_context:
            st.success(f"**Current Weather:**\n{st.session_state.weather_context}")
        
        st.markdown("---")
        if st.button("🗑️ Clear Chat History"):
            st.session_state.messages = []
            st.session_state.processed_files = set()
            st.session_state.weather_context = ""
            st.session_state.last_coords = None
            st.rerun()

    # --- RENDER CHAT HISTORY ---
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            if msg.get("image"):
                st.image(msg["image"], use_container_width=True)
            st.markdown(msg["content"])
            if msg.get("audio"):
                st.audio(msg["audio"], format="audio/mp3")

    # --- MEDIA INPUTS ---
    st.write("") # Spacer
    with st.expander("📎 Attach Leaf Photo or Voice Note", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            uploaded_file = st.file_uploader("📸 Upload Leaf", type=["jpg", "jpeg", "png"], label_visibility="collapsed")
        with col2:
            audio_bytes = st.audio_input("🎙️ Record Voice", label_visibility="collapsed")

    # --- HANDLE NEW INPUTS ---
    # Grab the active weather to pass to the LLM
    active_weather = st.session_state.weather_context
    
    # 1. Image Upload Logic
    if uploaded_file and uploaded_file.file_id not in st.session_state.processed_files:
        st.session_state.processed_files.add(uploaded_file.file_id)
        image_bytes = uploaded_file.getvalue()
        
        st.session_state.messages.append({"role": "user", "content": "Please diagnose this crop.", "image": image_bytes})
        with st.chat_message("user"):
            st.image(image_bytes, use_container_width=True)
            st.markdown("Please diagnose this crop.")
            
        with st.chat_message("assistant"):
            with st.spinner("Scanning image..."):
                detected_disease = analyze_crop_image(image_bytes)
                st.error(f"**Detected:** {detected_disease}")
                
                # We pass the weather into the advice generator!
                eng_advice = generate_farm_advice(st.session_state.messages, weather_context=active_weather, disease_context=detected_disease)
                final_advice = translate_text(eng_advice, "eng_Latn", target_lang_code)
                st.markdown(final_advice)
                
        st.session_state.messages.append({"role": "assistant", "content": f"**Detected:** {detected_disease}\n\n{final_advice}"})
        st.rerun()

    # 2. Voice Input Logic
    if audio_bytes and audio_bytes.file_id not in st.session_state.processed_files:
        st.session_state.processed_files.add(audio_bytes.file_id)
        
        temp_audio_path = "temp_mic.wav"
        with open(temp_audio_path, "wb") as f:
            f.write(audio_bytes.getbuffer())
            
        with st.chat_message("user"):
            with st.spinner("Transcribing..."):
                transcribed_text = audio_to_text(temp_audio_path)
            st.markdown(f"🎙️ *{transcribed_text}*")
            
        st.session_state.messages.append({"role": "user", "content": transcribed_text})
        
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                eng_text = translate_text(transcribed_text, target_lang_code, "eng_Latn")
                
                # Passing weather context
                eng_response = generate_farm_advice(st.session_state.messages, weather_context=active_weather)
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

    # 3. Text Chat Logic
    if prompt := st.chat_input("Message Mkulima AI..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                eng_input = translate_text(prompt, target_lang_code, "eng_Latn")
                
                # Passing weather context
                eng_response = generate_farm_advice(st.session_state.messages, weather_context=active_weather)
                final_response = translate_text(eng_response, "eng_Latn", target_lang_code)
                st.markdown(final_response)
        
        st.session_state.messages.append({"role": "assistant", "content": final_response})
        st.rerun()

if __name__ == "__main__":
    main()