# test_api.py
from api_setup import setup_apis
from db_setup import setup_database, setup_vector_db
import time

def test_complete_setup():
    """Test the full setup process."""
    print("Testing database connections...")
    try:
        engine, Session = setup_database()
        session = Session()
        session.execute("SELECT 1")
        session.close()
        print("✅ Database connection successful")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
    
    print("\nTesting vector database...")
    try:
        client = setup_vector_db()
        collection = client.get_or_create_collection("test_collection")
        print("✅ Vector database connection successful")
    except Exception as e:
        print(f"❌ Vector database setup failed: {e}")
    
    print("\nTesting API connections...")
    llms, embeddings = setup_apis()
    
    if llms:
        # Test each LLM with a simple prompt
        for name, llm in llms.items():
            print(f"\nTesting {name} LLM...")
            try:
                start_time = time.time()
                if name == "groq":
                    response = llm.invoke("Generate a simple quiz question about astronomy.")
                    output = response.content
                else:
                    output = llm.invoke("Generate a simple quiz question about astronomy.")
                end_time = time.time()
                
                print(f"✅ {name} responded in {end_time - start_time:.2f} seconds")
                print(f"Sample output: {output[:150]}...")
            except Exception as e:
                print(f"❌ {name} test failed: {e}")
    else:
        print("❌ No LLMs available to test")
    
    if embeddings:
        # Test embeddings
        for name, embedding_model in embeddings.items():
            print(f"\nTesting {name} embeddings...")
            try:
                start_time = time.time()
                test_embedding = embedding_model.embed_query("What is the process of photosynthesis?")
                end_time = time.time()
                
                print(f"✅ {name} embeddings generated in {end_time - start_time:.2f} seconds")
                print(f"Embedding dimensions: {len(test_embedding)}")
            except Exception as e:
                print(f"❌ {name} embeddings test failed: {e}")
    else:
        print("❌ No embedding models available to test")

if __name__ == "__main__":
    print("Running comprehensive setup test...\n")
    test_complete_setup()
    print("\nTest complete!") # All the API tests should pass successfully.