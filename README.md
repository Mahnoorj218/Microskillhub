MicroSkillHub

A full-stack web application for a skills marketplace where users can learn and share micro-skills, powered by an AI assistant.

Group Members:
- Urwa Iftikhar
- Nayab Afzal
- Mahnoor Jahangir

Tech Stack:
Frontend: HTML, CSS, JavaScript
Backend: FastAPI (Python)
Database: PostgreSQL
AI: Google Gemini API

Features:
- User Authentication (Register/Login)
- Skills Listing and Management
- AI-powered Assistant for skill recommendations
- RESTful API with FastAPI





Setup Instructions:
1. Clone the Repository:
bash
git clone https://github.com/Mahnoorj218/MicroSkillHub.git
cd MicroSkillHub
2. Backend Setup:
bash
cd Backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
3. Create .env File:
Create a .env file in the Backend folder:
DATABASE_URL=postgresql://username:password@localhost/microskillhub
SECRET_KEY=your_secret_key_here
GEMINI_API_KEY=your_gemini_api_key_here
4. Run the Backend:
bash
uvicorn main:app --reload
5. Open Frontend:
Open Frontend/index.html in your browser.

Live Deployment URL:
Coming soon (Railway/Render)


Running Tests:
bash
cd Backend
pytest test_main.py -v

Project Structure:

MicroSkillHub/
├── Backend/
│   ├── main.py
│   ├── db.py
│   ├── schemas.py
│   ├── ai_service.py
│   ├── schema.sql
│   ├── requirements.txt
│   └── test_main.py
└── Frontend/
    ├── index.html
    ├── app.js
    └── style.css
