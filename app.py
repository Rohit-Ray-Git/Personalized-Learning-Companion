# app.py
from flask import Flask, render_template, request, redirect, url_for, send_from_directory
from learning_assessment import (
    VARK_QUESTIONS,
    assess_learning_style, extract_key_concepts, generate_mind_map,
    search_web, generate_questions_from_concepts, load_or_process_documents,
    assess_knowledge, personalize_learning, review_progress, update_user_profile
)
from api_setup import setup_apis
import os

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'data/raw/'
app.config['STATIC_FOLDER'] = 'static/'

llms, embeddings = setup_apis()
if not llms.get("groq") or not embeddings.get("huggingface"):
    raise Exception("Required APIs not available.")
embedding_model = embeddings["huggingface"]
grok_instance = llms["groq"]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start', methods=['GET', 'POST'])
def start_learning():
    if request.method == 'POST':
        name = request.form.get('name')
        topic = request.form.get('topic')
        global user_data
        user_data = {'name': name, 'topic': topic, 'step': 'vark', 'scores': {"V": 0, "A": 0, "R": 0, "K": 0}, 'used_questions': set(), 'vark_q': 0}
        return redirect(url_for('learn'))
    return render_template('learn.html', step='start')

@app.route('/learn', methods=['GET', 'POST'])
def learn():
    global user_data
    if 'user_data' not in globals():
        return redirect(url_for('start_learning'))
    
    if request.method == 'POST':
        if user_data['step'] == 'vark':
            choice = request.form.get('choice')
            if choice in user_data['scores']:
                user_data['scores'][choice] += 1
            user_data['vark_q'] += 1
            if user_data['vark_q'] >= len(VARK_QUESTIONS):
                style = max(user_data['scores'], key=user_data['scores'].get)
                user_data['style'] = style
                user_data['step'] = 'upload'
            return redirect(url_for('learn'))
        
        elif user_data['step'] == 'upload':
            force_reprocess = False
            if 'file' in request.files and request.files['file'].filename:
                file = request.files['file']
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], file.filename))
                force_reprocess = True  # Only reprocess if a new file is uploaded
            content, _ = load_or_process_documents(force_reprocess=force_reprocess)
            user_data['content'] = content
            user_data['step'] = 'baseline'
            return redirect(url_for('quiz'))
        
        elif user_data['step'] == 'follow-up' and 'retry' in request.form:
            user_data['concepts'] = user_data['incorrect_concepts']
            return redirect(url_for('quiz'))
    
    if user_data['step'] == 'vark':
        q_index = user_data['vark_q']
        if q_index < len(VARK_QUESTIONS):
            question = VARK_QUESTIONS[q_index]['question']
            options = VARK_QUESTIONS[q_index]['options']
            return render_template('learn.html', step='vark', question=question, options=options)
        else:
            return redirect(url_for('learn'))
    
    elif user_data['step'] == 'upload':
        return render_template('learn.html', step='upload')
    
    elif user_data['step'] == 'follow-up':
        return redirect(url_for('quiz'))
    
    elif user_data['step'] == 'done':
        review_progress(user_data['name'])
        update_user_profile(user_data['name'], user_data['style'], user_data['topic'], user_data['baseline_score'], user_data['final_score'])
        resources = search_web(user_data['topic'], user_data['style'], grok_instance)
        return render_template('learn.html', step='done', name=user_data['name'], topic=user_data['topic'], baseline_score=user_data['baseline_score'], final_score=user_data['final_score'], resources=resources)
    
    return render_template('learn.html', step=user_data['step'], error="Unexpected step, please restart.")

@app.route('/quiz', methods=['GET', 'POST'])
def quiz():
    global user_data
    if 'user_data' not in globals() or user_data['step'] not in ['baseline', 'follow-up']:
        return redirect(url_for('start_learning'))
    
    if request.method == 'POST':
        user_answer = request.form.get('answer')
        q_index = user_data['q_index']
        correct_answer = user_data['questions'][q_index]['correct']
        if user_answer == correct_answer:
            user_data['correct'] += 1
        else:
            for concept in user_data['concepts']:
                if concept.lower() in user_data['questions'][q_index]['question'].lower():
                    user_data['incorrect_concepts'].append(concept)
                    break
        
        user_data['q_index'] += 1
        if user_data['q_index'] >= len(user_data['questions']):
            score = (user_data['correct'] / len(user_data['questions'])) * 100
            if user_data['step'] == 'baseline':
                user_data['baseline_score'] = score
                user_data['step'] = 'follow-up'
                print(f"Baseline completed: Score {score}%")
            else:
                user_data['final_score'] = score
                user_data['step'] = 'done'
                print(f"Follow-up completed: Score {score}%")
            user_data['q_index'] = 0
            user_data['correct'] = 0
            return redirect(url_for('learn'))
        return redirect(url_for('quiz'))
    
    if 'questions' not in user_data or user_data['q_index'] == 0:
        concepts = extract_key_concepts(user_data['content'], user_data['topic'], embedding_model)
        user_data['concepts'] = concepts
        user_data['incorrect_concepts'] = []
        questions, user_data['used_questions'] = generate_questions_from_concepts(grok_instance, concepts, user_data['topic'], user_data.get('baseline_score', 0), used_questions=user_data['used_questions'])
        user_data['questions'] = questions
        user_data['q_index'] = 0
        user_data['correct'] = 0
        generate_mind_map(concepts, user_data['topic'])
    
    q = user_data['questions'][user_data['q_index']]
    return render_template('quiz.html', question=q['question'], options=q['options'], phase=user_data['step'].capitalize())

@app.route('/progress')
def progress():
    name = request.args.get('name')
    if not name:
        return render_template('progress.html', error="Please provide a name.")
    import io
    import sys
    old_stdout = sys.stdout
    sys.stdout = io.StringIO()
    review_progress(name)
    progress_text = sys.stdout.getvalue()
    sys.stdout = old_stdout
    return render_template('progress.html', progress=progress_text)

@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory(app.config['STATIC_FOLDER'], filename)

if __name__ == "__main__":
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    if not os.path.exists(app.config['STATIC_FOLDER']):
        os.makedirs(app.config['STATIC_FOLDER'])
    app.run(debug=True)