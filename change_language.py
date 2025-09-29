#!/usr/bin/env python3
"""
Interactive script to change the target language for translation.
"""

import sys
from src.config import load_config, SUPPORTED_LANGUAGES

def main():
    print(" Book Translation - Language Configuration")
    print("=" * 50)
    
    try:
        config = load_config()
        current_lang = config.target_language
        print(f"Current target language: {current_lang}")
        print()
        
        print("Supported languages:")
        for i, (code, name) in enumerate(SUPPORTED_LANGUAGES.items(), 1):
            marker = "← current" if name == current_lang else ""
            print(f"  {i}. {name} {marker}")
        
        print(f"  {len(SUPPORTED_LANGUAGES) + 1}. Custom language")
        print()
        
        while True:
            try:
                choice = input("Select language (number): ").strip()
                
                if choice.isdigit():
                    choice_num = int(choice)
                    
                    if 1 <= choice_num <= len(SUPPORTED_LANGUAGES):
                        # Selected predefined language
                        lang_code = list(SUPPORTED_LANGUAGES.keys())[choice_num - 1]
                        new_language = SUPPORTED_LANGUAGES[lang_code]
                        break
                    elif choice_num == len(SUPPORTED_LANGUAGES) + 1:
                        # Custom language
                        new_language = input("Enter custom language name: ").strip()
                        if new_language:
                            break
                        else:
                            print(" Language name cannot be empty. Please try again.")
                    else:
                        print(f" Invalid choice. Please enter a number between 1 and {len(SUPPORTED_LANGUAGES) + 1}.")
                else:
                    print(" Please enter a valid number.")
                    
            except KeyboardInterrupt:
                print("\n👋 Cancelled.")
                sys.exit(0)
            except Exception as e:
                print(f" Error: {e}")
        
        # Update configuration
        config.update_target_language(new_language)
        config.save_config()
        
        print(f"✅ Target language updated to: {new_language}")
        print(f"📁 Output file will be: {config.get_output_filename()}")
        print()
        print("💡 You can now run 'python run.py' to start translation.")
        
    except Exception as e:
        print(f" Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
