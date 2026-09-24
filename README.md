# 🎙️ Google Meet AI Interpreter (meetTTS)

An open-source, zero-configuration real-time translation tool for Google Meet. It captures closed captions directly from your browser, translates them instantly using **GPT-OSS 20B** (via OpenAI-compatible endpoints) or **Google Gemini**, and speaks them out loud using Google Text-to-Speech (gTTS).

![Dark Mode UI](https://img.shields.io/badge/UI-Material_Design_3-blue) ![Language](https://img.shields.io/badge/Language-Python_3.12-yellow) ![License](https://img.shields.io/badge/License-Free-green)

---

## ✨ Features
- **Zero Configuration:** Works via a simple browser Bookmarklet. No extensions to install, no sketchy bots joining your calls.
- **Ultra-Fast Translation:** Powered by the GPT-OSS 20B model infrastructure.
- **Multi-language Support:** Instantly switch between Spanish, English, French, German, Italian, Portuguese, Japanese, and Chinese.
- **Smart Diffing:** Python backend ignores Google Meet's live typo-corrections and prevents repetitive, robotic TTS loops.
- **Dark Mode:** Clean, Material Design 3 interface that auto-detects your system preferences.

---

## 🚀 How to Run Locally

If you want to host your own version (highly recommended to avoid rate limits on free API keys), you can easily run this on your own machine.

### 1. Prerequisites
- **Python 3.10+** installed on your machine.
- A free API key configured for OpenAI-compatible endpoints (GROQ_API_KEY) OR Google Gemini (GEMINI_API_KEY).

### 2. Environment Variables
Create a file named .env in the root folder of the project and paste your API key inside:

`env
GROQ_API_KEY=your_api_key_here
`
*(If you prefer to use Google Gemini, use GEMINI_API_KEY=your_gemini_key_here instead).*

### 3. Quick Start (1-Click)

**For Windows:**
Simply double-click the start.bat file in the project folder. It will automatically create a virtual environment, install dependencies, and launch the server.

**For Mac / Linux:**
Open your terminal and run:
`ash
bash start.sh
`

### 4. Start Translating!
1. Open your browser and go to http://localhost:8000
2. You will see the **Google Meet Interpreter** Dashboard.
3. Drag the **Translate Google Meet** button to your browser's bookmarks bar.
4. Join any Google Meet call, turn on Captions (CC), and click your new bookmark!

---

## 🛠️ Created by
Developed by [ANGELUS11](https://angelus11.dev). Free to use and modify.
