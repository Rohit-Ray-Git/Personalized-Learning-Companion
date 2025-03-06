# learning_assessment.py
from db_setup import setup_database, UserProfile, Progress
from sqlalchemy.orm import Session
from api_setup import setup_apis
from content_processing import process_documents
import os
from collections import Counter
import re
import networkx as nx
try:
    import matplotlib.pyplot as plt
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
from duckduckgo_search import DDGS
import pickle
import time
import glob
import threading  # For Windows-compatible timeout

VARK_QUESTIONS = [
    {"question": "You need to learn a new skill. How do you prefer to start?", "options": {"V": "Watch a video or see diagrams", "A": "Listen to an explanation or podcast", "R": "Read instructions or a manual", "K": "Try it hands-on with guidance"}},
    {"question": "When remembering something, what helps most?", "options": {"V": "Pictures or visuals", "A": "Hearing it spoken", "R": "Writing it down or reading it", "K": "Doing it physically"}}
]

VARK_CONTENT = {
    "V": {"type": "visual", "keywords": ["video", "diagram", "tutorial"]},
    "A": {"type": "auditory", "keywords": ["podcast", "audio", "lecture"]},
    "R": {"type": "read/write", "keywords": ["article", "manual", "guide"]},
    "K": {"type": "kinesthetic", "keywords": ["interactive", "hands-on", "exercise"]}
}

def assess_learning_style():
    scores = {"V": 0, "A": 0, "R": 0, "K": 0}
    print("Please answer the following questions to determine your learning style:")
    for q in VARK_QUESTIONS:
        print(f"\n{q['question']}")
        for key, option in q["options"].items():
            print(f"{key}: {option}")
        choice = input("Enter your choice (V/A/R/K): ").upper()
        if choice in scores:
            scores[choice] += 1
    dominant_style = max(scores, key=scores.get)
    print(f"\nYour learning style scores: {scores}")
    print(f"Dominant style: {dominant_style}")
    return dominant_style

def extract_key_concepts(content, topic, num_concepts=5):
    print("Extracting key concepts...")
    start_time = time.time()
    all_text = " ".join(content.values()).lower()[:10000]
    words = re.findall(r'\b\w+\b', all_text)
    bigrams = [f"{words[i]} {words[i+1]}" for i in range(len(words)-1) if all(len(w) > 3 and w.isalpha() for w in [words[i], words[i+1]])][:100]
    
    stop_words = {"this", "that", "with", "from", "which", "about", "editors", "published", "university", "handbook", "borko", "furht", "armando", "escalante"}
    phrase_counts = Counter(bigrams)
    
    topic_lower = topic.lower()
    topic_concepts = [c for c in phrase_counts.keys() if topic_lower in c and not any(sw in c.split() for sw in stop_words)]
    if len(topic_concepts) < num_concepts:
        additional_concepts = [c for c in phrase_counts.keys() if not any(sw in c.split() for sw in stop_words)]
        topic_concepts.extend(additional_concepts)
    
    unique_concepts = list(dict.fromkeys(topic_concepts))[:num_concepts]
    print(f"Debug: Extracted key concepts: {unique_concepts} (took {time.time() - start_time:.2f}s)")
    return unique_concepts

def generate_mind_map(concepts, topic):
    G = nx.Graph()
    G.add_node(topic, type="root")
    for concept in concepts:
        G.add_node(concept, type="concept")
        G.add_edge(topic, concept)
    
    mind_map_text = f"{topic}\n"
    for concept in concepts:
        mind_map_text += f"  ├── {concept}\n"
    
    if MATPLOTLIB_AVAILABLE:
        pos = nx.spring_layout(G)
        plt.figure(figsize=(8, 6))
        nx.draw(G, pos, with_labels=True, node_color="lightblue", node_size=2000, font_size=10, font_weight="bold")
        plt.title(f"Mind Map for {topic}")
        plt.savefig("mind_map.png")
        print("Mind map saved as 'mind_map.png'")
    
    return mind_map_text

