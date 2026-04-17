import streamlit as st
import os
import pandas as pd
from dotenv import load_dotenv
from streamlit_geolocation import streamlit_geolocation

# Load environment variables safely
load_dotenv()

# Import services
from services.llm import generate_farm_advice
from services.translation import translate_text
from services.vision import analyze_crop_image
from services.speech import audio_to_text, text_to_audio
from services.weather import get_weather_by_coords
from services.carbon import calculate_baseline_carbon

# Page config must be the very first Streamlit command
st.set_page_config(page_title="Carbon & Data AI", page_icon="🌍", layout="wide")

LANG_MAP = {"English": "eng_Latn", "Swahili": "swa_Latn", "Kikuyu": "kik_Latn"}

# --- 1. INITIALIZE SHARED MEMORY ---
# This ensures data survives when the user clicks between pages
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Welcome to Carbon & Data. How can I help you today?"}]
if "processed_files" not in st.session_state:
    st.session_state.processed_files = set()
if "weather_context" not in st.session_state:
    st.session_state.weather_context = ""
if "active_coords" not in st.session_state:
    st.session_state.active_coords = None

# --- 2. GLOBAL SIDEBAR SETTINGS ---
with st.sidebar:
    st.title("🌍 Carbon & Data")
    selected_lang = st.selectbox("Language / Lugha", ["English", "Swahili", "Kikuyu"], index=0)
    target_lang_code = LANG_MAP[selected_lang]
    
    st.markdown("---")
    if st.button("🗑️ Clear Dashboard Data"):
        st.session_state.messages = [{"role": "assistant", "content": "Welcome to Carbon & Data. How can I help you today?"}]
        st.session_state.active_coords = None
        st.session_state.weather_context = ""
        st.session_state.processed_files = set()
        st.rerun()

# --- 3. PAGE DEFINITIONS ---

def chat_page():
    """Page 1: Text and Voice Chatbot"""
    st.title("💬 AI Assistant")
    
    # Render History
    for msg in st.session_state.messages:
        if msg["content"].startswith("[System Alert"):
            continue
        with st.chat_message(msg["role"]):
            if msg.get("image"):
                st.image(msg["image"], use_container_width=True)
            st.markdown(msg["content"])
            if msg.get("audio"):
                st.audio(msg["audio"], format="audio/mp3")

    # Voice Input
    audio_bytes = st.audio_input("🎙️ Record Voice Question")
    if audio_bytes and audio_bytes.file_id not in st.session_state.processed_files:
        st.session_state.processed_files.add(audio_bytes.file_id)
        temp_audio_path = "temp_mic.wav"
        with open(temp_audio_path, "wb") as f:
            f.write(audio_bytes.getbuffer())
            
        with st.chat_message("user"):
            with st.spinner("Transcribing..."):
                transcribed_text = audio_to_text(temp_audio_path, target_lang_code)
            st.markdown(f"🎙️ *{transcribed_text}*")
            
        st.session_state.messages.append({"role": "user", "content": transcribed_text})
        
        with st.chat_message("assistant"):
            with st.spinner("Analyzing..."):
                eng_text = translate_text(transcribed_text, target_lang_code, "eng_Latn")
                temp_history = st.session_state.messages.copy()
                temp_history[-1] = {"role": "user", "content": eng_text}
                
                eng_response = generate_farm_advice(temp_history, weather_context=st.session_state.weather_context)
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

    # Text Input
    if prompt := st.chat_input("Ask about carbon markets, soil health..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Analyzing..."):
                eng_input = translate_text(prompt, target_lang_code, "eng_Latn")
                temp_history = st.session_state.messages.copy()
                temp_history[-1] = {"role": "user", "content": eng_input}
                
                eng_response = generate_farm_advice(temp_history, weather_context=st.session_state.weather_context)
                final_response = translate_text(eng_response, "eng_Latn", target_lang_code)
                st.markdown(final_response)
        
        st.session_state.messages.append({"role": "assistant", "content": final_response})
        st.rerun()

def audit_page():
    """Page 2: GPS Mapping and Carbon Calculator"""
    st.title("🌍 Farm Map & Carbon Audit")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📍 Location Tracker")
        location = streamlit_geolocation()
        
        if location and location.get('latitude') and location.get('longitude'):
            coords = (location['latitude'], location['longitude'])
            st.session_state.active_coords = coords
            with st.spinner("Fetching map & weather..."):
                st.session_state.weather_context = get_weather_by_coords(coords[0], coords[1])
                
        if st.session_state.active_coords:
            lat, lon = st.session_state.active_coords
            st.success(f"**Mapped:** {lat:.4f}, {lon:.4f}")
            df = pd.DataFrame({'lat': [lat], 'lon': [lon]})
            st.map(df, zoom=14, use_container_width=True)
            
        if st.session_state.weather_context:
            st.info(f"**Local Weather:** {st.session_state.weather_context}")

    with col2:
        st.markdown("### 📊 Carbon Audit Tool")
        farm_size = st.number_input("Farm Size (Acres)", min_value=1.0, value=5.0)
        practice = st.selectbox("Primary Practice", ["Conventional", "No-Till", "Agroforestry", "Cover Cropping", "Regenerative"])
        
        if st.button("Generate Baseline Audit"):
            audit_results = calculate_baseline_carbon(farm_size, practice)
            tco2e = audit_results['estimated_tCO2e']
            st.success(f"**Est. Sequestration:** {tco2e} tCO2e/year")
            
            audit_msg = f"[System Alert: User generated an audit. Size: {farm_size} acres. Practice: {practice}. Sequestration: {tco2e} tCO2e/yr.]"
            st.session_state.messages.append({"role": "user", "content": audit_msg})
            st.caption("Audit saved to AI memory. You can now ask the Assistant about these results.")

def vision_page():
    """Page 3: Satellite and Drone Imagery"""
    st.title("🛰️ Spatial Imagery Analysis")
    st.write("Upload drone or satellite imagery for AI assessment.")
    
    uploaded_file = st.file_uploader("Upload Image (JPEG/PNG)", type=["jpg", "jpeg", "png"])
    
    if uploaded_file and uploaded_file.file_id not in st.session_state.processed_files:
        st.session_state.processed_files.add(uploaded_file.file_id)
        image_bytes = uploaded_file.getvalue()
        
        st.image(image_bytes, use_container_width=True)
        
        with st.spinner("Processing spatial imagery..."):
            analysis = analyze_crop_image(image_bytes)
            st.success("Analysis Complete!")
            st.info(f"**Raw AI Output:** {analysis}")
            
            st.session_state.messages.append({"role": "user", "content": "Analyze this image.", "image": image_bytes})
            st.session_state.messages.append({"role": "user", "content": f"[System: Vision detected {analysis}]"})
            st.caption("Image data sent to AI memory. Switch to the Chat Assistant to discuss the results.")

# --- 4. NAVIGATION ROUTER ---
# This bundles the functions into pages and creates the sidebar menu automatically
pg = st.navigation([
    st.Page(chat_page, title="AI Assistant", icon="💬"),
    st.Page(audit_page, title="Map & Audit", icon="🌍"),
    st.Page(vision_page, title="Spatial Vision", icon="🛰️")
])

# Run the app
pg.run()