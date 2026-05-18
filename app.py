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
from services.veterinary import (
    get_nearby_veterinarians, 
    format_vet_for_display, 
    get_emergency_hotline,
    get_emergency_care_tips
)
from services.carbon_markets import (
    calculate_potential_earnings,
    get_carbon_certification_requirements,
    get_certification_checklist
)
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
    
    # Save the selected language to session state so it works across all pages
    st.session_state.selected_lang = st.selectbox("Language / Lugha", ["English", "Swahili", "Kikuyu"], index=0)
    
    st.markdown("---")
    if st.button("🗑️ Clear Dashboard Data"):
        st.session_state.messages = [{"role": "assistant", "content": "Welcome to Carbon & Data. How can I help you today?"}]
        st.session_state.active_coords = None
        st.session_state.weather_context = ""
        st.session_state.processed_files = set()
        st.rerun()

# --- 3. PAGE DEFINITIONS ---

def chat_page():
    """Page 1: Text, Voice, and Image Chatbot"""
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

    # --- MEDIA INPUTS ---
    st.write("") # Small spacer
    with st.expander("📎 Attach Image or Voice Note", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            uploaded_file = st.file_uploader("📸 Upload Image", type=["jpg", "jpeg", "png"], label_visibility="collapsed")
        with col2:
            audio_bytes = st.audio_input("🎙️ Record Voice", label_visibility="collapsed")

    # --- 1. IMAGE UPLOAD LOGIC ---
    if uploaded_file and uploaded_file.file_id not in st.session_state.processed_files:
        st.session_state.processed_files.add(uploaded_file.file_id)
        image_bytes = uploaded_file.getvalue()
        
        st.session_state.messages.append({"role": "user", "content": "Analyze this image.", "image": image_bytes})
        with st.chat_message("user"):
            st.image(image_bytes, use_container_width=True)
            st.markdown("Analyze this image.")
            
        with st.chat_message("assistant"):
            with st.spinner("Processing image..."):
                analysis = analyze_crop_image(image_bytes)
                st.session_state.messages.append({"role": "user", "content": f"[System: Vision detected {analysis}] Give me a breakdown of what this means."})
                
                response = generate_farm_advice(st.session_state.messages, weather_context=st.session_state.weather_context)
                
                target_lang_code = LANG_MAP[st.session_state.get('selected_lang', 'English')]
                final_response = translate_text(response, "eng_Latn", target_lang_code)
                st.markdown(final_response)
                
        st.session_state.messages.append({"role": "assistant", "content": final_response})
        st.rerun()

    # --- 2. VOICE INPUT LOGIC ---
    if audio_bytes and audio_bytes.file_id not in st.session_state.processed_files:
        st.session_state.processed_files.add(audio_bytes.file_id)
        temp_audio_path = "temp_mic.wav"
        target_lang_code = LANG_MAP[st.session_state.get('selected_lang', 'English')]
        
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

    # --- 3. TEXT INPUT LOGIC ---
    if prompt := st.chat_input("Ask about carbon markets, soil health..."):
        target_lang_code = LANG_MAP[st.session_state.get('selected_lang', 'English')]
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
    """Page 2: GPS Mapping and Carbon Audit"""
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
        
        practice = st.selectbox(
            "Primary Practice", 
            ["Conventional", "No-Till", "Agroforestry", "Cover Cropping", "Regenerative"]
        )
        
        # NEW: Soil type input
        soil_type = st.selectbox(
            "Soil Type",
            ["Loam", "Clay", "Sandy"],
            help="🌾 Check soil type—affects carbon retention"
        )
        
        # NEW: Crop selection
        crops = st.multiselect(
            "Crops Grown",
            ["Maize", "Beans", "Coffee", "Tea", "Avocado", "Banana", "Vegetables"],
            help="Select all crops on your farm"
        )
        
        if st.button("📊 Generate Baseline Audit"):
            audit_results = calculate_baseline_carbon(farm_size, practice, soil_type, crops)
            tco2e = audit_results['estimated_tCO2e']
            
            # Display results
            st.success(f"✅ **Est. Sequestration:** {tco2e} tCO2e/year")
            
            # NEW: Show soil health note
            st.info(audit_results['soil_health_note'])
            
            # NEW: Show carbon credit earnings
            st.markdown("---")
            st.subheader("💰 Carbon Credit Market Value")
            
            col_earn1, col_earn2 = st.columns(2)
            
            with col_earn1:
                earnings = calculate_potential_earnings(tco2e, "vcs_verified_carbon_unit")
                st.metric(
                    "Annual Value (USD)",
                    f"${earnings['annual_earnings_usd']}",
                    help="Based on Verra carbon credit standard"
                )
            
            with col_earn2:
                st.metric(
                    "Annual Value (KES)",
                    f"KES {earnings['annual_earnings_kes']:,}",
                    help="Approximate Kenyan Shilling conversion"
                )
            
            # Show certification path
            with st.expander("🏆 Get Carbon Credit Certified", expanded=False):
                cert_type = st.selectbox(
                    "Certification Path",
                    ["Verra VCS (International)", "Gold Standard", "Kenya National"]
                )
                
                cert_map = {
                    "Verra VCS (International)": "vcs_verra",
                    "Gold Standard": "gold_standard",
                    "Kenya National": "kenya_national"
                }
                
                cert_key = cert_map[cert_type]
                requirements = get_carbon_certification_requirements()[cert_key]
                
                col_cert1, col_cert2 = st.columns(2)
                
                with col_cert1:
                    st.markdown(f"**{requirements['standard']}**")
                    st.metric("Cost (Approx)", f"${requirements['cost_estimate_usd']}")
                    st.metric("Timeline", f"{requirements['timeline_months']} months")
                
                with col_cert2:
                    st.markdown("**Pros:**")
                    for pro in requirements['pros']:
                        st.caption(f"✅ {pro}")
                    st.markdown("**Cons:**")
                    for con in requirements['cons']:
                        st.caption(f"⚠️ {con}")
                
                st.markdown("---")
                st.markdown("**Certification Checklist:**")
                checklist = get_certification_checklist(cert_key)
                for step in checklist:
                    st.caption(step)
            
            # Save audit to AI memory
            audit_msg = f"[System Alert: User generated an audit. Size: {farm_size} acres. Practice: {practice}. Soil: {soil_type}. Sequestration: {tco2e} tCO2e/yr. Crops: {', '.join(crops) if crops else 'Not specified'}]"
            st.session_state.messages.append({"role": "user", "content": audit_msg})
            st.caption("✅ Audit saved to AI memory. You can ask the Assistant about these results.")
 
def veterinary_page():
    """Page: Find Nearby Veterinary Services & Emergency Support"""
    st.title("🐄 Livestock Veterinary Support")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### 📍 Nearby Veterinary Clinics")
        
        if not st.session_state.active_coords:
            st.warning("📍 **Enable location access first!**")
            st.info("""
            1. Go to **Map & Audit** page
            2. Click location button to share your GPS location
            3. Come back to this page
            """)
        else:
            lat, lon = st.session_state.active_coords
            
            # Search radius
            search_radius = st.slider("Search Radius (km)", 5, 50, 15)
            
            # Animal type filter
            animal_types = ["cattle", "poultry", "sheep", "goats", "pigs", "all"]
            selected_animal = st.selectbox(
                "Looking for vet for:",
                animal_types,
                index=5
            )
            
            with st.spinner("🔍 Finding vets near you..."):
                animal_filter = None if selected_animal == "all" else selected_animal
                vets = get_nearby_veterinarians(lat, lon, search_radius, animal_filter)
            
            if vets:
                st.success(f"✅ Found {len(vets)} vet(s) near you")
                
                for i, vet in enumerate(vets):
                    with st.container(border=True):
                        vet_col1, vet_col2 = st.columns([3, 1])
                        
                        with vet_col1:
                            st.markdown(f"### **{vet['name']}**")
                            
                            # Key info
                            col_info1, col_info2 = st.columns(2)
                            with col_info1:
                                st.caption(f"📍 **Distance:** {vet['distance_km']} km")
                                st.caption(f"📞 **Phone:** {vet['phone']}")
                                st.caption(f"🕐 **Hours:** {vet['hours']}")
                            with col_info2:
                                st.caption(f"⭐ **Rating:** {vet['rating']}")
                                st.caption(f"🆘 **Emergency:** {vet['emergency_hours']}")
                                st.caption(f"📍 **Area:** {vet['address']}")
                            
                            st.caption(f"**Treats:** {', '.join(vet['services'])}")
                            st.caption(f"**Specializes in:** {', '.join(vet['specialties'])}")
                        
                        with vet_col2:
                            # Action buttons
                            col_btn1, col_btn2 = st.columns(2)
                            
                            with col_btn1:
                                if st.button("📞", key=f"call_{vet['id']}", help="Call", use_container_width=True):
                                    st.success(f"📞 Calling {vet['phone']}...")
                            
                            with col_btn2:
                                if st.button("💬", key=f"whatsapp_{vet['id']}", help="WhatsApp", use_container_width=True):
                                    st.info(f"💬 WhatsApp ready: {vet['whatsapp']}")
                    
                    st.write("")  # Spacer
            else:
                st.warning(f"⚠️ No vets found within {search_radius} km.")
                st.info("Try increasing the search radius or check your location.")
    
    with col2:
        st.markdown("### 🆘 Emergency Care")
        
        # Emergency hotlines
        st.subheader("Emergency Hotlines")
        hotlines = get_emergency_hotline()
        
        for hotline_key, hotline_info in hotlines.items():
            with st.container(border=True):
                st.markdown(f"**{hotline_info['name']}**")
                st.markdown(f"`{hotline_info['phone']}`")
                st.caption(hotline_info['description'])
        
        st.markdown("---")
        
        # Emergency tips
        st.subheader("⚠️ When to Call Vet")
        
        selected_animal_tips = st.selectbox(
            "Select animal type for tips:",
            ["cattle", "poultry", "sheep_goats"],
            key="emergency_tips_animal"
        )
        
        tips = get_emergency_care_tips(selected_animal_tips)
        
        with st.expander("🔴 Warning Signs", expanded=True):
            for sign in tips["signs"]:
                st.markdown(f"• {sign}")
        
        with st.expander("✅ Immediate Actions"):
            for action in tips["immediate_actions"]:
                st.markdown(f"✓ {action}")
        
        with st.expander("❌ What NOT to Do"):
            for avoid in tips["avoid"]:
                st.markdown(f"✗ {avoid}")

# --- 4. NAVIGATION ROUTER ---
# This bundles the functions into pages and creates the sidebar menu automatically
pg = st.navigation([
    st.Page(chat_page, title="AI Assistant", icon="💬"),
    st.Page(audit_page, title="Map & Audit", icon="🌍"),
    st.Page(veterinary_page, title="Vet Services", icon="🐄"),
])
# Run the app
pg.run()