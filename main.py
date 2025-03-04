import os
import argparse
from api_setup import setup_apis
from src.data.db_setup import setup_database, setup_vector_db

def main():
    """Main entry point for project setup."""
    parser = argparse.ArgumentParser(description='Personalized Learning Companion Setup')
    parser.add_argument('--skip-apis', action='store_true', help='Skip API setup')
    args = parser.parse_args()
    
    print("=" * 50)
    print("Personalized Learning Companion - Initial Setup")
    print("=" * 50)
    
    # Set up databases
    print("\nSetting up databases...")
    engine, Session = setup_database()
    vector_db = setup_vector_db()
    
    # Set up API connections (if not skipped)
    llms = {}
    embeddings = {}
    if not args.skip_apis:
        print("\nSetting up API connections...")
        llms, embeddings = setup_apis()
    else:
        print("\nSkipping API setup...")
    
    # 3. Verify setup
    print("\n" + "=" * 50)
    print("Setup Verification:")
    print("=" * 50)
    
    print(f"Database: {'✅ Connected' if engine else '❌ Failed'}")
    print(f"Vector DB: {'✅ Connected' if vector_db else '❌ Failed'}")
    print(f"LLMs: {'✅ ' + ', '.join(llms.keys()) if llms else '❌ None configured'}")
    print(f"Embeddings: {'✅ ' + ', '.join(embeddings.keys()) if embeddings else '❌ None configured'}")
    
    print("\n" + "=" * 50)
    print("Initial setup complete!")
    print("=" * 50)
    print("\nNext steps:")
    print("1. Add your study materials to the data/raw directory")
    print("2. Run the document processing pipeline")
    print("3. Create a test user and start learning!")

if __name__ == "__main__":
    main()