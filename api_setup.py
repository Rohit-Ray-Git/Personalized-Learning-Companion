# api_setup.py
from groq import Groq
from langchain_groq import ChatGroq
from huggingface_hub import InferenceClient
from dotenv import load_dotenv
import os

class HuggingFaceEmbeddingWrapper:
    def __init__(self, client, model):
        self.client = client
        self.model = model
    
    def embed_query(self, text):
        embedding = self.client.feature_extraction(text, model=self.model)
        return embedding.tolist()  # Convert ndarray to list

def setup_apis():
    """Configure Groq and Huggingface APIs."""
    load_dotenv()
    
    llms = {}
    embeddings = {}
    
    # Groq API setup
    groq_api_key = os.getenv("GROQ_API_KEY")
    if groq_api_key:
        try:
            llms["groq"] = ChatGroq(
                api_key=groq_api_key,
                model="gemma2-9b-it"
            )
            print("✅ Groq API configured")
        except Exception as e:
            print(f"❌ Groq API setup failed: {e}")
    
    # Huggingface API (Embeddings)
    hf_api_key = os.getenv("HF_API_KEY")
    if hf_api_key:
        try:
            client = InferenceClient(token=hf_api_key)
            embeddings["huggingface"] = HuggingFaceEmbeddingWrapper(
                client, "sentence-transformers/all-MiniLM-L6-v2"
            )
            print("✅ Huggingface embeddings configured")
        except Exception as e:
            print(f"❌ Huggingface embeddings failed: {e}")
    
    return llms, embeddings

if __name__ == "__main__":
    llms, embeddings = setup_apis()
    if "groq" in llms:
        response = llms["groq"].invoke("Hello, generate a simple quiz question.")
        print(f"Groq response: {response.content}")
    if "huggingface" in embeddings:
        emb = embeddings["huggingface"].embed_query("Test sentence")
        print(f"Huggingface embedding length: {len(emb)}")