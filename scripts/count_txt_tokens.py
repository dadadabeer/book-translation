# count_txt_tokens.py
import tiktoken

# Load GPT-2 tokenizer (works well for English estimates)
enc = tiktoken.get_encoding("gpt2")

with open("data/pg16317.txt", "r", encoding="utf-8") as f:
    text = f.read()

tokens = enc.encode(text)
print(f"Total tokens in file: {len(tokens)}")
