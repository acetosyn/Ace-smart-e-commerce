🛒 ACE: Smart e-Commerce System

## 📸 Demo Screenshot

[![ACE Demo Screenshot](static/images/Ace.JPG)](static/images/Ace.JPG)


ACE (AI Commerce Engine) is a voice- and chat-enabled smart assistant that helps users effortlessly find top-rated products across major e-commerce platforms like Jumia, Amazon, and more. Just speak or type the product you want — ACE automates the search and returns the best matches based on user needs and reviews.

🔍 Features
Voice Assistant (Voicebot) – 

Chat Assistant (Chatbot) – T

E-commerce Scraper Engine –

Auto-Typing Search Input – 

Contextual Product Memory – 

Responsive UI 

ace-smart-ecommerce/
│
├── static/
│   ├── css/
│   ├── js/
│   └── images/
├── templates/
│   ├── index.html
│   └── home.html
│
├── app.py              # Flask app and routing
├── engine.py           # LLM backend for chat
├── engine2.py          # Web scraping logic
├── llm_engine.py       # Handles context-aware voice assistant logic
├── search_fetch.js     # Auto-search and input typing handler
├── chatbot.js          # Chatbot frontend logic
├── voicebot.js         # Voicebot frontend logic
├── requirements.txt
└── README.md



⚙️ Technologies Used
Frontend: HTML, CSS, JavaScript, Lottie animations

Backend: Python (Flask)

AI/LLM: LLaMA 3 via Groq API (streamed)

Scraping: Requests, BeautifulSoup, Srapperapi

TTS: Currently optional (planned integration with Google TTS, 11Labs, or Coqui)

Context Memory: Custom logic using sessionStorage and context parsing


Future Improvements
Integrate production-ready TTS via 11Labs or Google TTS.

Add more e-commerce platforms (Amazon, Konga, etc).

Enable product comparison and price history.

Add user account and wishlists.

Deploy to Render, Vercel, or a cloud VM with HTTPS.


👤 Author
Developer: [ALIYU HAKEEM TOSIN]
Project: ACE - Smart e-Commerce System

Contact: [acetosyn@gmail.com
Git - acetosyn
                            ]
