#!/usr/bin/env python3
"""
Chunk-based translation runner that translates each chunk separately and merges at the end.
"""

import os
import sys
import time
from src.chunk_translator import ChunkTranslator
from src.chunk_merger import ChunkMerger
from src.config import load_config

def main():
    try:
        # Load configuration
        config = load_config()
        
        target_lang = config.target_language
        chunks_dir = config.chunks_dir
        output_file = config.get_output_filename()
        format_output = config.format_output
        
        print(" CHUNK-BASED TRANSLATION SYSTEM")
        print("=" * 60)
        print(f" Target Language: {target_lang}")
        print(f" Source Chunks: {chunks_dir}")
        print(f" Final Output: {output_file}")
        print(f" Format Output: {format_output}")
        print("=" * 60)
        
        # Initialize chunk translator
        translator = ChunkTranslator("translated_chunks")
        
        # Check if chunks already exist
        existing_chunks = translator.get_translated_files()
        if existing_chunks:
            print(f" Found {len(existing_chunks)} existing translated chunks")
            response = input("Continue with existing chunks? (y/N): ").strip().lower()
            if response != 'y':
                print("🧹 Clearing existing chunks...")
                translator.clear_translated_chunks()
                translator.progress_tracker.clear_progress()
        
        # Translate all chunks separately
        print("\n STEP 1: TRANSLATING CHUNKS SEPARATELY")
        print("-" * 60)
        
        start_time = time.time()
        results = translator.translate_all_chunks(
            chunks_dir=chunks_dir,
            target_lang=target_lang,
            format_output=format_output,
            max_chunks=config.num_chunks,
            max_tokens=config.max_tokens,
            temperature=config.temperature
        )
        translation_time = time.time() - start_time
        
        # Check if translation was successful
        successful_chunks = sum(1 for r in results if r["success"])
        if successful_chunks == 0:
            print("No chunks were translated successfully!")
            sys.exit(1)
        
        print(f"\n✅ Translation completed: {successful_chunks} chunks")
        
        # Merge chunks
        print("\n STEP 2: MERGING CHUNKS INTO FINAL BOOK")
        print("-" * 60)
        
        merger = ChunkMerger("translated_chunks")
        
        # Validate chunks before merging
        validation = merger.validate_chunks()
        if not validation["valid"]:
            print("Warning: Chunk validation failed!")
            if validation["missing_chunks"]:
                print(f"   Missing chunks: {validation['missing_chunks']}")
            if validation["extra_chunks"]:
                print(f"   Extra chunks: {validation['extra_chunks']}")
            
            response = input("Continue with merge anyway? (y/N): ").strip().lower()
            if response != 'y':
                print("Merge cancelled")
                sys.exit(1)
        
        # Perform merge
        merge_start = time.time()
        merge_stats = merger.merge_chunks(output_file, add_chapter_breaks=True)
        merge_time = time.time() - start_time - translation_time
        
        # Final statistics
        total_time = time.time() - start_time
        
        print(f"\n CHUNK-BASED TRANSLATION COMPLETE!")
        print("=" * 60)
        print(f"FINAL STATISTICS:")
        print(f"   • Total chunks processed: {len(results)}")
        print(f"   • Successful translations: {successful_chunks}")
        print(f"   • Failed translations: {len(results) - successful_chunks}")
        print(f"   • Translation time: {translation_time/60:.1f} minutes")
        print(f"   • Merge time: {merge_time:.1f} seconds")
        print(f"   • Total time: {total_time/60:.1f} minutes")
        print(f"   • Final book size: {merge_stats['total_characters']:,} characters")
        print(f"   • Output file: {output_file}")
        print()
        
        # Show chunk directory info
        print("📁 CHUNK FILES:")
        print(f"   • Translated chunks directory: translated_chunks/")
        print(f"   • Individual chunk files: {len(translator.get_translated_files())}")
        print(f"   • Final merged book: {output_file}")
        print()
        
        if len(results) - successful_chunks > 0:
            print(" Failed chunks (can be retried individually):")
            for result in results:
                if not result["success"]:
                    print(f"   • {result['filename']}: {result['error']}")
            print()
        
        print("💡 You can now:")
        print("   • View individual translated chunks in 'translated_chunks/'")
        print("   • Re-translate specific chunks if needed")
        print("   • Re-merge chunks with different options")
        print("   • Delete 'translated_chunks/' directory to save space")
        
    except KeyboardInterrupt:
        print(f"\n Translation interrupted by user")
        print("💡 Individual chunk files are saved in 'translated_chunks/'")
        print("💡 You can resume by running the script again")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
