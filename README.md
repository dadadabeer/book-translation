

# Book Translation Project

A Python-based book translation system that uses SEA-LION AI models to translate English books into various languages with proper formatting. The system was designed iteratively, with assumptions documented and tradeoffs explained.  

> **Note for reviewers (recruiters):**  
>Below, I’ve included the assumptions I made, the design priorities, the problems I encountered, and how I solved them. This should help you understand how I approach problem solving and what I consider important as a software engineer.

---

## Assumptions

- The SEA-LION model can reliably handle **up to ~18k tokens output**.  
- To avoid truncation, I set a **safer cap at 15k** initially.  
- Translation often **increases token count**, so I set **output > input tokens**.  
- Internet interruptions and rate limits are expected, so the system must be **resumable**.  
- Some errors (mixed translation, dropped text) would require **post-processing cleanup**.  

---

## Design Approach

- **Token Calculations**  
  I began by calculating the total tokens of the source book. Empirical testing showed the SEA-LION model reliably outputs ~18k tokens, so I started with a max of 15k, then refined downward.  

- **Chunking Strategy**  
  Very long input chunks caused truncation and testing difficulties. I iterated toward smaller chunks (~1.3k tokens). I made the **output size slightly larger than input** to account for expansion in translation.  

- **Tradeoffs**  
  - **Large chunks**: fewer API calls but higher risk of truncation or incomplete translation.  
  - **Small chunks**: more reliable and easier to retry, but slower if sequential.  
  I chose smaller chunks and then solved the speed issue with parallelization.  

---

## Problems Encountered & Solutions

1. **Prompt Following Issues**  
   - Sometimes the model ignored instructions and returned English.  
   - **Solution**: tightened the system prompt, re-emphasized “translate everything.”  

2. **Truncation**  
   - Long outputs were cut off mid-sentence.  
   - **Solution**: reduced chunk size, adjusted token limits.  

3. **Mixed / Double Translation**  
   - Some chunks were partly untranslated or repeated.  
   - **Solution**: regex-based repetition cleanup + token tuning. Feeding Max token output can result in duplication of content; LLM SIDE EFFECT.  

4. **Slow Translation**  
   - Sequential runs took too long (35s per chunk × ~174 chunks).  
   - **Solution**: parallelized into 4 workers, balancing throughput with API rate limits.  

5. **Resumability / Fault Tolerance**  
   - Internet disconnects or rate limits could interrupt translation.  
   - **Solution**: progress tracker:  
     - Skips already translated chunks  
     - Retries failed ones  
     - Allows safe resume  

---

## Validation

- Checked **random consecutive chunks** for smooth continuity at boundaries.  
- Verified no leftover English, no truncation.  
- Ensured **headings and formatting** were preserved.  
- Spot-checked translation accuracy against original.  

---

## Features

- **AI-Powered Translation**: SEA-LION Gemma v4-27B models  
- **Chunk-Based System**: Each chunk translated separately and saved  
- **Resumable Translation**: Skip already completed chunks  
- **Parallel Processing**: 4 threads tuned for 35s/chunk  
- **Clean Formatting**: Removed markdown, wrapped lines neatly  
- **JSON Config Management**: Easy reproducibility  
- **Multi-language Support**: Configurable target languages  


Priorities as a Software Engineer

Reliability – Resumable, fault-tolerant design prevents work loss

Scalability – Parallelization tuned to API limits and throughput

Quality – Token limits adjusted to avoid truncation or mistranslation

Maintainability – Clear modular code, config-driven design

Validation – Spot-checked outputs to ensure smooth transitions and accuracy

---



## Quick Start

### 1. Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Set up API key
echo "SEALION_API_KEY=your_api_key_here" > .env
```

### 2. Configure
```bash
# Interactive language selection
python change_language.py

# Or edit config.json directly
```

### 3. Translate
```bash
# Create chunks. Already created but re run this if you want more chunks by adjusting the token size of each chunk (currently 1500)
python scripts/chunk_book.py

# Translate (sequential)
python run_chunk_based.py

# Translate (parallel recommended)
python run_chunk_based_parallel.py

