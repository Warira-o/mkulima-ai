import streamlit as st
import os
import pandas as pd
from dotenv import load_dotenv
from streamlit_geolocation import streamlit_geolocation

load_dotenv()

from services.llm import generate_farm_advice
from services.translation import translate_text
from services.vision import analyze_crop_image, analyze_crop_image_full
from services.speech import audio_to_text, text_to_audio
from services.weather import get_weather_by_coords
from services.carbon import calculate_baseline_carbon
from services.veterinary import (
    get_nearby_veterinarians,
    get_emergency_hotline,
    get_emergency_care_tips,
)
from services.carbon_markets import (
    calculate_potential_earnings,
    get_carbon_certification_requirements,
    get_certification_checklist,
)
from services.market_prices import (
    get_market_prices,
    get_best_market,
    format_price_table,
    get_last_updated,
    FALLBACK_PRICES,
    TREND_ARROWS,
)
from services.planting_calendar import (
    generate_planting_calendar,
    get_zone_description,
)

st.set_page_config(page_title="Mkulima AI", page_icon="🌍", layout="wide")

LANG_MAP = {"English": "eng_Latn", "Swahili": "swa_Latn", "Kikuyu": "kik_Latn"}

# ---------- SESSION STATE ----------
for key, default in [
    ("messages", [{"role": "assistant", "content": "Welcome to Mkulima AI. How can I help your farm today?"}]),
    ("processed_files", set()),
    ("weather_context", ""),
    ("active_coords", None),
    ("carbon_history", []),
]:
    if key not in st.session_state:
        st.session_state[key] = default

# ---------- SIDEBAR ----------
with st.sidebar:
    st.title("🌍 Mkulima AI")
    st.caption("Climate-Smart Farming for Kenya")
    st.session_state.selected_lang = st.selectbox(
        "Language / Lugha", ["English", "Swahili", "Kikuyu"], index=0
    )
    st.markdown("---")
    if st.button("🗑️ Clear Chat History"):
        st.session_state.messages = [{"role": "assistant", "content": "Welcome to Mkulima AI. How can I help your farm today?"}]
        st.session_state.processed_files = set()
        st.rerun()


