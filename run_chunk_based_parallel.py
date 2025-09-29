#!/usr/bin/env python3
"""
Parallel chunk-based translation runner that processes multiple chunks simultaneously.
"""

import os
import sys
import time
import asyncio
import concurrent.futures
from datetime import datetime
from src.chunk_translator import ChunkTranslator
from src.chunk_merger import ChunkMerger
from src.config import load_config

class ParallelChunkTranslator(ChunkTranslator):
    """Parallel version of ChunkTranslator that processes multiple chunks simultaneously."""
    
    def __init__(self, output_dir: str = "translated_chunks", max_workers: int = 4):
        super().__init__(output_dir)
        self.max_workers = max_workers
        self.semaphore = asyncio.Semaphore(max_workers)
    
    def translate_chunk_file_sync(self, chunk_filepath: str, target_lang: str, format_output: bool = True, max_tokens: int = 8000, temperature: float = 0.2) -> dict:
        """Synchronous version of translate_chunk_file for thread pool execution."""
        chunk_start = time.time()
        filename = os.path.basename(chunk_filepath)
        
        try:
            # Read chunk
            with open(chunk_filepath, "r", encoding="utf-8") as f:
                chunk_text = f.read()
            
            print(f" [Thread] Translating {filename}...")
            
            # Import here to avoid circular imports
            from src.chunk_translator import translate_chunk
            from src.formatter import format_book_output
            
            # Translate
            translation = translate_chunk(chunk_text, target_lang, max_tokens, temperature)
            
            # Format if enabled
            if format_output:
                formatted_translation = format_book_output(translation)
                final_output = formatted_translation
            else:
                final_output = translation
            
            # Save as separate file
            translated_filename = f"translated_{filename}"
            translated_filepath = os.path.join(self.output_dir, translated_filename)
            
            with open(translated_filepath, "w", encoding="utf-8") as f:
                f.write(final_output)
            
            chunk_end = time.time()
            duration = chunk_end - chunk_start
            
            result = {
                "success": True,
                "filename": filename,
                "translated_filename": translated_filename,
                "translated_filepath": translated_filepath,
                "input_size": len(chunk_text),
                "output_size": len(final_output),
                "duration": duration,
                "translation": final_output
            }
            
            print(f" [Thread] {filename} → {translated_filename} ({duration:.1f}s)")
            return result
            
        except Exception as e:
            chunk_end = time.time()
            duration = chunk_end - chunk_start
            
            result = {
                "success": False,
                "filename": filename,
                "error": str(e),
                "duration": duration
            }
            
            print(f"[Thread] {filename} failed: {str(e)}")
            return result
    
    def translate_all_chunks_parallel(self, chunks_dir: str, target_lang: str, format_output: bool = True, max_chunks: int = None, max_tokens: int = 8000, temperature: float = 0.2):
        """Translate all chunks in parallel using thread pool."""
        
        # Get chunk files
        if not os.path.exists(chunks_dir):
            raise FileNotFoundError(f"Chunks directory '{chunks_dir}' not found!")
        
        chunk_files = sorted([f for f in os.listdir(chunks_dir) if f.endswith(".txt")])
        
        if not chunk_files:
            raise ValueError(f"No chunk files found in '{chunks_dir}'!")
        
        # Limit chunks if specified
        if max_chunks:
            chunk_files = chunk_files[:max_chunks]
        
        total_chunks = len(chunk_files)
        
        print(f" PARALLEL TRANSLATION SYSTEM ({self.max_workers} workers)")
        print("=" * 60)
        print(f" Target Language: {target_lang}")
        print(f" Chunks Directory: {chunks_dir}")
        print(f"Output Directory: {self.output_dir}")
        print(f" Format Output: {format_output}")
        print(f"Max Workers: {self.max_workers}")
        print("=" * 60)
        
        # Start progress tracking
        self.progress_tracker.start_session(
            target_lang, 
            total_chunks, 
            self.output_dir
        )
        
        start_time = time.time()
        results = []
        
        # Prepare chunk tasks
        chunk_tasks = []
        for filename in chunk_files:
            chunk_filepath = os.path.join(chunks_dir, filename)
            
            # Check if already translated
            translated_filename = f"translated_{filename}"
            translated_filepath = os.path.join(self.output_dir, translated_filename)
            
            if os.path.exists(translated_filepath):
                print(f"Skipping {filename} (already translated)")
                # Read existing translation
                with open(translated_filepath, "r", encoding="utf-8") as f:
                    existing_translation = f.read()
                
                result = {
                    "success": True,
                    "filename": filename,
                    "translated_filename": translated_filename,
                    "translated_filepath": translated_filepath,
                    "output_size": len(existing_translation),
                    "duration": 0,
                    "translation": existing_translation,
                    "skipped": True
                }
                results.append(result)
            else:
                chunk_tasks.append((chunk_filepath, target_lang, format_output, max_tokens, temperature))
        
        # Execute parallel translation
        if chunk_tasks:
            print(f"\n Processing {len(chunk_tasks)} chunks in parallel...")
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # Submit all tasks
                future_to_chunk = {
                    executor.submit(
                        self.translate_chunk_file_sync, 
                        chunk_filepath, 
                        target_lang, 
                        format_output, 
                        max_tokens, 
                        temperature
                    ): chunk_filepath
                    for chunk_filepath, target_lang, format_output, max_tokens, temperature in chunk_tasks
                }
                
                # Collect results as they complete
                for i, future in enumerate(concurrent.futures.as_completed(future_to_chunk)):
                    chunk_filepath = future_to_chunk[future]
                    try:
                        result = future.result()
                        results.append(result)
                        
                        # Update progress
                        if result["success"]:
                            self.progress_tracker.mark_chunk_completed(
                                result["filename"], 
                                result["output_size"], 
                                result["duration"]
                            )
                        else:
                            self.progress_tracker.mark_chunk_failed(result["filename"], result["error"])
                        
                        # Progress update
                        completed = len(results)
                        print(f" Progress: [{completed}/{total_chunks}] ({completed/total_chunks*100:.1f}%)")
                        
                    except Exception as e:
                        print(f" Error processing {chunk_filepath}: {e}")
                        error_result = {
                            "success": False,
                            "filename": os.path.basename(chunk_filepath),
                            "error": str(e),
                            "duration": 0
                        }
                        results.append(error_result)
        
        # Sort results by filename to maintain order
        results.sort(key=lambda x: x["filename"])
        
        total_time = time.time() - start_time
        successful_chunks = sum(1 for r in results if r["success"])
        
        print(f"\n PARALLEL TRANSLATION COMPLETE!")
        print("=" * 60)
        print(f" STATISTICS:")
        print(f"   • Total chunks: {total_chunks}")
        print(f"   • Successful: {successful_chunks}")
        print(f"   • Failed: {total_chunks - successful_chunks}")
        print(f"   • Skipped: {sum(1 for r in results if r.get('skipped', False))}")
        print(f"   • Total time: {total_time/60:.1f} minutes")
        print(f"   • Average time per chunk: {total_time/total_chunks:.1f} seconds")
        print(f"   • Workers used: {self.max_workers}")
        print()
        
        if total_chunks - successful_chunks > 0:
            print(" Failed chunks:")
            for result in results:
                if not result["success"]:
                    print(f"   • {result['filename']}: {result['error']}")
            print()
        
        return results

