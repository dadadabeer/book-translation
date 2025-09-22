import os
from openai import OpenAI
from dotenv import load_dotenv

# Load API key from .env
load_dotenv()
API_KEY = os.getenv("SEALION_API_KEY")

client = OpenAI(
    base_url="https://api.sea-lion.ai/v1",
    api_key=API_KEY,
)

def test_max_output_in_steps():
    prompt = "Write the word HELLO repeatedly until you reach the maximum output limit."
    step_sizes = [20000, 40000, 80000, 128000]  # probe gradually

    for step in step_sizes:
        print(f"\n--- Testing with max_tokens={step} ---")
        try:
            response = client.chat.completions.create(
                model="aisingapore/Gemma-SEA-LION-v4-27B-IT",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=step,
            )

            usage = response.usage
            print("Prompt tokens:", usage.prompt_tokens)
            print("Completion tokens:", usage.completion_tokens)
            print("Total tokens:", usage.total_tokens)

            # Show first 200 characters of output
            output = response.choices[0].message.content
            print("Sample output:", output[:200].replace("\n", " ") + "...")

            # Detect truncation: if output ended right at max_tokens
            if usage.completion_tokens >= step:
                print("⚠️ Likely truncated at the max token cap.")
                break

        except Exception as e:
            print("Error:", e)
            break

if __name__ == "__main__":
    test_max_output_in_steps()
