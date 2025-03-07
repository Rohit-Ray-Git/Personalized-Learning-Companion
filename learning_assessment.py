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
import threading
import numpy as np

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

def extract_key_concepts(content, topic, embedding_model, num_concepts=5):
    print("Extracting key concepts...")
    start_time = time.time()
    all_text = " ".join(content.values()).lower()[:10000] if content else ""
    words = re.findall(r'\b\w+\b', all_text)
    bigrams = [" ".join([words[i], words[i+1]]) for i in range(len(words)-1) if all(len(w) > 3 and w.isalpha() for w in [words[i], words[i+1]])][:100]
    
    stop_words = {"this", "that", "with", "from", "which", "about", "editors", "published", "university", "handbook", "borko", "furht", "armando", "escalante", "science", "florida"}
    phrase_counts = Counter(bigrams)
    
    topic_lower = topic.lower()
    candidates = [c for c in phrase_counts.keys() if not any(sw in c.split() for sw in stop_words)]
    if not candidates and not content:
        candidates = [f"{topic_lower} {i+1}" for i in range(num_concepts)]
    
    if candidates and embedding_model:
        topic_embedding = embedding_model.embed_query(topic_lower)
        candidate_embeddings = [embedding_model.embed_query(c) for c in candidates]
        similarities = [np.dot(topic_embedding, c_emb) / (np.linalg.norm(topic_embedding) * np.linalg.norm(c_emb)) for c_emb in candidate_embeddings]
        ranked = sorted(zip(candidates, similarities), key=lambda x: x[1], reverse=True)
        unique_concepts = [c for c, _ in ranked][:num_concepts]
    else:
        unique_concepts = list(dict.fromkeys(candidates))[:num_concepts]
    
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

def search_web(topic, style, grok_instance):
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
        print(f"DuckDuckGo search failed: {e}. Using Grok's mock X search...")
        formatted_results = [
            {"title": f"X Post on {topic}", "url": "https://x.com", "description": f"A recent post: 'Loving this {VARK_CONTENT[style]['type']} {topic} tutorial!'"},
            {"title": f"X Post on {topic}", "url": "https://x.com", "description": f"Check out this {VARK_CONTENT[style]['keywords'][0]} on {topic}!"},
            {"title": f"X Post on {topic}", "url": "https://x.com", "description": f"Someone shared a great {VARK_CONTENT[style]['type']} resource for {topic}."}
        ]
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

