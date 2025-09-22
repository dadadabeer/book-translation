#!/usr/bin/env python3
"""
Book chunking script that splits pg16317.txt into ~6k token chunks
while respecting paragraph boundaries for better translation reliability.
"""

import os
import re
import sys
from typing import List, Tuple

# Add parent directory to path to import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.config import load_config


def estimate_tokens(text: str) -> int:
    """
    Estimate token count for text (rough approximation).
    1 token ≈ 4 characters for English text.
    """
    return len(text) // 4


def split_into_paragraphs(text: str) -> List[str]:
    """
    Split text into paragraphs, preserving paragraph breaks.
    """
    # Split on double newlines (paragraph breaks)
    paragraphs = re.split(r'\n\s*\n', text)
    
    # Clean up paragraphs and filter out empty ones
    cleaned_paragraphs = []
    for para in paragraphs:
        para = para.strip()
        if para and len(para) > 10:  # Skip very short paragraphs
            cleaned_paragraphs.append(para)
    
    return cleaned_paragraphs


def create_chunks(paragraphs: List[str], target_tokens: int = 6000) -> List[str]:
    """
    Create chunks from paragraphs, respecting the target token limit.
    """
    chunks = []
    current_chunk = ""
    
    for paragraph in paragraphs:
        # Test if adding this paragraph would exceed the limit
        test_chunk = current_chunk + "\n\n" + paragraph if current_chunk else paragraph
        
        if estimate_tokens(test_chunk) <= target_tokens:
            current_chunk = test_chunk
        else:
            # Current chunk is full, save it and start new one
            if current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = paragraph
            else:
                # Single paragraph is too large, split it by sentences
                sentences = re.split(r'(?<=[.!?])\s+', paragraph)
                temp_chunk = ""
                
                for sentence in sentences:
                    test_sentence = temp_chunk + " " + sentence if temp_chunk else sentence
                    
                    if estimate_tokens(test_sentence) <= target_tokens:
                        temp_chunk = test_sentence
                    else:
                        if temp_chunk:
                            chunks.append(temp_chunk.strip())
                            temp_chunk = sentence
                        else:
                            # Single sentence is too large, force it
                            chunks.append(sentence)
                            temp_chunk = ""
                
                if temp_chunk:
                    current_chunk = temp_chunk
    
    # Add the last chunk
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    return chunks


def clean_gutenberg_text(text: str) -> str:
    """
    Clean Project Gutenberg text by removing headers and footers.
    """
    # Remove Project Gutenberg header
    text = re.sub(r'^\*\*\* START OF THE PROJECT GUTENBERG.*?\*\*\*', '', text, flags=re.MULTILINE | re.DOTALL)
    
    # Remove Project Gutenberg footer
    text = re.sub(r'\*\*\* END OF THE PROJECT GUTENBERG.*?\*\*\*$', '', text, flags=re.MULTILINE | re.DOTALL)
    
    # Remove the license text at the beginning
    text = re.sub(r'^.*?The Art of Public Speaking\s*BY\s*J\. BERG ESENWEIN', 'The Art of Public Speaking\nBY\nJ. BERG ESENWEIN', text, flags=re.MULTILINE | re.DOTALL)
    
    return text.strip()


def main():
    """Main function to chunk the book."""
    try:
        # Load configuration
        config = load_config()
        
        input_file = "data/pg16317.txt"
        output_dir = config.chunks_dir
        target_tokens = config.target_tokens
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        print(f"Reading {input_file}...")
        with open(input_file, 'r', encoding='utf-8') as f:
            text = f.read()
        
        print(f"Original text length: {len(text):,} characters")
        print(f"Estimated tokens: {estimate_tokens(text):,}")
        print(f"Target tokens per chunk: {target_tokens:,}")
        
        # Split into paragraphs
        paragraphs = split_into_paragraphs(text)
        print(f"Found {len(paragraphs)} paragraphs")
        
        # Create chunks
        chunks = create_chunks(paragraphs, target_tokens=target_tokens)
        print(f"Created {len(chunks)} chunks")
        
    except Exception as e:
        print(f"❌ Error loading configuration: {e}")
        print("💡 Using default settings...")
        
        # Fallback to default settings
        input_file = "data/pg16317.txt"
        output_dir = "chunks"
        target_tokens = 6000
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        print(f"Reading {input_file}...")
        with open(input_file, 'r', encoding='utf-8') as f:
            text = f.read()
        
        print(f"Original text length: {len(text):,} characters")
        print(f"Estimated tokens: {estimate_tokens(text):,}")
        
        # Split into paragraphs
        paragraphs = split_into_paragraphs(text)
        print(f"Found {len(paragraphs)} paragraphs")
        
        # Create chunks
        chunks = create_chunks(paragraphs, target_tokens=target_tokens)
        print(f"Created {len(chunks)} chunks")
    
    # Write chunks to files
    for i, chunk in enumerate(chunks, 1):
        filename = f"chunk_{i:02d}.txt"
        filepath = os.path.join(output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(chunk)
        
        token_count = estimate_tokens(chunk)
        print(f"  {filename}: {len(chunk):,} chars, ~{token_count:,} tokens")
    
    print(f"\nChunking complete! Created {len(chunks)} files in {output_dir}/")
    
    # Summary statistics
    total_tokens = sum(estimate_tokens(chunk) for chunk in chunks)
    avg_tokens = total_tokens / len(chunks)
    print(f"Average tokens per chunk: {avg_tokens:,.0f}")


if __name__ == "__main__":
    main()