def main():
    try:
        # Load configuration
        config = load_config()
        
        target_lang = config.target_language
        chunks_dir = config.chunks_dir
        output_file = config.get_output_filename()
        format_output = config.format_output
        
        print(" PARALLEL CHUNK-BASED TRANSLATION SYSTEM")
        print("=" * 60)
        print(f" Target Language: {target_lang}")
        print(f" Source Chunks: {chunks_dir}")
        print(f" Final Output: {output_file}")
        print(f" Format Output: {format_output}")
        print(f" Parallel Workers: 4")
        print("=" * 60)
        
        # Initialize parallel chunk translator
        translator = ParallelChunkTranslator("translated_chunks", max_workers=4)
        
        # Check if chunks already exist
        existing_chunks = translator.get_translated_files()
        if existing_chunks:
            print(f" Found {len(existing_chunks)} existing translated chunks")
            response = input("Continue with existing chunks? (y/N): ").strip().lower()
            if response != 'y':
                print("🧹 Clearing existing chunks...")
                translator.clear_translated_chunks()
                translator.progress_tracker.clear_progress()
        
        # Translate all chunks in parallel
        print("\n STEP 1: PARALLEL TRANSLATION")
        print("-" * 60)
        
        start_time = time.time()
        results = translator.translate_all_chunks_parallel(
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
            print(" No chunks were translated successfully!")
            sys.exit(1)
        
        print(f"\n Parallel translation completed: {successful_chunks} chunks")
        
        # Merge chunks
        print("\n STEP 2: MERGING CHUNKS INTO FINAL BOOK")
        print("-" * 60)
        
        merger = ChunkMerger("translated_chunks")
        
        # Validate chunks before merging
        validation = merger.validate_chunks()
        if not validation["valid"]:
            print("  Warning: Chunk validation failed!")
            if validation["missing_chunks"]:
                print(f"   Missing chunks: {validation['missing_chunks']}")
            if validation["extra_chunks"]:
                print(f"   Extra chunks: {validation['extra_chunks']}")
            
            response = input("Continue with merge anyway? (y/N): ").strip().lower()
            if response != 'y':
                print(" Merge cancelled")
                sys.exit(1)
        
        # Perform merge
        merge_start = time.time()
        merge_stats = merger.merge_chunks(output_file, add_chapter_breaks=True)
        merge_time = time.time() - start_time - translation_time
        
        # Final statistics
        total_time = time.time() - start_time
        
        print(f"\n PARALLEL TRANSLATION COMPLETE!")
        print("=" * 60)
        print(f" FINAL STATISTICS:")
        print(f"   • Total chunks processed: {len(results)}")
        print(f"   • Successful translations: {successful_chunks}")
        print(f"   • Failed translations: {len(results) - successful_chunks}")
        print(f"   • Translation time: {translation_time/60:.1f} minutes")
        print(f"   • Merge time: {merge_time:.1f} seconds")
        print(f"   • Total time: {total_time/60:.1f} minutes")
        print(f"   • Final book size: {merge_stats['total_characters']:,} characters")
        print(f"   • Output file: {output_file}")
        print(f"   • Parallel workers: 4")
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
        
        print(" You can now:")
        print("   • View individual translated chunks in 'translated_chunks/'")
        print("   • Re-translate specific chunks if needed")
        print("   • Re-merge chunks with different options")
        print("   • Delete 'translated_chunks/' directory to save space")
        print()
        print("⚡ Performance tip: Use this parallel version for faster translation!")
        
    except KeyboardInterrupt:
        print(f"\n  Translation interrupted by user")
        print("💡 Individual chunk files are saved in 'translated_chunks/'")
        print("💡 You can resume by running the script again")
        sys.exit(1)
    except Exception as e:
        print(f" Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