def generate_questions_from_concepts(llm, concepts, topic, score, num_questions=2, used_questions=None):
    if used_questions is None:
        used_questions = set()
    print("Generating questions...")
    start_time = time.time()
    questions = []
    
    difficulty = "basic" if score < 50 else "intermediate" if score <= 75 else "advanced"
    prompt = f"For the topic '{topic}', generate {num_questions} {difficulty}-level multiple-choice quiz questions about the following concepts: {', '.join(concepts)}. Each question should have 4 options (A, B, C, D) and one correct answer. Avoid repeating these questions: {', '.join(used_questions) if used_questions else 'none'}. Ensure relevance to {topic}. Format each as: 'Question: [q] Options: A) [a] B) [b] C) [c] D) [d] Correct: [letter]' separated by newlines."
    try:
        response = invoke_llm_with_timeout(llm, prompt)
        if response is None:
            raise Exception("Timeout occurred")
        debug_response = re.sub(r"Correct: [A-D]\)?\s*(?=\n\n|$)", "", response, flags=re.DOTALL).strip()
        print(f"Debug: LLM batch questions (answers hidden): {debug_response}")
    except Exception as e:
        print(f"LLM invocation failed: {e}. Using fallback questions.")
        response = (
            f"Question: How does {concepts[0]} enable {topic}?\nOptions: A) Scalability and flexibility B) Increased hardware costs C) Limited access D) Manual processing\nCorrect: A\n\n"
            f"Question: What role does {concepts[1 if len(concepts) > 1 else 0]} play in {topic}?\nOptions: A) Algorithm development B) Hardware design C) Data storage D) Weather prediction\nCorrect: A"
        )
        debug_response = re.sub(r"Correct: [A-D]\)?\s*(?=\n\n|$)", "", response, flags=re.DOTALL).strip()
        print(f"Debug: Fallback questions (answers hidden): {debug_response}")
    
    question_pattern = re.compile(r"(?:\*\*Question(?: \d+)?:\*\*|Question:)\s*(.+?)\s*(?:\n\s*Options:|\nOptions:)\s*(.+?)\s*(?:\n\s*Correct:|\nCorrect:)\s*([A-D])\)?\s*(?:\n|$)", re.DOTALL)
    matches = question_pattern.findall(response)
    if not matches:
        print(f"Debug: No questions parsed from response. Raw response: {response}")
    
    for i, match in enumerate(matches):
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
        else:
            print(f"Debug: Failed to parse match {i}: q='{q_part}', opts={len(options)}, correct='{correct_part}'")
    
    if len(questions) < num_questions:
        print(f"Debug: Only {len(questions)} valid questions parsed. Using fallback.")
        fallback_questions = [
            {"question": f"How does {concepts[0]} enable {topic}?", "options": {"A": "Scalability and flexibility", "B": "Increased hardware costs", "C": "Limited access", "D": "Manual processing"}, "correct": "A"},
            {"question": f"What role does {concepts[1 if len(concepts) > 1 else 0]} play in {topic}?", "options": {"A": "Algorithm development", "B": "Hardware design", "C": "Data storage", "D": "Weather prediction"}, "correct": "A"}
        ]
        questions.extend([q for q in fallback_questions if q["question"] not in used_questions][:num_questions - len(questions)])
    
    print(f"Question generation completed (took {time.time() - start_time:.2f}s)")
    return questions[:num_questions], used_questions

def load_or_process_documents(force_reprocess=False):
    cache_file = "data/processed_content.pkl"
    raw_dir = "data/raw/"
    if force_reprocess or not os.path.exists(cache_file) or any(os.path.getmtime(f) > os.path.getmtime(cache_file) for f in glob.glob(f"{raw_dir}/*") if os.path.isfile(f)):
        print("Processing documents...")
        start_time = time.time()
        content, graphs = process_documents()
        with open(cache_file, 'wb') as f:
            pickle.dump((content, graphs), f)
        print(f"Document processing completed (took {time.time() - start_time:.2f}s)")
        return content, graphs
    print("Loading cached document content...")
    with open(cache_file, 'rb') as f:
        return pickle.load(f)

def assess_knowledge(llm, topic, content, embedding_model, score, style, phase="Baseline", used_questions=None):
    correct = 0
    if not content:
        print(f"\nNo documents uploaded for '{topic}'. Using topic-based fallback concepts.")
    
    concepts = extract_key_concepts(content, topic, embedding_model)
    topic_lower = topic.lower()
    relevant_concepts = [c for c in concepts if topic_lower in c.lower()]
    if not relevant_concepts:
        print(f"\n⚠️ Warning: Uploaded documents (if any) do not align with '{topic}'. Questions may be generic.")
        confirm = input(f"Concepts extracted: {concepts}. Do these look relevant to '{topic}'? (yes/no): ").lower()
        if confirm != "yes":
            print("Please upload relevant documents to 'data/raw/' and press Enter to retry...")
            input()
            content, _ = load_or_process_documents(force_reprocess=True)
            concepts = extract_key_concepts(content, topic, embedding_model)
    
    questions, used_questions = generate_questions_from_concepts(llm, concepts, topic, score, used_questions=used_questions)
    difficulty = "basic" if score < 50 else "intermediate" if score <= 75 else "advanced"
    print(f"\nAssessing your {phase.lower()} knowledge of {topic} ({difficulty.capitalize()} Level):")
    incorrect_concepts = []
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
            for concept in concepts:
                if concept.lower() in q["question"].lower():
                    incorrect_concepts.append(concept)
                    break
    
    score = (correct / len(questions)) * 100
    print(f"{phase} knowledge score for {topic}: {score}%")
    
    if style == "V":
        print("Would you like me to generate a diagram of these concepts? (yes/no): ")
        if input().lower() == "yes":
            print(f"[Mock Image]: A diagram showing '{topic}' with nodes for {', '.join(concepts)} connected by edges.")
    
    return score, used_questions, incorrect_concepts

