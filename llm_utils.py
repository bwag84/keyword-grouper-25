import os
import json
from dotenv import load_dotenv

# Load API keys
load_dotenv()

# Placeholder functions - Implement actual API calls here
# Remember to add robust error handling (try-except blocks, retries) and JSON parsing

def call_openai_api(prompt):
    from openai import OpenAI
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    try:
        response = client.chat.completions.create(
            model="gpt-4-turbo-preview", # Or another suitable model
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1, # Lower temperature for more deterministic output
            response_format={ "type": "json_object" } # If supported by model
        )
        content = response.choices[0].message.content
        # Ensure JSON parsing is robust
        return json.loads(content.strip())
    except Exception as e:
        print(f"Error calling OpenAI API: {e}")
        # Try to parse JSON even if response_format failed
        try:
            # Find JSON block if there's extra text (common issue)
            json_start = content.find('{')
            json_end = content.rfind('}') + 1
            if json_start != -1 and json_end != -1:
                 return json.loads(content[json_start:json_end])
        except Exception as json_e:
             print(f"Error parsing OpenAI JSON response: {json_e}. Content: {content}")
             return None # Indicate failure


def call_gemini_api(prompt):
    import google.generativeai as genai
    genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
    model = genai.GenerativeModel('gemini-pro') # Or 'gemini-1.5-pro-latest'
    try:
        # Gemini might need specific configuration for JSON output guarantee
        # generation_config = genai.types.GenerationConfig(response_mime_type="application/json") # Check latest SDK
        response = model.generate_content(prompt) # Add generation_config= if available
        content = response.text
        # Gemini response might need cleaning before JSON parsing
        json_start = content.find('{')
        json_end = content.rfind('}') + 1
        if json_start != -1 and json_end != -1:
            return json.loads(content[json_start:json_end].strip())
        else:
            print(f"Could not find JSON in Gemini response: {content}")
            return None
    except Exception as e:
        print(f"Error calling Gemini API: {e}")
        return None

def call_claude_api(prompt):
    from anthropic import Anthropic
    client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    try:
        response = client.messages.create(
            model="claude-3-opus-20240229", # Or Sonnet/Haiku
            max_tokens=500, # Adjust as needed
            temperature=0.1,
            messages=[{"role": "user", "content": prompt}]
        )
        content = response.content[0].text
        # Claude might wrap JSON in markdown or other text
        json_start = content.find('{')
        json_end = content.rfind('}') + 1
        if json_start != -1 and json_end != -1:
            return json.loads(content[json_start:json_end].strip())
        else:
            print(f"Could not find JSON in Claude response: {content}")
            return None
    except Exception as e:
        print(f"Error calling Claude API: {e}")
        return None

def call_mistral_api(prompt):
    # Option 1: Using MistralAI client (if installed via 'pip install mistralai')
    # from mistralai.client import MistralClient
    # from mistralai.models.chat_completion import ChatMessage
    # client = MistralClient(api_key=os.getenv("MISTRAL_API_KEY"))
    # model = "mistral-large-latest" # Or other Mistral model
    # messages = [ChatMessage(role="user", content=prompt)]
    # try:
    #     response = client.chat(model=model, messages=messages, temperature=0.1)
    #     content = response.choices[0].message.content
    #     # Parse JSON robustly
    #     # ... (similar JSON finding logic as above) ...
    # except Exception as e:
    #     print(f"Error calling Mistral API: {e}")
    #     return None

    # Option 2: Using OpenAI client with Mistral via compatible endpoint (e.g., TogetherAI)
    # Ensure MISTRAL_API_KEY is set (even if it's an OpenAI-format key for the endpoint)
    # and OPENAI_API_BASE is set in .env or environment pointing to the compatible endpoint
    from openai import OpenAI
    client = OpenAI(
        api_key=os.getenv("MISTRAL_API_KEY"), # Or specific key for the endpoint
        base_url=os.getenv("MISTRAL_API_BASE_URL") # e.g., "https://api.together.xyz/v1"
    )
    try:
        response = client.chat.completions.create(
            model="mistralai/Mistral-7B-Instruct-v0.1", # Or specific model name on the platform
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            # May or may not support response_format JSON
        )
        content = response.choices[0].message.content
        # Parse JSON robustly
        json_start = content.find('{')
        json_end = content.rfind('}') + 1
        if json_start != -1 and json_end != -1:
            return json.loads(content[json_start:json_end].strip())
        else:
             print(f"Could not find JSON in Mistral (OpenAI Compatible) response: {content}")
             return None
    except Exception as e:
        print(f"Error calling Mistral API (OpenAI Compatible): {e}")
        return None


def get_llm_grouping(keyword, language, llm_choice, custom_prompt_template):
    """Gets grouping from the selected LLM."""
    # Format the final prompt sent to the API
    prompt = custom_prompt_template.format(keyword=keyword, language=language)

    if llm_choice == "OpenAI":
        return call_openai_api(prompt)
    elif llm_choice == "Gemini":
        return call_gemini_api(prompt)
    elif llm_choice == "Claude":
        return call_claude_api(prompt)
    elif llm_choice == "Mistral":
        return call_mistral_api(prompt)
    else:
        raise ValueError("Invalid LLM choice")