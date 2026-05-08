# app.py

import streamlit as st
import requests
import google.generativeai as genai
from gtts import gTTS
import os

# --- API KEYS ---
OPENWEATHERMAP_API_KEY = ""
GEMINI_API_KEY = ""
genai.configure(api_key=GEMINI_API_KEY)

# --- Fetch Coordinates for a City ---
def get_coordinates(city):
    try:
        geo_url = f"http://api.openweathermap.org/geo/1.0/direct?q={city}&limit=1&appid={OPENWEATHERMAP_API_KEY}"
        response = requests.get(geo_url).json()
        if response:
            return response[0]["lat"], response[0]["lon"]
        else:
            return None, None
    except:
        return None, None

# --- Fetch AQI using OpenWeatherMap ---
def fetch_aqi(city):
    lat, lon = get_coordinates(city)
    if lat is None:
        return None
    try:
        aqi_url = f"http://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={OPENWEATHERMAP_API_KEY}"
        response = requests.get(aqi_url).json()
        aqi = response["list"][0]["main"]["aqi"]
        return aqi
    except:
        return None

# --- Convert AQI index to description ---
def classify_aqi(aqi):
    mapping = {
        1: "Good",
        2: "Fair",
        3: "Moderate",
        4: "Poor",
        5: "Very Poor"
    }
    return mapping.get(aqi, "Unknown")

# --- Fetch Earthquake Alerts from USGS ---
def fetch_disaster_alerts():
    try:
        url = "https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&minmagnitude=5&orderby=time"
        response = requests.get(url)
        data = response.json()

        alerts = []
        for feature in data.get("features", [])[:5]:
            props = feature.get("properties", {})
            title = props.get("title", "No title")
            alerts.append(f"{title}")

        return alerts if alerts else ["No recent disaster alerts."]
    except Exception as e:
        print(f"[ERROR] USGS API failed: {e}")
        return ["Disaster alert fetch failed."]

# --- Generate Guidelines with Gemini ---
def generate_guidelines_with_gemini(aqi_value, aqi_description, disasters):
    try:
        prompt = f"""You are an environmental safety assistant. Based on the following data, generate public safety guidelines:

Air Quality Index (AQI): {aqi_value} ({aqi_description})
Current Disaster Alerts:
{chr(10).join(disasters)}

Write concise, clear bullet points suitable for the public. Avoid panic, focus on clarity and helpful action.
"""

        model = genai.GenerativeModel("gemini-pro")
        response = model.generate_content(prompt)

        return response.text.strip()
    except Exception as e:
        print(f"[ERROR] Gemini call failed: {e}")
        return "⚠️ Could not generate alert using Gemini at this time."

# --- Generate Voice Summary ---
def generate_voice_summary(text, filename="alert.mp3"):
    try:
        tts = gTTS(text)
        tts.save(filename)
        return filename
    except Exception as e:
        print(f"[ERROR] TTS generation failed: {e}")
        return None

# --- Streamlit UI ---
st.set_page_config(page_title="Environmental & Disaster Alert Bot", page_icon="🌍")
st.title("🌍 Real-Time Environmental & Disaster Alert Chatbot")

city = st.text_input("Enter your city", value="Delhi")

if st.button("Check Conditions & Generate Alert"):
    aqi = fetch_aqi(city)
    if aqi:
        condition = classify_aqi(aqi)
        st.success(f"✅ AQI for {city.title()}: {aqi} ({condition})")
    else:
        condition = "Unknown"
        st.error("❌ Failed to fetch AQI data.")

    st.markdown("### 🌪️ Current Earthquake Alerts:")
    disasters = fetch_disaster_alerts()
    for d in disasters:
        st.markdown(f"- {d}")

    st.markdown("### 🔔 Public Safety Guidelines:")
    if aqi and disasters:
        guidelines = generate_guidelines_with_gemini(aqi, condition, disasters)
        st.markdown(guidelines)

        st.markdown("### 🔊 Voice Summary:")
        audio_path = generate_voice_summary(guidelines)
        if audio_path:
            audio_file = open(audio_path, 'rb')
            audio_bytes = audio_file.read()
            st.audio(audio_bytes, format='audio/mp3')
        else:
            st.warning("⚠️ Could not generate voice alert.")
    else:
        st.warning("⚠️ Could not generate alert at this time.")

st.markdown("---")
st.caption("Developed by Code Pilots")