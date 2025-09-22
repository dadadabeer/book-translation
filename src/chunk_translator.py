"""
Chunk-based translator that saves each translated chunk as a separate file.
"""

import os
import time
import re
from datetime import datetime
from src.client import get_client
from src.formatter import format_book_output
from src.config import load_config
from src.progress_tracker import ProgressTracker

def clean_repetition(text: str) -> str:
    """
    Detects and trims repeated trailing sections that the model sometimes generates.
    Looks for a long substring that repeats at the end and removes duplicates.
    """
    # Find repeated block of >=200 chars at the end
    match = re.search(r'(.{200,})(\1+)$', text, re.DOTALL)
    if match:
        return text[: match.start(2)].strip()
    return text.strip()

def translate_chunk(text: str, target_lang: str = "Indonesian", max_tokens: int = 8000, temperature: float = 0.2) -> str:
    """Translate a chunk of text using SEA-LION API."""
    try:
        client = get_client()
        print(f"🔄 Calling SEA-LION API for translation to {target_lang}...")

        response = client.chat.completions.create(
            model="aisingapore/Gemma-SEA-LION-v4-27B-IT",
            messages=[
                {
                    "role": "system",
                    "content": (
                        f"You are a professional translator. "
                        f"Translate EVERYTHING into {target_lang}. "
                        "Preserve the original structure, formatting, and headings. "
                        "Do NOT add notes, comments, or English text. "
                        "Stop translating when you reach the end of the provided text."
                    ),
                },
                {
                    "role": "user",
                    "content": text,
                },
            ],
            max_tokens=max_tokens,
            temperature=temperature,
        )

        raw_output = response.choices[0].message.content
        result = clean_repetition(raw_output)

        print(f"✅ Translation successful, length: {len(result)} chars")
        return result

    except Exception as e:
        print(f"❌ Translation error: {str(e)}")
        print("🔄 Falling back to original text...")
        return text

class ChunkTranslator:
    """Translates chunks and saves each as a separate file."""
    
    def __init__(self, output_dir: str = "translated_chunks"):
        self.output_dir = output_dir
        self.progress_tracker = ProgressTracker()
        os.makedirs(self.output_dir, exist_ok=True)
    
    def translate_chunk_file(self, chunk_filepath: str, target_lang: str, format_output: bool = True, max_tokens: int = 8000, temperature: float = 0.2) -> dict:
        """
        Translate a single chunk file and save it separately.
        
        Returns:
            dict: Translation result with metadata
        """
        chunk_start = time.time()
        filename = os.path.basename(chunk_filepath)
        
        try:
            # Read chunk
            with open(chunk_filepath, "r", encoding="utf-8") as f:
                chunk_text = f.read()
            
            print(f"🔄 Translating {filename}...")
            
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
            
            print(f"✅ {filename} → {translated_filename} ({duration:.1f}s)")
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
            
            print(f"❌ {filename} failed: {str(e)}")
            return result
    
    def translate_all_chunks(self, chunks_dir: str, target_lang: str, format_output: bool = True, max_chunks: int = None, max_tokens: int = 8000, temperature: float = 0.2):
        """Translate all chunks in a directory."""
        
        # Get chunk files
        if not os.path.exists(chunks_dir):
            raise FileNotFoundError(f"Chunks directory '{chunks_dir}' not found!")
        
        chunk_files = numeric_sort([f for f in os.listdir(chunks_dir) if f.endswith(".txt")])
        
        if not chunk_files:
            raise ValueError(f"No chunk files found in '{chunks_dir}'!")
        
        # Limit chunks if specified
        if max_chunks:
            chunk_files = chunk_files[:max_chunks]
        
        total_chunks = len(chunk_files)
        
        print(f"🚀 TRANSLATING {total_chunks} CHUNKS SEPARATELY")
        print("=" * 60)
        print(f"📖 Target Language: {target_lang}")
        print(f"📁 Chunks Directory: {chunks_dir}")
        print(f"📁 Output Directory: {self.output_dir}")
        print(f"🎨 Format Output: {format_output}")
        print("=" * 60)
        
        # Start progress tracking
        self.progress_tracker.start_session(
            target_lang, 
            total_chunks, 
            self.output_dir
        )
        
        start_time = time.time()
        results = []
        
        for i, filename in enumerate(chunk_files):
            chunk_filepath = os.path.join(chunks_dir, filename)
            
            print(f"\n📊 Progress: [{i+1}/{total_chunks}]")
            
            # Check if already translated
            translated_filename = f"translated_{filename}"
            translated_filepath = os.path.join(self.output_dir, translated_filename)
            
            if os.path.exists(translated_filepath):
                print(f"⏭️  Skipping {filename} (already translated)")
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
            else:
                # Translate chunk
                result = self.translate_chunk_file(chunk_filepath, target_lang, format_output, max_tokens, temperature)
                
                # Update progress
                if result["success"]:
                    self.progress_tracker.mark_chunk_completed(
                        filename, 
                        result["output_size"], 
                        result["duration"]
                    )
                else:
                    self.progress_tracker.mark_chunk_failed(filename, result["error"])
            
            results.append(result)
        
        total_time = time.time() - start_time
        successful_chunks = sum(1 for r in results if r["success"])
        
        print(f"\n🎉 CHUNK TRANSLATION COMPLETE!")
        print("=" * 60)
        print(f"📊 STATISTICS:")
        print(f"   • Total chunks: {total_chunks}")
        print(f"   • Successful: {successful_chunks}")
        print(f"   • Failed: {total_chunks - successful_chunks}")
        print(f"   • Total time: {total_time/60:.1f} minutes")
        print(f"   • Output directory: {self.output_dir}")
        print()
        
        if total_chunks - successful_chunks > 0:
            print("❌ Failed chunks:")
            for result in results:
                if not result["success"]:
                    print(f"   • {result['filename']}: {result['error']}")
            print()
        
        return results
    
    def get_translated_files(self) -> list:
        """Get list of translated chunk files."""
        if not os.path.exists(self.output_dir):
            return []
        
        files = [f for f in os.listdir(self.output_dir) if f.startswith("translated_") and f.endswith(".txt")]
        return sorted(files)
    
    def clear_translated_chunks(self):
        """Clear all translated chunk files."""
        if os.path.exists(self.output_dir):
            for filename in self.get_translated_files():
                filepath = os.path.join(self.output_dir, filename)
                os.remove(filepath)
            print(f"✅ Cleared {len(self.get_translated_files())} translated chunk files")
        else:
            print("📁 No translated chunks directory found")


def numeric_sort(files):
    def extract_num(fname):
        match = re.search(r'(\d+)', fname)
        return int(match.group(1)) if match else float("inf")
    return sorted(files, key=extract_num)