def personalize_learning(llm, topic, style, baseline_score, content, embedding_model, grok_instance):
    used_questions = set()
    score = baseline_score
    concepts = extract_key_concepts(content, topic, embedding_model)
    
    while True:
        mind_map = generate_mind_map(concepts, topic)
        print("\nGenerated Mind Map:")
        print(mind_map)
        
        phase_score, used_questions, incorrect_concepts = assess_knowledge(llm, topic, content, embedding_model, score, style, phase="Follow-up", used_questions=used_questions)
        score = max(score, phase_score)
        
        resources = search_web(topic, style, grok_instance)
        print(f"\nRecommended {VARK_CONTENT[style]['type']} resources for {topic}:")
        for i, res in enumerate(resources, 1):
            print(f"{i}. {res['title']} - {res['url']}\n   {res['description']}")
        
        if phase_score == 100 or not incorrect_concepts:
            print("\nGreat job! You've mastered this set.")
            review = input("Would you like to review the concepts again? (yes/no): ").lower()
            if review == "yes":
                phase_score, used_questions, incorrect_concepts = assess_knowledge(llm, topic, content, embedding_model, score, style, phase="Review", used_questions=used_questions)
            break
        else:
            retry = input(f"\nYou scored {phase_score}%. Would you like to retry questions on {', '.join(incorrect_concepts)}? (yes/no): ").lower()
            if retry != "yes":
                break
            concepts = incorrect_concepts
    
    return score

def review_progress(name):
    engine, Session = setup_database()
    session = Session()
    user = session.query(UserProfile).filter_by(name=name).first()
    if not user:
        print("No progress found for this user yet.")
        return
    print(f"\nProgress Review for {name}:")
    progresses = session.query(Progress).filter_by(user_id=user.id).order_by(Progress.last_updated).all()
    for p in progresses:
        print(f"Topic: {p.subject}, Phase: {p.phase}, Score: {p.score}%, Updated: {p.last_updated}")
    weak_areas = [p.subject for p in progresses if p.score < 75]
    if weak_areas:
        print(f"Suggested topics to revisit: {', '.join(set(weak_areas))}")
    session.close()

def update_user_profile(name, learning_style, topic, baseline_score, final_score):
    engine, Session = setup_database()
    session = Session()
    user = session.query(UserProfile).filter_by(name=name).first()
    if not user:
        user = UserProfile(name=name, learning_style=learning_style)
        session.add(user)
    else:
        user.learning_style = learning_style
    session.commit()
    
    baseline_progress = Progress(user_id=user.id, subject=topic, score=baseline_score, phase="baseline")
    final_progress = Progress(user_id=user.id, subject=topic, score=final_score, phase="follow-up")
    session.add(baseline_progress)
    session.add(final_progress)
    session.commit()
    
    print(f"Updated profile for {name} (ID: {user.id}) with style {learning_style}, baseline score {baseline_score}%, final score {final_score}%")
    session.close()
    return user.id

if __name__ == "__main__":
    llms, embeddings = setup_apis()
    if not llms.get("groq") or not embeddings.get("huggingface"):
        print("❌ Required APIs not available. Exiting.")
        exit(1)
    
    name = input("Enter your name: ")
    review_progress(name)
    topic = input("What topic would you like to learn about? (e.g., 'General', 'Machine Learning'): ")
    style = assess_learning_style()
    print("\nPlease upload study materials to 'data/raw/' for your topic (optional).")
    input("Press Enter once files are uploaded or to proceed without files...")
    
    content, graphs = load_or_process_documents()
    embedding_model = embeddings["huggingface"]
    baseline_score, used_questions, _ = assess_knowledge(llms["groq"], topic, content, embedding_model, 0, style, phase="Baseline")
    final_score = personalize_learning(llms["groq"], topic, style, baseline_score, content, embedding_model, llms["groq"])
    update_user_profile(name, style, topic, baseline_score, final_score)