def search_web(topic, style):
    print("Searching web with DuckDuckGo...")
    start_time = time.time()
    query = f"{topic} {VARK_CONTENT[style]['type']} educational resources {', '.join(VARK_CONTENT[style]['keywords'])}"
    try:
        with DDGS() as ddgs:
            results = [r for r in ddgs.text(query, region="us-en", safesearch="moderate", max_results=3)]
        formatted_results = [
            {
                "title": r.get("title", "Untitled"),
                "url": r.get("href", "https://duckduckgo.com"),
                "description": r.get("body", f"A {VARK_CONTENT[style]['type']} resource on {topic}")
            } for r in results
        ]
    except Exception as e:
        print(f"DuckDuckGo search failed: {e}. Falling back to placeholders.")
        formatted_results = [{"title": f"{topic} {VARK_CONTENT[style]['type'].capitalize()} Tutorial", "url": "https://example.com", "description": f"A {VARK_CONTENT[style]['type']} guide to {topic}"}]
    print(f"Web search completed (took {time.time() - start_time:.2f}s)")
    return formatted_results

def invoke_llm_with_timeout(llm, prompt, timeout_seconds=10):
    result = [None]
    def worker():
        result[0] = llm.invoke(prompt).content
    
    thread = threading.Thread(target=worker)
    thread.start()
    thread.join(timeout_seconds)
    if thread.is_alive():
        print(f"LLM invocation timed out after {timeout_seconds}s")
        return None
    return result[0]

def generate_questions_from_concepts(llm, concepts, topic, score, num_questions=2):
    print("Generating questions...")
    start_time = time.time()
    questions = []
    used_questions = set()
    difficulty = "basic" if score < 50 else "intermediate" if score <= 75 else "advanced"
    
    prompt = f"For the topic '{topic}', generate {num_questions} {difficulty}-level multiple-choice quiz questions about the following concepts: {', '.join(concepts)}. Each question should have 4 options (A, B, C, D) and one correct answer. Ensure relevance to {topic}. Format each as: 'Question: [q] Options: A) [a] B) [b] C) [c] D) [d] Correct: [letter]' separated by newlines."
    try:
        response = invoke_llm_with_timeout(llm, prompt)
        if response is None:
            raise Exception("Timeout occurred")
        print(f"Debug: Full LLM batch response: {response}")
    except Exception as e:
        print(f"LLM invocation failed: {e}. Using fallback questions.")
        response = (
            f"Question: How does {concepts[0]} relate to {topic}?\nOptions: A) Provides computational power B) Unrelated field C) Limits processing D) Manual method\nCorrect: A\n\n"
            f"Question: What role does {concepts[1]} play in {topic}?\nOptions: A) Supports infrastructure B) Slows development C) Increases costs D) Reduces accuracy\nCorrect: A"
        )
    
    question_pattern = re.compile(r"(?:\*\*Question:\*\*|Question:)\s*(.*?)\s*Options:\s*(.*?)\s*Correct:\s*([A-D])", re.DOTALL)
    matches = question_pattern.findall(response)
    
    for match in matches:
        q_part, opts_part, correct_part = match
        q_part = q_part.strip()
        options = {}
        for line in opts_part.split('\n'):
            if line.strip() and line[0] in "ABCD" and ")" in line:
                letter = line[0]
                text = line.split(")", 1)[1].strip()
                options[letter] = text
        if q_part and len(options) == 4 and correct_part in "ABCD" and q_part not in used_questions:
            used_questions.add(q_part)
            questions.append({"question": q_part, "options": options, "correct": correct_part})
    
    if len(questions) < num_questions:
        print("Debug: Insufficient valid questions parsed. Using fallback.")
        fallback_questions = [
            {"question": f"How does {concepts[0]} relate to {topic}?", "options": {"A": "Provides computational power", "B": "Unrelated field", "C": "Limits processing", "D": "Manual method"}, "correct": "A"},
            {"question": f"What role does {concepts[1]} play in {topic}?", "options": {"A": "Supports infrastructure", "B": "Slows development", "C": "Increases costs", "D": "Reduces accuracy"}, "correct": "A"}
        ]
        questions.extend([q for q in fallback_questions if q["question"] not in used_questions][:num_questions - len(questions)])
    
    print(f"Question generation completed (took {time.time() - start_time:.2f}s)")
    return questions[:num_questions]

