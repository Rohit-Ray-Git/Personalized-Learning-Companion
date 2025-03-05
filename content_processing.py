# content_processing.py (unchanged from your latest working version, just confirming)
import os
from PyPDF2 import PdfReader
from docx import Document
import networkx as nx
from collections import Counter

def extract_text_from_pdf(file_path):
    """Extract text from a PDF file."""
    try:
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        return text.strip()
    except Exception as e:
        print(f"Error processing PDF {file_path}: {e}")
        return ""

def extract_text_from_docx(file_path):
    """Extract text from a DOCX file."""
    try:
        doc = Document(file_path)
        text = "\n".join([para.text for para in doc.paragraphs if para.text])
        return text.strip()
    except Exception as e:
        print(f"Error processing DOCX {file_path}: {e}")
        return ""

def extract_text_from_txt(file_path):
    """Extract text from a TXT file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read().strip()
    except Exception as e:
        print(f"Error processing TXT {file_path}: {e}")
        return ""

def process_documents(directory="data/raw"):
    """Process all supported files in the directory and build knowledge graphs."""
    supported_extensions = {".pdf", ".docx", ".txt"}
    extracted_content = {}
    knowledge_graphs = {}
    
    if not os.path.exists(directory):
        print(f"Directory {directory} not found. Creating it...")
        os.makedirs(directory)
        return extracted_content, knowledge_graphs
    
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        ext = os.path.splitext(filename)[1].lower()
        
        if ext in supported_extensions:
            print(f"Processing {filename}...")
            if ext == ".pdf":
                text = extract_text_from_pdf(file_path)
            elif ext == ".docx":
                text = extract_text_from_docx(file_path)
            elif ext == ".txt":
                text = extract_text_from_txt(file_path)
            
            if text:
                extracted_content[filename] = text
                knowledge_graphs[filename] = build_knowledge_graph(text)
                print(f"✅ Processed {filename}: {len(text)} chars, {knowledge_graphs[filename].number_of_nodes()} nodes")
            else:
                print(f"❌ No content extracted from {filename}")
    
    return extracted_content, knowledge_graphs

def build_knowledge_graph(text, max_nodes=10):
    """Create a simple knowledge graph from text."""
    words = [word.lower() for word in text.split() if len(word) > 3 and word.isalpha()]
    common_words = [word for word, count in Counter(words).most_common(max_nodes)]
    
    G = nx.Graph()
    for i, word in enumerate(common_words):
        G.add_node(word)
        if i > 0:
            G.add_edge(common_words[i-1], word)
    
    return G

if __name__ == "__main__":
    content, graphs = process_documents()
    for filename, graph in graphs.items():
        print(f"\nKnowledge graph for {filename}:")
        print(f"Nodes: {list(graph.nodes)}")
        print(f"Edges: {list(graph.edges)}")