# main.py
import argparse
from api_setup import setup_apis
from db_setup import setup_database

def main():
    parser = argparse.ArgumentParser(description="Personalized Learning Companion Setup")
    parser.add_argument("--skip-apis", action="store_true", help="Skip API setup")
    args = parser.parse_args()

    print("=" * 50)
    print("Personalized Learning Companion - Initial Setup")
    print("=" * 50)

    # Database setup
    print("\nSetting up database...")
    engine, Session = setup_database()

    # API setup
    llms = {}
    embeddings = {}
    if not args.skip_apis:
        print("\nSetting up APIs...")
        llms, embeddings = setup_apis()
    else:
        print("\nSkipping API setup...")

    # Verification
    print("\n" + "=" * 50)
    print("Setup Verification:")
    print("=" * 50)
    print(f"Database: {'✅ Connected' if engine else '❌ Failed'}")
    print(f"LLMs: {'✅ ' + ', '.join(llms.keys()) if llms else '❌ None configured'}")
    print(f"Embeddings: {'✅ ' + ', '.join(embeddings.keys()) if embeddings else '❌ None configured'}")

    print("\nSetup complete!")

if __name__ == "__main__":
    main()

