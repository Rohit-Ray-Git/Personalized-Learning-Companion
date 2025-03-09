# 📚 Personalized Learning Companion

![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python) ![Flask](https://img.shields.io/badge/Flask-2.3.3-green?logo=flask) ![Bootstrap](https://img.shields.io/badge/Bootstrap-5.3.3-purple?logo=bootstrap) ![License](https://img.shields.io/badge/License-MIT-yellow)

Welcome to the **Personalized Learning Companion**, a web-based tool designed to enhance your learning experience by tailoring content to your unique learning style. Powered by AI and a sleek Bootstrap UI, this project helps you master topics like machine learning through quizzes, mind maps, and curated resources. 🚀

---

## ✨ Features

- **Learning Style Assessment** 🎨: Identify your VARK (Visual, Auditory, Reading/Writing, Kinesthetic) style with a quick questionnaire.
- **Document Processing** 📖: Upload PDFs (e.g., `deeplearningbook.pdf`) to extract key concepts using Hugging Face embeddings.
- **Dynamic Quizzes** ❓: Test your knowledge with baseline and follow-up quizzes, adapting to your progress.
- **Mind Maps** 🗺️: Visualize key concepts with auto-generated diagrams (saved as `static/mind_map.png`).
- **Resource Recommendations** 🔗: Get personalized web links based on your topic and learning style.
- **Progress Tracking** 📊: Save and review your scores in a SQLite database.
- **Professional UI** 💻: Built with Flask and styled with Bootstrap 5 for a responsive, modern look.

---

## 🛠️ Tech Stack

- **Backend**: Python 3.12, Flask 2.3.3
- **Frontend**: Bootstrap 5.3.3 (CDN), HTML/CSS
- **AI/ML**: 
  - Groq API (accessing LLM) for question generation
  - Hugging Face embeddings for concept extraction
- **Visualization**: Matplotlib (Agg backend) for mind maps
- **Database**: SQLite for user profiles and progress
- **Dependencies**: See `requirements.txt`

---

## 🚀 Getting Started

### Prerequisites
- Python 3.12+
- Git
- A virtual environment (recommended)

### Installation
1. **Clone the Repository**:
   ```bash
   git clone https://github.com/yourusername/personalized-learning-companion.git
   cd personalized-learning-companion
   ```
2. **Set Up Virtual Environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate
   # On Windows: venv\Scripts\activate
   ```
3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
4. **Configure APIs:**:
   - Set up a .env file with your Grok API key:
   ```bash
   GROK_API_KEY=your-api-key-here
   HF_API_KEY=your-api-key-here
   ```
5. **Prepare Data**:
- Place your PDFs (e.g., deeplearningbook.pdf) in data/raw/.
- The app will process them and cache results in data/processed_content.pkl.

### Running the App
```bash
python app.py
```

- Open your browser to http://127.0.0.1:5000.
- Start learning, review progress, or explore the UI! 🌟

---

## 🎯 Usage

1. **Start Learning**:
   - Click "Start Learning" on the homepage.
   - Enter your name (e.g., "David Baner") and topic (e.g., "Machine Learning").
   - Answer VARK questions to determine your style (e.g., Visual).
   - Upload PDFs (optional) or proceed with existing content.

2. **Take Quizzes**:
   - Complete a baseline quiz to assess your initial knowledge.
   - Follow up with a quiz targeting weaker areas.

3. **Review Results**:
   - See your scores, a mind map, and recommended resources on the "Done" page.
   - Check past progress by entering your name on the homepage.

---

## ⚙️ Development Notes

- **Caching**: Document processing is cached to `processed_content.pkl` and only reprocesses if new files are uploaded.
- **Thread Safety**: Matplotlib uses the `Agg` backend to avoid GUI conflicts with Flask.
- **API Limits**: Web search uses mock X posts (DuckDuckGo rate-limited).

### Known Issues
- Concept extraction occasionally merges terms (e.g., `strategiesandmeta algorithms`). Fix in progress.
- Question parsing may fall back to generic questions if LLM’s format varies.

---

## 🔮 Future Work

The Personalized Learning Companion is set to evolve with cutting-edge AI enhancements! Here’s what’s on the horizon:

- **LangChain AI Agents** 🤖: Integrate agents from [LangChain](https://python.langchain.com/) to create autonomous, context-aware assistants. Planned agents include:
  - **Tutor Agent**: Uses LangChain’s memory and tool-calling capabilities to provide step-by-step guidance and personalized explanations.
  - **Research Agent**: Leverages LangChain’s web search and document retrieval tools to fetch up-to-date resources beyond mock X posts.
  - **Adaptive Quiz Agent**: Combines LangChain’s reasoning with Grok to dynamically adjust question complexity and offer conversational feedback.

- **Advanced Tools** 🛠️:
  - **Real-Time Web Search**: Replace DuckDuckGo mocks with LangChain’s search tools or X API for live, relevant content.
  - **Concept Refinement**: Enhance concept extraction with LangChain’s text summarization and entity recognition to fix merged terms (e.g., `strategiesandmeta algorithms` → "strategies and meta-algorithms").
  - **Multi-Modal Support**: Add image and audio processing (e.g., via Hugging Face transformers) to support Visual and Auditory learners with richer content.

- **UI Upgrades** 🎨: Expand the Bootstrap UI with interactive dashboards, progress timelines, and agent-driven chat interfaces.

These enhancements will make the app a fully-fledged AI-powered learning platform, adapting seamlessly to each user’s needs! 🚀

---

## 🤝 Contributing

1. Fork the repo.
2. Create a branch (`git checkout -b feature/awesome-idea`).
3. Commit changes (`git commit -m "Add awesome idea"`).
4. Push to your branch (`git push origin feature/awesome-idea`).
5. Open a Pull Request!