# ============================================================
# PAGE 1 — AI ASSISTANT
# ============================================================
def chat_page():
    st.title("💬 AI Assistant")

    for msg in st.session_state.messages:
        if msg["content"].startswith("[System"):
            continue
        with st.chat_message(msg["role"]):
            if msg.get("image"):
                st.image(msg["image"], use_container_width=True)
            st.markdown(msg["content"])
            if msg.get("audio"):
                st.audio(msg["audio"], format="audio/mp3")

    st.write("")
    with st.expander("📎 Attach Image or Voice Note", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            uploaded_file = st.file_uploader("📸 Upload Image", type=["jpg", "jpeg", "png"], label_visibility="collapsed")
        with col2:
            audio_bytes = st.audio_input("🎙️ Record Voice", label_visibility="collapsed")

    # IMAGE
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
                target_lang_code = LANG_MAP[st.session_state.get("selected_lang", "English")]
                final_response = translate_text(response, "eng_Latn", target_lang_code)
                st.markdown(final_response)
        st.session_state.messages.append({"role": "assistant", "content": final_response})
        st.rerun()

    # VOICE
    if audio_bytes and audio_bytes.file_id not in st.session_state.processed_files:
        st.session_state.processed_files.add(audio_bytes.file_id)
        temp_audio_path = "temp_mic.wav"
        target_lang_code = LANG_MAP[st.session_state.get("selected_lang", "English")]
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

    # TEXT
    if prompt := st.chat_input("Ask about carbon markets, soil health, crop diseases, prices..."):
        target_lang_code = LANG_MAP[st.session_state.get("selected_lang", "English")]
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


# ============================================================
# PAGE 2 — FARM MAP & CARBON AUDIT
# ============================================================
def audit_page():
    st.title("🌍 Farm Map & Carbon Audit")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 📍 Location Tracker")
        location = streamlit_geolocation()
        if location and location.get("latitude") and location.get("longitude"):
            coords = (location["latitude"], location["longitude"])
            st.session_state.active_coords = coords
            with st.spinner("Fetching map & weather..."):
                st.session_state.weather_context = get_weather_by_coords(coords[0], coords[1])
        if st.session_state.active_coords:
            lat, lon = st.session_state.active_coords
            st.success(f"**Mapped:** {lat:.4f}, {lon:.4f}")
            df = pd.DataFrame({"lat": [lat], "lon": [lon]})
            st.map(df, zoom=14, use_container_width=True)
        if st.session_state.weather_context:
            st.info(f"**Local Weather:** {st.session_state.weather_context}")

    with col2:
        st.markdown("### 📊 Carbon Audit Tool")
        farm_size = st.number_input("Farm Size (Acres)", min_value=1.0, value=5.0)
        practice = st.selectbox("Primary Practice", ["Conventional", "No-Till", "Agroforestry", "Cover Cropping", "Regenerative"])
        soil_type = st.selectbox("Soil Type", ["Loam", "Clay", "Sandy"], help="Affects carbon retention")
        crops = st.multiselect("Crops Grown", ["Maize", "Beans", "Coffee", "Tea", "Avocado", "Banana", "Vegetables"])

        if st.button("📊 Generate Baseline Audit"):
            audit_results = calculate_baseline_carbon(farm_size, practice, soil_type, crops)
            tco2e = audit_results["estimated_tCO2e"]
            st.success(f"✅ **Est. Sequestration:** {tco2e} tCO2e/year")
            st.info(audit_results["soil_health_note"])

            # Save to carbon history for dashboard
            from datetime import datetime
            st.session_state.carbon_history.append({
                "date": datetime.now().strftime("%b %Y"),
                "tCO2e": tco2e,
                "practice": practice,
            })

            st.markdown("---")
            st.subheader("💰 Carbon Credit Market Value")
            col_earn1, col_earn2 = st.columns(2)
            with col_earn1:
                earnings = calculate_potential_earnings(tco2e, "vcs_verified_carbon_unit")
                st.metric("Annual Value (USD)", f"${earnings['annual_earnings_usd']}", help="Based on Verra carbon credit standard")
            with col_earn2:
                st.metric("Annual Value (KES)", f"KES {earnings['annual_earnings_kes']:,}")

            with st.expander("🏆 Get Carbon Credit Certified", expanded=False):
                cert_type = st.selectbox("Certification Path", ["Verra VCS (International)", "Gold Standard", "Kenya National"])
                cert_map = {"Verra VCS (International)": "vcs_verra", "Gold Standard": "gold_standard", "Kenya National": "kenya_national"}
                cert_key = cert_map[cert_type]
                requirements = get_carbon_certification_requirements()[cert_key]
                col_cert1, col_cert2 = st.columns(2)
                with col_cert1:
                    st.markdown(f"**{requirements['standard']}**")
                    st.metric("Cost (Approx)", f"${requirements['cost_estimate_usd']}")
                    st.metric("Timeline", f"{requirements['timeline_months']} months")
                with col_cert2:
                    st.markdown("**Pros:**")
                    for pro in requirements["pros"]:
                        st.caption(f"✅ {pro}")
                    st.markdown("**Cons:**")
                    for con in requirements["cons"]:
                        st.caption(f"⚠️ {con}")
                st.markdown("---")
                st.markdown("**Certification Checklist:**")
                for step in get_certification_checklist(cert_key):
                    st.caption(step)

            audit_msg = f"[System Alert: User generated an audit. Size: {farm_size} acres. Practice: {practice}. Soil: {soil_type}. Sequestration: {tco2e} tCO2e/yr. Crops: {', '.join(crops) if crops else 'Not specified'}]"
            st.session_state.messages.append({"role": "user", "content": audit_msg})
            st.caption("✅ Audit saved to AI memory and Carbon Dashboard.")


# ============================================================
# PAGE 3 — CARBON PROGRESS DASHBOARD (NEW)
# ============================================================
def carbon_dashboard_page():
    st.title("📈 Carbon Progress Dashboard")
    st.caption("Track how your farming practices are building carbon sequestration over time.")

    history = st.session_state.carbon_history

    if not history:
        st.info("No audit data yet. Run a Carbon Audit on the **Map & Audit** page to start tracking your progress.")
        st.markdown("---")
        st.markdown("### Why track carbon progress?")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Avg. Carbon Price", "$15–30 / tCO2e", help="Current voluntary carbon market rates")
        with col2:
            st.metric("Typical Smallholder Gain", "1–7 tCO2e/yr", help="Per acre with regenerative practices")
        with col3:
            st.metric("Potential Annual Income", "KES 2,000–30,000", help="From carbon credits per acre")
        return

    # Build chart data
    df = pd.DataFrame(history)

    st.markdown("### Sequestration Over Time (tCO2e/year)")
    st.line_chart(df.set_index("date")["tCO2e"])

    st.markdown("### Audit History")
    st.dataframe(df, use_container_width=True)

    # Summary metrics
    latest = history[-1]["tCO2e"]
    best = max(h["tCO2e"] for h in history)
    earnings = calculate_potential_earnings(latest, "vcs_verified_carbon_unit")

    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Latest Sequestration", f"{latest} tCO2e/yr")
    with col2:
        st.metric("Best Ever", f"{best} tCO2e/yr")
    with col3:
        st.metric("Est. Current Earnings", f"KES {earnings['annual_earnings_kes']:,}/yr")

    st.markdown("---")
    st.markdown("### 🌱 How to increase your carbon score")
    tips = [
        ("Switch from Conventional to No-Till", "+200% carbon sequestration"),
        ("Add Agroforestry (trees on farm)", "+650% carbon sequestration"),
        ("Use Cover Cropping between seasons", "+300% carbon sequestration"),
        ("Move to fully Regenerative practices", "+500% carbon sequestration"),
    ]
    for tip, impact in tips:
        with st.container(border=True):
            col_t1, col_t2 = st.columns([3, 1])
            with col_t1:
                st.markdown(f"**{tip}**")
            with col_t2:
                st.caption(impact)


# ============================================================
# PAGE 4 — CROP DISEASE SCANNER (UPGRADED)
# ============================================================
def disease_scanner_page():
    st.title("🔬 Crop Disease Scanner")
    st.caption("Take a photo of a sick plant and get an instant diagnosis and treatment plan.")

    st.info("📸 Upload a clear photo of the affected leaf, stem, or fruit for best results.")

    uploaded_file = st.file_uploader(
        "Upload crop photo", type=["jpg", "jpeg", "png"], label_visibility="collapsed"
    )

    if uploaded_file:
        image_bytes = uploaded_file.getvalue()
        col1, col2 = st.columns([1, 2])

        with col1:
            st.image(image_bytes, caption="Your uploaded photo", use_container_width=True)

        with col2:
            with st.spinner("🔍 Analyzing your crop..."):
                result = analyze_crop_image_full(image_bytes)

            disease = result["disease"]

            if disease == "Healthy" or "Healthy" in disease:
                st.success(f"✅ **{disease}**")
            else:
                st.error(f"🦠 **Detected: {disease}**")

            st.markdown(f"**Urgency:** {result['urgency']}")
            st.markdown(f"**Cause:** {result['cause']}")

            st.markdown("---")
            st.markdown("**Symptoms:**")
            st.caption(result["symptoms"])

            st.markdown("**Treatment Steps:**")
            for i, step in enumerate(result["treatment"], 1):
                st.markdown(f"{i}. {step}")

        # Push to AI memory so the assistant knows
        disease_msg = f"[System: Crop disease scanner detected '{disease}' on farmer's plant. Treatment steps provided.]"
        st.session_state.messages.append({"role": "user", "content": disease_msg})

        st.markdown("---")
        st.info("💬 You can ask the **AI Assistant** more questions about this disease.")


# ============================================================
# PAGE 5 — MARKET PRICE TRACKER (NEW)
# ============================================================
def market_prices_page():
    st.title("📊 Market Price Tracker")
    st.caption(f"Daily commodity prices across Kenya markets. Last updated: {get_last_updated()}")

    commodities = list(FALLBACK_PRICES.keys())
    selected = st.selectbox("Select a crop to check prices:", commodities)

    data = FALLBACK_PRICES.get(selected, {})
    best = get_best_market(selected)
    price_table = format_price_table(selected)

    st.markdown("---")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(
            f"Best Price — {best['market']}",
            f"KES {best['price']:,}",
            help=f"Per {best['unit']}"
        )
    with col2:
        st.metric("Market Trend", best["trend"])
    with col3:
        unit = data.get("unit", "")
        st.metric("Unit", unit)

    st.markdown("---")
    st.markdown("### 🗺️ Prices by Market")
    df = pd.DataFrame(price_table)
    st.dataframe(df, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.info(f"💡 **Tip:** {best['tip']}")

    st.markdown("---")
    st.markdown("### Quick Overview — All Crops Today")
    overview_data = []
    for crop, info in FALLBACK_PRICES.items():
        best_market = max(info["markets"], key=lambda m: info["markets"][m])
        best_price = info["markets"][best_market]
        overview_data.append({
            "Crop": crop,
            "Best Market": best_market,
            f"Best Price (KES)": f"{best_price:,}",
            "Unit": info["unit"],
            "Trend": TREND_ARROWS.get(info["trend"], "➡️"),
        })
    st.dataframe(pd.DataFrame(overview_data), use_container_width=True, hide_index=True)

    # Push market info to AI context
    market_msg = f"[System: Farmer checked market prices. {selected} best price is KES {best['price']:,} per {best['unit']} in {best['market']}. Trend: {best['trend']}]"
    if market_msg not in [m["content"] for m in st.session_state.messages[-3:]]:
        st.session_state.messages.append({"role": "user", "content": market_msg})


# ============================================================
# PAGE 6 — PLANTING CALENDAR (NEW)
# ============================================================
def planting_calendar_page():
    st.title("🗓️ Personalised Planting Calendar")
    st.caption("Get a planting and harvesting schedule based on your location and crops.")

    if not st.session_state.active_coords:
        st.warning("📍 **Share your location first!**")
        st.info("Go to the **Map & Audit** page, click the location button, then come back here.")
        return

    lat, lon = st.session_state.active_coords
    st.success(f"📍 Using your location: {lat:.4f}, {lon:.4f}")

    crops = st.multiselect(
        "Which crops do you grow?",
        ["Maize", "Beans", "Coffee", "Tea", "Avocado", "Banana", "Vegetables"],
        default=["Maize", "Beans"] if not st.session_state.get("audit_crops") else [],
        help="Select all crops on your farm"
    )

    if not crops:
        st.info("Select at least one crop above to generate your calendar.")
        return

    calendar = generate_planting_calendar(lat, lon, crops)
    zone_desc = get_zone_description(calendar["zone"].lower().replace(" ", "_"))

    st.markdown("---")
    st.markdown(f"### 🌍 Your Farming Zone: **{calendar['zone']}**")
    st.caption(zone_desc)
    st.caption(f"Current month: **{calendar['current_month']}**")

    st.markdown("---")
    st.markdown("### 🌱 Your Crop Schedule")

    for crop_entry in calendar["schedule"]:
        with st.container(border=True):
            st.markdown(f"#### {crop_entry['crop']}")

            for season in crop_entry["seasons"]:
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.caption(f"**Season:** {season['season']}")
                with col2:
                    st.caption(f"**Plant:** {season['plant_month']}")
                with col3:
                    st.caption(f"**Harvest:** {season['harvest_month']}")
                with col4:
                    st.caption(season["timing"])

            st.markdown("---")
            col_a, col_b = st.columns(2)
            with col_a:
                st.caption(f"🌤️ **Climate tip:** {crop_entry['climate_tip']}")
                st.caption(f"⚠️ **Climate risk:** {crop_entry['climate_risk']}")
            with col_b:
                st.caption(f"🌱 **Carbon benefit:** {crop_entry['carbon_benefit']}")
                st.caption(f"🌍 **Best soil:** {', '.join(crop_entry['soil_pref'])}")

    # Save to AI memory
    crops_str = ", ".join(crops)
    calendar_msg = f"[System: Farmer is in the {calendar['zone']} zone and grows {crops_str}. A personalised planting calendar has been generated for their location ({lat:.4f}, {lon:.4f}).]"
    if calendar_msg not in [m["content"] for m in st.session_state.messages[-3:]]:
        st.session_state.messages.append({"role": "user", "content": calendar_msg})


# ============================================================
# PAGE 7 — VETERINARY SUPPORT
# ============================================================
def veterinary_page():
    st.title("🐄 Livestock Veterinary Support")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("### 📍 Nearby Veterinary Clinics")
        if not st.session_state.active_coords:
            st.warning("📍 **Enable location access first!**")
            st.info("1. Go to **Map & Audit** page\n2. Click the location button\n3. Come back here")
        else:
            lat, lon = st.session_state.active_coords
            search_radius = st.slider("Search Radius (km)", 5, 50, 15)
            animal_types = ["cattle", "poultry", "sheep", "goats", "pigs", "all"]
            selected_animal = st.selectbox("Looking for vet for:", animal_types, index=5)

            with st.spinner("🔍 Finding vets near you..."):
                animal_filter = None if selected_animal == "all" else selected_animal
                vets = get_nearby_veterinarians(lat, lon, search_radius, animal_filter)

            if vets:
                st.success(f"✅ Found {len(vets)} vet(s) near you")
                for vet in vets:
                    with st.container(border=True):
                        vet_col1, vet_col2 = st.columns([3, 1])
                        with vet_col1:
                            st.markdown(f"### **{vet['name']}**")
                            st.caption(f"📍 **Distance:** {vet['distance_km']} km &nbsp;&nbsp;|&nbsp;&nbsp; ⭐ **Rating:** {vet['rating']}")
                            st.caption(f"📞 **Phone:** {vet['phone']} &nbsp;&nbsp;|&nbsp;&nbsp; 🆘 **Emergency:** {vet['emergency_hours']}")
                            st.caption(f"🕐 **Hours:** {vet['hours']} &nbsp;&nbsp;|&nbsp;&nbsp; 📍 **Area:** {vet['address']}")
                            st.write("")
                            st.caption(f"**Treats:** {', '.join(vet['services'])}")
                            st.caption(f"**Specializes in:** {', '.join(vet['specialties'])}")
                        with vet_col2:
                            if st.button("📞 Call", key=f"call_{vet['id']}", use_container_width=True):
                                st.success(f"📞 Calling {vet['phone']}...")
                            if st.button("💬 WhatsApp", key=f"whatsapp_{vet['id']}", use_container_width=True):
                                st.info(f"💬 WhatsApp: {vet['whatsapp']}")
                    st.write("")
            else:
                st.warning(f"⚠️ No vets found within {search_radius} km. Try increasing radius.")

    with col2:
        st.markdown("### 🆘 Emergency Care")
        st.subheader("Emergency Hotlines")
        for _, hotline_info in get_emergency_hotline().items():
            with st.container(border=True):
                st.markdown(f"**{hotline_info['name']}**")
                st.markdown(f"`{hotline_info['phone']}`")
                st.caption(hotline_info["description"])
        st.markdown("---")
        st.subheader("⚠️ When to Call Vet")
        selected_animal_tips = st.selectbox("Select animal:", ["cattle", "poultry", "sheep_goats"], key="tips_animal")
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


# ============================================================
# NAVIGATION
# ============================================================
pg = st.navigation([
    st.Page(chat_page,             title="AI Assistant",        icon="💬"),
    st.Page(audit_page,            title="Map & Audit",         icon="🌍"),
    st.Page(carbon_dashboard_page, title="Carbon Dashboard",    icon="📈"),
    st.Page(disease_scanner_page,  title="Disease Scanner",     icon="🔬"),
    st.Page(market_prices_page,    title="Market Prices",       icon="📊"),
    st.Page(planting_calendar_page,title="Planting Calendar",   icon="🗓️"),
    st.Page(veterinary_page,       title="Vet Services",        icon="🐄"),
])
pg.run()