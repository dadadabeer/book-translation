# src/formatter.py
import re
import textwrap

def format_translated_text(text: str, line_width: int = 80) -> str:
    """
    Clean up and format translated text for better readability.
    
    Args:
        text: Raw translated text from the API
        line_width: Maximum characters per line for wrapping
    
    Returns:
        Formatted text with proper paragraph structure
    """
    
    # Remove markdown formatting
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)  # Remove **bold**
    text = re.sub(r'##\s*(.*)', r'\1', text)      # Remove ## headers
    text = re.sub(r'#\s*(.*)', r'\1', text)       # Remove # headers
    
    # Clean up extra whitespace and newlines
    text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)  # Multiple newlines to double
    text = re.sub(r'[ \t]+', ' ', text)            # Multiple spaces to single
    text = text.strip()
    
    # Split into paragraphs
    paragraphs = re.split(r'\n\s*\n', text)
    formatted_paragraphs = []
    
    for paragraph in paragraphs:
        paragraph = paragraph.strip()
        if not paragraph:
            continue
            
        # Skip very short lines that look like headers/titles
        if len(paragraph) < 50 and (
            paragraph.isupper() or 
            paragraph.count('\n') == 0 or
            ':' in paragraph and len(paragraph.split(':')) == 2
        ):
            formatted_paragraphs.append(paragraph)
        else:
            # Wrap long paragraphs
            wrapped = textwrap.fill(
                paragraph, 
                width=line_width,
                break_long_words=False,
                break_on_hyphens=False
            )
            formatted_paragraphs.append(wrapped)
    
    # Join paragraphs with proper spacing
    return '\n\n'.join(formatted_paragraphs)


def format_book_output(text: str) -> str:
    """
    Special formatting for book output with chapter/section awareness.
    Preserves indentation and structure while cleaning up formatting.
    """
    
    # Remove markdown formatting
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    text = re.sub(r'##\s*(.*)', r'\1', text)
    text = re.sub(r'#\s*(.*)', r'\1', text)
    
    # Clean up excessive whitespace but preserve indentation
    text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)  # Multiple newlines to double
    text = re.sub(r'[ \t]{2,}', ' ', text)         # Multiple spaces/tabs to single space
    text = text.strip()
    
    lines = text.split('\n')
    formatted_lines = []
    
    for line in lines:
        # Preserve empty lines
        if not line.strip():
            formatted_lines.append('')
            continue
        
        # Detect indentation (leading whitespace)
        stripped_line = line.strip()
        leading_whitespace = line[:len(line) - len(line.lstrip())]
        
        # Check if line looks like a title/header (short lines, titles, etc.)
        is_title = (
            len(stripped_line) < 60 and (
                stripped_line.isupper() or
                stripped_line.count(' ') < 5 or
                ':' in stripped_line and len(stripped_line.split(':')) == 2 or
                stripped_line.startswith('CHAPTER') or
                stripped_line.startswith('Chapter') or
                stripped_line.startswith('BAB') or
                stripped_line.startswith('Bab')
            )
        )
        
        # Check if line appears to be indented content (like author names, credits, etc.)
        is_indented_content = (
            leading_whitespace and (
                len(stripped_line) < 100 or  # Short indented lines
                ':' in stripped_line or      # Lines with colons
                stripped_line.startswith(('Author', 'Penulis', 'Credit', 'Kredit', 'Release', 'Tarikh'))
            )
        )
        
        if is_title:
            # Titles/headers - no indentation, no wrapping
            formatted_lines.append(stripped_line)
        elif is_indented_content:
            # Preserve indentation for structured content
            if len(stripped_line) > 80:
                # Wrap indented content while preserving indentation
                indent_len = len(leading_whitespace)
                wrapped = textwrap.fill(
                    stripped_line,
                    width=80,
                    initial_indent=leading_whitespace,
                    subsequent_indent=' ' * indent_len,
                    break_long_words=False,
                    break_on_hyphens=False
                )
                formatted_lines.append(wrapped)
            else:
                formatted_lines.append(line.rstrip())
        else:
            # Regular paragraph content
            if len(stripped_line) > 80:
                # Wrap long paragraphs
                wrapped = textwrap.fill(
                    stripped_line,
                    width=80,
                    break_long_words=False,
                    break_on_hyphens=False
                )
                formatted_lines.append(wrapped)
            else:
                formatted_lines.append(stripped_line)
    
    # Join lines and clean up spacing
    result = '\n'.join(formatted_lines)
    result = re.sub(r'\n\s*\n\s*\n+', '\n\n', result)
    
    return result.strip()