def load_or_process_documents():
    cache_file = "data/processed_content.pkl"
    raw_dir = "data/raw/"
    if os.path.exists(cache_file):
        latest_raw_time = max(os.path.getmtime(f) for f in glob.glob(f"{raw_dir}/*") if os.path.isfile(f)) if glob.glob(f"{raw_dir}/*") else 0
        if os.path.getmtime(cache_file) > latest_raw_time:
            print("Loading cached document content...")
            with open(cache_file, 'rb') as f:
                return pickle.load(f)
    print("Processing documents...")
    start_time = time.time()
    content, graphs = process_documents()
    with open(cache_file, 'wb') as f:
        pickle.dump((content, graphs), f)
    print(f"Document processing completed (took {time.time() - start_time:.2f}s)")
    return content, graphs

def assess_baseline_knowledge(llm, topic, content):
    correct = 0
    if not content:
        print(f"\nNo documents uploaded for '{topic}'. Skipping assessment.")
        return 0
    
    concepts = extract_key_concepts(content, topic)
    topic_lower = topic.lower()
    relevant_concepts = [c for c in concepts if topic_lower in c.lower()]
    if not relevant_concepts:
        print(f"\n⚠️ Warning: Uploaded documents (likely about cloud computing) do not align with the topic '{topic}'. Questions may reflect document content rather than the specified topic.")
    
    questions = generate_questions_from_concepts(llm, concepts, topic, 0)
    print(f"\nAssessing your baseline knowledge of {topic}:")
    for q in questions:
        print(f"\nQuestion: {q['question']}")
        for opt, text in q["options"].items():
            print(f"{opt}) {text}")
        user_answer = input("Your answer (A/B/C/D): ").strip().upper()
        correct_answer = q["correct"]
        if user_answer == correct_answer:
            correct += 1
            print("Correct!")
        else:
            print(f"Incorrect. The correct answer is '{correct_answer}' ({q['options'][correct_answer]}).")
    
    score = (correct / len(questions)) * 100
    print(f"Baseline knowledge score for {topic}: {score}%")
    return score

def personalize_learning(llm, topic, style, score, concepts):
    mind_map = generate_mind_map(concepts, topic)
    print("\nGenerated Mind Map:")
    print(mind_map)
    
    questions = generate_questions_from_concepts(llm, concepts, topic, score)
    print(f"\nPersonalized follow-up questions for your {VARK_CONTENT[style]['type']} learning style:")
    correct = 0
    for q in questions:
        print(f"\nQuestion: {q['question']}")
        for opt, text in q["options"].items():
            print(f"{opt}) {text}")
        user_answer = input("Your answer (A/B/C/D): ").strip().upper()
        correct_answer = q["correct"]
        if user_answer == correct_answer:
            correct += 1
            print("Correct!")
        else:
            print(f"Incorrect. The correct answer is '{correct_answer}' ({q['options'][correct_answer]}).")
    follow_up_score = (correct / len(questions)) * 100
    print(f"Follow-up score: {follow_up_score}%")
    
    resources = search_web(topic, style)
    print(f"\nRecommended {VARK_CONTENT[style]['type']} resources for {topic}:")
    for i, res in enumerate(resources, 1):
        print(f"{i}. {res['title']} - {res['url']}\n   {res['description']}")

def update_user_profile(name, learning_style, topic, score):
    engine, Session = setup_database()
    session = Session()
    user = session.query(UserProfile).filter_by(name=name).first()
    if not user:
        user = UserProfile(name=name, learning_style=learning_style)
        session.add(user)
    else:
        user.learning_style = learning_style
    session.commit()
    progress = Progress(user_id=user.id, subject=topic, score=score)
    session.add(progress)
    session.commit()
    print(f"Updated profile for {name} (ID: {user.id}) with style {learning_style} and score {score}%")
    session.close()
    return user.id

if __name__ == "__main__":
    llms, embeddings = setup_apis()
    if not llms.get("groq"):
        print("❌ Required LLM not available. Exiting.")
        exit(1)
    
    name = input("Enter your name: ")
    topic = input("What topic would you like to learn about? (e.g., 'General', 'Machine Learning'): ")
    style = assess_learning_style()
    print("\nPlease upload study materials to 'data/raw/' for your topic.")
    input("Press Enter once files are uploaded...")
    
    content, graphs = load_or_process_documents()
    score = assess_baseline_knowledge(llms["groq"], topic, content)
    if content:
        concepts = extract_key_concepts(content, topic)
        personalize_learning(llms["groq"], topic, style, score, concepts)
    update_user_profile(name, style, topic, score)