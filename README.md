# AI Google Meet Live Interpreter

This project automatically captures live transcription (captions) from Google Meet, translates them in real-time using **Gemini 2.5 Flash**, and reads them out loud using **Text-To-Speech (TTS)**.

## Prerequisites

1. You must have **Google Chrome** installed.
2. An active Google Gemini API Key.

## Setup

1. Add your API key to the .env file:
   `env
   GEMINI_API_KEY=your_api_key_here
   `

## How to run

1. **Start Chrome in Debug Mode**
   You MUST completely close Google Chrome (all windows) and then start it from your terminal using this exact command:
   
   **Windows:**
   `powershell
   & "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222
   `

2. **Join the Meeting**
   In the Chrome browser that opens, go to Google Meet, join your meeting, and click the **"Turn on captions" (CC)** button. The script needs the captions to be visible to scrape them.

3. **Run the Interpreter**
   Open a new terminal in this folder and run:
   `powershell
   uv run src/main.py
   `

## Architecture
- \scraper.py\: Connects to Chrome via Playwright CDP and observes the DOM for new caption chunks.
- \	ranslator.py\: Orchestrates Gemini 2.5 Flash to accurately translate the spoken context into Spanish (or any language).
- \	ts.py\: Generates the TTS audio using \gTTS\ and plays it asynchronously using \pygame\.
