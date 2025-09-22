"""
Chunk merger that combines translated chunk files into a single book.
"""

import os
import re
from typing import List, Optional

class ChunkMerger:
    """Merges translated chunk files into a single book."""
    
    def __init__(self, translated_chunks_dir: str = "translated_chunks"):
        self.translated_chunks_dir = translated_chunks_dir
    
    def get_chunk_order(self, translated_files: List[str]) -> List[str]:
        """Extract chunk order from filenames."""
        # Extract chunk numbers from filenames like "translated_chunk_01.txt"
        chunk_numbers = []
        for filename in translated_files:
            match = re.search(r'chunk_(\d+)\.txt', filename)
            if match:
                chunk_numbers.append((int(match.group(1)), filename))
        
        # Sort by chunk number
        chunk_numbers.sort(key=lambda x: x[0])
        return [filename for _, filename in chunk_numbers]
    
    def merge_chunks(self, output_file: str, add_chapter_breaks: bool = True, add_page_numbers: bool = False) -> dict:
        """
        Merge all translated chunk files into a single book.
        
        Args:
            output_file: Path to output file
            add_chapter_breaks: Add chapter breaks between chunks
            add_page_numbers: Add page numbers (experimental)
        
        Returns:
            dict: Merge statistics
        """
        
        if not os.path.exists(self.translated_chunks_dir):
            raise FileNotFoundError(f"Translated chunks directory '{self.translated_chunks_dir}' not found!")
        
        # Get all translated files
        translated_files = [f for f in os.listdir(self.translated_chunks_dir) 
                          if f.startswith("translated_") and f.endswith(".txt")]
        
        if not translated_files:
            raise ValueError(f"No translated chunk files found in '{self.translated_chunks_dir}'!")
        
        # Sort files by chunk order
        ordered_files = self.get_chunk_order(translated_files)
        
        print(f"🔄 MERGING {len(ordered_files)} TRANSLATED CHUNKS")
        print("=" * 60)
        print(f"📁 Source Directory: {self.translated_chunks_dir}")
        print(f"📁 Output File: {output_file}")
        print(f"📖 Add Chapter Breaks: {add_chapter_breaks}")
        print("=" * 60)
        
        total_chars = 0
        chunk_count = 0
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        with open(output_file, "w", encoding="utf-8") as out:
            for i, filename in enumerate(ordered_files):
                chunk_filepath = os.path.join(self.translated_chunks_dir, filename)
                
                print(f"📄 Merging {filename}...")
                
                # Read chunk content
                with open(chunk_filepath, "r", encoding="utf-8") as f:
                    chunk_content = f.read()
                
                chunk_chars = len(chunk_content)
                total_chars += chunk_chars
                chunk_count += 1
                
                # Add chapter break if requested (except for first chunk)
                if add_chapter_breaks and i > 0:
                    out.write("\n" + "="*80 + "\n")
                    out.write(f"CHAPTER {i+1}")
                    out.write("\n" + "="*80 + "\n\n")
                
                # Write chunk content
                out.write(chunk_content)
                
                # Add spacing between chunks
                if i < len(ordered_files) - 1:  # Not the last chunk
                    out.write("\n\n")
                
                print(f"   ✅ {chunk_chars:,} characters added")
        
        merge_stats = {
            "total_chunks": chunk_count,
            "total_characters": total_chars,
            "output_file": output_file,
            "chunk_files": ordered_files
        }
        
        print(f"\n🎉 MERGE COMPLETE!")
        print("=" * 60)
        print(f"📊 STATISTICS:")
        print(f"   • Total chunks merged: {chunk_count}")
        print(f"   • Total characters: {total_chars:,}")
        print(f"   • Output file: {output_file}")
        print(f"   • File size: {os.path.getsize(output_file) / 1024 / 1024:.1f} MB")
        print()
        
        return merge_stats
    
    def validate_chunks(self) -> dict:
        """Validate that all chunks are present and in order."""
        
        if not os.path.exists(self.translated_chunks_dir):
            return {"valid": False, "error": "Directory not found"}
        
        translated_files = [f for f in os.listdir(self.translated_chunks_dir) 
                          if f.startswith("translated_") and f.endswith(".txt")]
        
        if not translated_files:
            return {"valid": False, "error": "No translated chunks found"}
        
        # Check for gaps in chunk numbering
        chunk_numbers = []
        for filename in translated_files:
            match = re.search(r'chunk_(\d+)\.txt', filename)
            if match:
                chunk_numbers.append(int(match.group(1)))
        
        chunk_numbers.sort()
        expected_numbers = list(range(1, len(chunk_numbers) + 1))
        
        missing_chunks = set(expected_numbers) - set(chunk_numbers)
        extra_chunks = set(chunk_numbers) - set(expected_numbers)
        
        return {
            "valid": len(missing_chunks) == 0,
            "total_chunks": len(translated_files),
            "missing_chunks": sorted(missing_chunks),
            "extra_chunks": sorted(extra_chunks),
            "chunk_files": sorted(translated_files)
        }
    
    def list_chunks(self):
        """List all translated chunks with their sizes."""
        
        if not os.path.exists(self.translated_chunks_dir):
            print("📁 No translated chunks directory found")
            return
        
        translated_files = [f for f in os.listdir(self.translated_chunks_dir) 
                          if f.startswith("translated_") and f.endswith(".txt")]
        
        if not translated_files:
            print("📄 No translated chunk files found")
            return
        
        ordered_files = self.get_chunk_order(translated_files)
        
        print(f"📄 TRANSLATED CHUNKS ({len(ordered_files)} files)")
        print("=" * 60)
        
        total_size = 0
        for filename in ordered_files:
            filepath = os.path.join(self.translated_chunks_dir, filename)
            size = os.path.getsize(filepath)
            total_size += size
            
            print(f"   {filename}: {size:,} bytes")
        
        print("=" * 60)
        print(f"📊 Total size: {total_size:,} bytes ({total_size/1024/1024:.1f} MB)")
        print(f"📁 Directory: {self.translated_chunks_dir}")
