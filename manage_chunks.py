#!/usr/bin/env python3
"""
Utility to manage chunk-based translation system.
"""

import sys
import os
from src.chunk_translator import ChunkTranslator
from src.chunk_merger import ChunkMerger

def list_chunks():
    """List all translated chunks."""
    merger = ChunkMerger()
    merger.list_chunks()

def clear_chunks():
    """Clear all translated chunks."""
    translator = ChunkTranslator()
    
    existing_chunks = translator.get_translated_files()
    if not existing_chunks:
        print("📁 No translated chunks found")
        return
    
    print(f"⚠️  This will delete {len(existing_chunks)} translated chunk files")
    response = input("Are you sure? (y/N): ").strip().lower()
    
    if response == 'y':
        translator.clear_translated_chunks()
        translator.progress_tracker.clear_progress()
        print("✅ All translated chunks cleared")
    else:
        print("❌ Cancelled")

def validate_chunks():
    """Validate translated chunks."""
    merger = ChunkMerger()
    validation = merger.validate_chunks()
    
    if validation["valid"]:
        print("✅ All chunks are valid and ready for merging")
        print(f"📊 Total chunks: {validation['total_chunks']}")
    else:
        print("❌ Chunk validation failed!")
        if validation["missing_chunks"]:
            print(f"   Missing chunks: {validation['missing_chunks']}")
        if validation["extra_chunks"]:
            print(f"   Extra chunks: {validation['extra_chunks']}")

def merge_only(output_file: str = None):
    """Merge existing chunks without translating."""
    from src.config import load_config
    
    config = load_config()
    if not output_file:
        output_file = config.get_output_filename()
    
    merger = ChunkMerger()
    
    # Validate first
    validation = merger.validate_chunks()
    if not validation["valid"]:
        print("❌ Cannot merge: chunk validation failed!")
        return
    
    print(f"🔄 Merging {validation['total_chunks']} chunks to {output_file}")
    
    try:
        merge_stats = merger.merge_chunks(output_file, add_chapter_breaks=True)
        print("✅ Merge completed successfully!")
    except Exception as e:
        print(f"❌ Merge failed: {e}")

def main():
    if len(sys.argv) < 2:
        print("📄 Chunk Management Utility")
        print("=" * 40)
        print("Usage:")
        print("  python manage_chunks.py list     - List all translated chunks")
        print("  python manage_chunks.py clear    - Clear all translated chunks")
        print("  python manage_chunks.py validate - Validate chunk integrity")
        print("  python manage_chunks.py merge    - Merge chunks to final book")
        print("  python manage_chunks.py help     - Show this help")
        return
    
    command = sys.argv[1].lower()
    
    if command == "list":
        list_chunks()
    elif command == "clear":
        clear_chunks()
    elif command == "validate":
        validate_chunks()
    elif command == "merge":
        output_file = sys.argv[2] if len(sys.argv) > 2 else None
        merge_only(output_file)
    elif command == "help":
        print("📄 Chunk Management Utility")
        print("=" * 40)
        print("Commands:")
        print("  list     - List all translated chunks with sizes")
        print("  clear    - Delete all translated chunk files")
        print("  validate - Check chunk integrity and completeness")
        print("  merge    - Merge chunks into final book")
        print("  help     - Show this help message")
        print()
        print("Examples:")
        print("  python manage_chunks.py list")
        print("  python manage_chunks.py clear")
        print("  python manage_chunks.py validate")
        print("  python manage_chunks.py merge")
        print("  python manage_chunks.py merge output/custom_book.txt")
    else:
        print(f"❌ Unknown command: {command}")
        print("💡 Use 'python manage_chunks.py help' for usage information.")

if __name__ == "__main__":
    main()
