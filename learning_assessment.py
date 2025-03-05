# learning_assessment.py
from db_setup import setup_database, UserProfile, Progress
from sqlalchemy.orm import Session
from api_setup import setup_apis
from content_processing import process_documents
import os
from collections import Counter
import re

# VARK Questionnaire
VARK_QUESTIONS = [
    {
        "question": "You need to learn a new skill. How do you prefer to start?",
        "options": {
            "V": "Watch a video or see diagrams",
            "A": "Listen to an explanation or podcast",
            "R": "Read instructions or a manual",
            "K": "Try it hands-on with guidance"
        }
    },
    {
        "question": "When remembering something, what helps most?",
        "options": {
            "V": "Pictures or visuals",
            "A": "Hearing it spoken",
            "R": "Writing it down or reading it",
            "K": "Doing it physically"
        }
    }
]

def assess_learning_style():
    """Conduct a simple VARK assessment."""
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
    """Extract key concepts from document content, prioritizing topic relevance."""
    all_text = " ".join(content.values()).lower()
    words = re.findall(r'\b\w+\b', all_text)
    bigrams = [f"{words[i]} {words[i+1]}" for i in range(len(words)-1) if all(len(w) > 3 and w.isalpha() for w in [words[i], words[i+1]])]
    single_words = [word for word in words if len(word) > 3 and word.isalpha()]
    
    stop_words = {"this", "that", "with", "from", "which", "about", "editors", "published", "university", "handbook", "borko", "furht", "armando", "escalante"}
    phrase_counts = Counter(bigrams)
    word_counts = Counter(single_words)
    
    topic_lower = topic.lower()
    # Prioritize concepts containing the topic
    topic_concepts = [c for c in phrase_counts.keys() if topic_lower in c and not any(sw in c.split() for sw in stop_words)]
    if len(topic_concepts) < num_concepts:
        additional_concepts = [w for w in word_counts.keys() if w not in stop_words and not any(sw in w for sw in stop_words)]
        topic_concepts.extend(additional_concepts)
    
    unique_concepts = list(dict.fromkeys(topic_concepts))[:num_concepts]
    print(f"Debug: Extracted key concepts: {unique_concepts}")
    return unique_concepts

def generate_questions_from_concepts(llm, concepts, topic, num_questions=2):
    """Generate MCQs from extracted concepts, ensuring topic relevance."""
    questions = []
    used_questions = set()
    
    for concept in concepts:
        if len(questions) >= num_questions:
            break
        prompt = f"For the topic '{topic}', generate a multiple-choice quiz question about the concept '{concept}' with 4 options (A, B, C, D) and one correct answer. Ensure the question is relevant to {topic} and based on typical educational content for this concept. Format as: 'Question: [q] Options: A) [a] B) [b] C) [c] D) [d] Correct: [letter]'."
        response = llm.invoke(prompt).content
        print(f"Debug: LLM response for '{concept}': {response[:100]}...")
        try:
            q_part = response.split("Question:")[1].split("Options:")[0].strip()
            opts_part = response.split("Options:")[1].split("Correct:")[0].strip()
            correct_part = response.split("Correct:")[1].strip()
            options = {}
            opts_lines = opts_part.split('\n')
            for line in opts_lines:
                if line.strip() and line[0] in "ABCD" and ")" in line:
                    letter = line[0]
                    text = line.split(")", 1)[1].strip()
                    options[letter] = text
            if q_part and len(options) == 4 and correct_part in "ABCD" and q_part not in used_questions:
                used_questions.add(q_part)
                questions.append({"question": q_part, "options": options, "correct": correct_part})
            else:
                print(f"Debug: Failed to parse response for '{concept}' - incomplete options or duplicate")
        except IndexError:
            print(f"Debug: Parsing failed for '{concept}' - using fallback")
            q_part = f"What is the role of {concept} in {topic}?"
            options = {
                "A": f"A core component of {topic}",
                "B": "An unrelated technology",
                "C": "A minor feature",
                "D": "A deprecated method"
            }
            correct_part = "A"
            if q_part not in used_questions:
                used_questions.add(q_part)
                questions.append({"question": q_part, "options": options, "correct": correct_part})
    
    # Fallback if no relevant concepts match the topic
    while len(questions) < num_questions:
        prompt = f"For the topic '{topic}', generate a multiple-choice quiz question about a fundamental aspect of {topic} with 4 options (A, B, C, D) and one correct answer, based on general knowledge of {topic}. Format as: 'Question: [q] Options: A) [a] B) [b] C) [c] D) [d] Correct: [letter]'."
        response = llm.invoke(prompt).content
        print(f"Debug: Fallback LLM response: {response[:100]}...")
        try:
            q_part = response.split("Question:")[1].split("Options:")[0].strip()
            opts_part = response.split("Options:")[1].split("Correct:")[0].strip()
            correct_part = response.split("Correct:")[1].strip()
            options = {}
            opts_lines = opts_part.split('\n')
            for line in opts_lines:
                if line.strip() and line[0] in "ABCD" and ")" in line:
                    letter = line[0]
                    text = line.split(")", 1)[1].strip()
                    options[letter] = text
            if q_part and len(options) == 4 and correct_part in "ABCD" and q_part not in used_questions:
                used_questions.add(q_part)
                questions.append({"question": q_part, "options": options, "correct": correct_part})
        except IndexError:
            q_part = f"What is a key feature of {topic}?"
            options = {
                "A": "Scalability",
                "B": "Local processing",
                "C": "Manual operations",
                "D": "Static resources"
            }
            correct_part = "A"
            if q_part not in used_questions:
                used_questions.add(q_part)
                questions.append({"question": q_part, "options": options, "correct": correct_part})
    
    return questions[:num_questions]

def assess_baseline_knowledge(llm, topic, content):
    """Assess baseline knowledge with generated multiple-choice questions."""
    correct = 0
    
    if not content:
        print(f"\nNo documents uploaded for '{topic}'. Skipping assessment.")
        return 0
    
    concepts = extract_key_concepts(content, topic)
    # Check if concepts align with topic
    topic_lower = topic.lower()
    relevant_concepts = [c for c in concepts if topic_lower in c.lower()]
    if not relevant_concepts:
        print(f"\nWarning: Uploaded documents may not align with the topic '{topic}'. Questions will be based on document content and general {topic} knowledge.")
    
    questions = generate_questions_from_concepts(llm, concepts, topic)
    print(f"\nAssessing your knowledge of {topic} with generated questions from your documents:")
    
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

def update_user_profile(name, learning_style, topic, score):
    """Store or update user profile in the database."""
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
    # Setup APIs
    llms, embeddings = setup_apis()
    if not llms.get("groq"):
        print("❌ Required LLM not available. Exiting.")
        exit(1)
    
    # User onboarding
    name = input("Enter your name: ")
    topic = input("What topic would you like to learn about? (e.g., 'General', 'Machine Learning'): ")
    
    # Assess learning style
    style = assess_learning_style()
    
    # Prompt for documents
    print("\nPlease upload study materials to 'data/raw/' for your topic.")
    input("Press Enter once files are uploaded...")
    
    # Process documents once
    content, graphs = process_documents()
    
    # Assess baseline knowledge
    score = assess_baseline_knowledge(llms["groq"], topic, content)
    
    # Update profile
    update_user_profile(name, style, topic, score)