# Merge into final book
python manage_chunks.py merge
```

## Project Structure

```
book-translation/
├── 📁 chunks/                    # Original book chunks (174 files)
│   ├── chunk_01.txt             # Book segments for translation
│   ├── chunk_02.txt
│   └── ...                      # chunk_01.txt to chunk_174.txt
│
├── 📁 translated_chunks/         # Translated chunks (119 files)
│   ├── translated_chunk_01.txt  # AI-translated versions
│   ├── translated_chunk_02.txt
│   └── ...                      # Corresponding translated files
│
├── 📁 output/                    # Final translated books
│   ├── translated_book_malay.txt      # Complete Malay translation
│   └── translated_book_vietnamese.txt # Complete Vietnamese translation
│
├── 📁 data/                      # Source material
│   └── pg16317.txt              # Original English book (Project Gutenberg)
│
├── 📁 scripts/                   # Utility scripts
│   ├── chunk_book.py            # Splits book into manageable chunks
│   ├── count_txt_tokens.py      # Counts tokens in original text file
│   └── test_tokens.py           # Script to test max output token of current model of SEALION
│
├── 📁 src/                       # Core application code
│   ├── __init__.py              # Package initialization
│   ├── chunk_merger.py          # Combines translated chunks
│   ├── chunk_translator.py      # Main translation logic
│   ├── client.py                # SEA-LION API integration
│   ├── config.py                # Configuration management
│   ├── formatter.py             # Output formatting
│   └── progress_tracker.py      # Resume capability
│
├── 📄 run_chunk_based.py         # Sequential translation runner
├── 📄 run_chunk_based_parallel.py # Parallel translation (recommended)
├── 📄 manage_chunks.py           # Chunk management CLI
├── 📄 change_language.py         # Interactive language selector
├── 📄 config.json               # Translation settings
├── 📄 translation_progress.json # Progress tracking file
├── 📄 requirements.txt          # Python dependencies
├── 📄 .env                      # API keys (not in git)
└── 📄 README.md                 # This file
```

### File Descriptions

| File/Directory | Purpose | Key Features |
|----------------|---------|--------------|
| `chunks/` | Original book segments | 174 files, ~1500 tokens each |
| `translated_chunks/` | AI-translated segments | Progressively built, resumable |
| `output/` | Final translated books | Complete books in target language |
| `data/pg16317.txt` | Source book | Project Gutenberg English text |
| `run_chunk_based_parallel.py` | Main translator | 4 parallel workers, fault-tolerant |
| `manage_chunks.py` | Chunk utilities | List, validate, merge, clear operations |
| `config.json` | Settings | Language, model, token limits, formatting |
| `translation_progress.json` | Progress tracking | Resume capability, skip completed chunks |
| `src/chunk_translator.py` | Core translation logic | Main translation processing |
| `src/client.py` | SEA-LION API integration | API communication, error handling |
| `src/chunk_merger.py` | Combines translated chunks | Merges chunks into final book |
| `src/progress_tracker.py` | Resume functionality | Tracks completed chunks |
| `scripts/chunk_book.py` | Book segmentation | Splits into optimal chunk sizes |
| `scripts/count_txt_tokens.py` | Token counting | Analyzes text file token counts |
| `scripts/test_tokens.py` | Token testing | Utilities for token analysis |

### Key Directories

- **`chunks/`**: Contains the original English text split into manageable segments
- **`translated_chunks/`**: Stores individual translated segments as they're processed
- **`output/`**: Final complete translated books ready for reading
- **`src/`**: Modular Python code for translation logic, configuration, and utilities
- **`scripts/`**: Standalone utilities for book processing

## Configuration

### Key Settings in `config.json`:

```json
{
  "translation": {
    "target_language": "Vietnamese",
    "model": "aisingapore/Gemma-SEA-LION-v4-27B-IT",
    "max_tokens": 2250,
    "temperature": 0.2
  },
  "chunking": {
    "target_tokens": 1500,
    "max_chunks": null
  },
  "output": {
    "line_width": 80,
    "format_output": true,
    "output_dir": "output"
  },
  "processing": {
    "num_chunks": null,
    "chunks_dir": "chunks"
  }
}
```

### Configuration Options:

| Setting | Purpose | Recommended Value |
|---------|---------|-------------------|
| `target_language` | Translation target | "Vietnamese", "Malay", etc. |
| `max_tokens` | API output limit | 2250 (prevents truncation) |
| `target_tokens` | Chunk size | 1500 (balanced) |
| `num_chunks` | Limit for testing | `null` (all chunks) or number |
| `format_output` | Clean formatting | `true` (recommended) |

## Usage Examples (run the corresponding script for sequential or parallel)

### Full Book Translation
```bash
python run_chunk_based_parallel.py  # 4 parallel workers
```

### Test Run (First 10 chunks)
```bash
# Edit config.json: "num_chunks": 10
python run_chunk_based_parallel.py
```

### Resume Interrupted Translation
```bash
python run_chunk_based_parallel.py  # Automatically skips completed chunks
```

### Chunk Management
```bash
python manage_chunks.py list       # List all translated chunks
python manage_chunks.py validate   # Check chunk integrity
python manage_chunks.py clear      # Clear all chunks and progress
python manage_chunks.py merge      # Merge chunks into final book
```

## Performance

### Timing Estimates:
- **Total for 174 chunks**: ~1.5 hours (sequential) vs ~22 mins (parallel - 4 Threads)


## Troubleshooting

### Common Issues:

| Problem | Solution |
|---------|----------|
| Translation truncated | Increase `max_tokens` in config |
| Wrong language | Check `target_language` setting |
| Slow translation | Use parallel version |
| API errors | Check `.env` file and internet |
| Missing chunks | Run `manage_chunks.py validate` |

### Debug Commands:
```bash
# Check configuration
python -c "from src.config import load_config; print(load_config().target_language)"

# Validate chunks
python manage_chunks.py validate

# List chunk status
python manage_chunks.py list
```

## Technical Details

### Design Decisions:
- **Chunk Size**: 1500 tokens balances quality vs. API limits
- **Output Limit**: 2250 tokens prevents truncation
- **Parallel Workers**: 4 threads optimized for API rate limits
- **Resume Logic**: File-based progress tracking

### Validation Approach:
- Manual spot-checks at chunk boundaries
- Verification of formatting preservation
- Chunk ordering and completeness checks

## Supported Languages

- Vietnamese, Malay, Indonesian, Thai, Tagalog
- Any language supported by SEA-LION model

## Dependencies

- `openai>=1.0.0` - SEA-LION API communication
- `python-dotenv>=1.0.0` - Environment variables
