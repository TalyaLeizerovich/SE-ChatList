# Introduction 
ChatList is an AI-powered assistant that filters, summarizes, and extracts action items from noisy WhatsApp group conversations. It uses NLP and contextual analysis to identify important reminders, deadlines, and events, generating a clear, personalized daily checklist for each user. The project aims to reduce message overload and help families and students stay organized without missing critical information. 

# Getting Started
1.	Make sure you have 3.10 python
2.	Make sure you have virtual enviroment (venv)
3.  Download on your computer: https://ollama.com/download/windows
4.	Open CMD and run: pip install -r requirements.txt

# Build and Test
1. In the first CMD run: uvicorn main:app --port 8000
2. In the second CMD run: C:\softwareEngineer\ChatList\frontend streamlit run views/ui.py
Note: During the launch, you will probably see a WhatsApp QR code. Scan it using your WhatsApp account via linked devices.

