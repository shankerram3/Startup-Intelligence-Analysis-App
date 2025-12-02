#!/usr/bin/env python3
"""
Script to process the Glīd article specifically
This bypasses the max_articles limit and processes just this one article
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from entity_extractor import process_articles_directory
from dotenv import load_dotenv
import os

load_dotenv()

def main():
    # Find the Glīd article
    glid_file = project_root / "data" / "articles" / "articles" / "2025-11" / "27" / "tc_41ecf52e3bee.json"
    
    if not glid_file.exists():
        print(f"❌ Article file not found: {glid_file}")
        return False
    
    print("=" * 80)
    print("Processing Glīd Article")
    print("=" * 80)
    print(f"Article file: {glid_file}")
    print()
    
    # Process just this article by creating a temporary directory with only this file
    # Or we can process the whole directory but force this one
    articles_dir = str(project_root / "data" / "articles")
    output_dir = str(project_root / "data" / "processing")
    
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        print("❌ OPENAI_API_KEY not set in .env")
        return False
    
    # Process with resume=False to force processing, but we'll manually check
    # Actually, better to process with resume=True but ensure this article is included
    print("Processing article...")
    extractions = process_articles_directory(
        articles_dir=articles_dir,
        output_dir=output_dir,
        openai_api_key=openai_api_key,
        max_articles=None,  # No limit
        resume=True,  # Still resume, but this article isn't processed yet
        validate_data=True,
    )
    
    if extractions:
        # Check if Glīd article is in extractions
        glid_found = False
        for ext in extractions:
            article_id = ext.get("article_metadata", {}).get("article_id")
            if article_id == "41ecf52e3bee":
                glid_found = True
                print(f"✅ Glīd article processed!")
                print(f"   Entities extracted: {len(ext.get('entities', []))}")
                print(f"   Relationships: {len(ext.get('relationships', []))}")
                break
        
        if not glid_found:
            print("⚠️  Article not found in extractions (may have been filtered or failed)")
            return False
        
        return True
    else:
        print("❌ No extractions returned")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

