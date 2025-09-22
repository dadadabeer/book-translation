"""
Configuration management for the book translation system.
"""

import json
import os
from typing import Dict, Any, Optional


class Config:
    """Configuration manager for the translation system."""
    
    def __init__(self, config_file: str = "config.json"):
        self.config_file = config_file
        self.config = self._load_config()
        self._validate_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from JSON file."""
        if not os.path.exists(self.config_file):
            raise FileNotFoundError(f"Configuration file '{self.config_file}' not found.")
        
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in config file: {e}")
        except Exception as e:
            raise Exception(f"Error loading config file: {e}")
    
    def _validate_config(self):
        """Validate configuration values."""
        required_sections = ['translation', 'chunking', 'output', 'processing']
        
        for section in required_sections:
            if section not in self.config:
                raise ValueError(f"Missing required config section: {section}")
        
        # Validate translation section
        translation = self.config['translation']
        if 'target_language' not in translation:
            raise ValueError("Missing 'target_language' in translation config")
        
        if not isinstance(translation.get('target_language'), str):
            raise ValueError("'target_language' must be a string")
        
        # Validate chunking section
        chunking = self.config['chunking']
        if 'target_tokens' not in chunking:
            raise ValueError("Missing 'target_tokens' in chunking config")
        
        if not isinstance(chunking.get('target_tokens'), int) or chunking['target_tokens'] <= 0:
            raise ValueError("'target_tokens' must be a positive integer")
    
    @property
    def target_language(self) -> str:
        """Get target language for translation."""
        return self.config['translation']['target_language']
    
    @property
    def model(self) -> str:
        """Get AI model name."""
        return self.config['translation'].get('model', 'aisingapore/Gemma-SEA-LION-v4-27B-IT')
    
    @property
    def max_tokens(self) -> int:
        """Get maximum tokens per API call."""
        return self.config['translation'].get('max_tokens', 18000)
    
    @property
    def temperature(self) -> float:
        """Get temperature setting for API calls."""
        return self.config['translation'].get('temperature', 0.1)
    
    @property
    def target_tokens(self) -> int:
        """Get target tokens per chunk."""
        return self.config['chunking']['target_tokens']
    
    @property
    def max_chunks(self) -> Optional[int]:
        """Get maximum number of chunks to process."""
        return self.config['chunking'].get('max_chunks')
    
    @property
    def line_width(self) -> int:
        """Get line width for output formatting."""
        return self.config['output'].get('line_width', 80)
    
    @property
    def format_output(self) -> bool:
        """Get whether to format output."""
        return self.config['output'].get('format_output', True)
    
    @property
    def output_dir(self) -> str:
        """Get output directory."""
        return self.config['output'].get('output_dir', 'output')
    
    @property
    def num_chunks(self) -> int:
        """Get number of chunks to process."""
        return self.config['processing'].get('num_chunks', 1)
    
    @property
    def chunks_dir(self) -> str:
        """Get chunks directory."""
        return self.config['processing'].get('chunks_dir', 'chunks')
    
    def get_output_filename(self) -> str:
        """Generate output filename based on target language."""
        lang_code = self.target_language.lower()
        return os.path.join(self.output_dir, f"translated_book_{lang_code}.txt")
    
    def update_target_language(self, language: str):
        """Update target language in config."""
        self.config['translation']['target_language'] = language
    
    def save_config(self):
        """Save current configuration to file."""
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)


def load_config(config_file: str = "config.json") -> Config:
    """Load configuration from file."""
    return Config(config_file)


# Predefined language options for easy selection
SUPPORTED_LANGUAGES = {
    "malay": "Malay",
    "indonesian": "Indonesian", 
    "thai": "Thai",
    "vietnamese": "Vietnamese",
    "tagalog": "Tagalog",
}
