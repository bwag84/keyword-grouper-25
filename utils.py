# utils.py
import pandas as pd
import io
import pycountry

# Note: Removed 'import streamlit as st' as decorators are moved to app.py

def parse_keywords(input_data, source_type):
    """
    Parses keywords from uploaded file or text area.
    Returns a tuple: (list_of_keywords, error_message or None)
    """
    keywords = []
    error_message = None
    if source_type == "csv" and input_data is not None:
        try:
            # Read the uploaded file content
            content = input_data.getvalue()
            # Attempt to decode assuming UTF-8, handle potential errors
            try:
                 csv_content = content.decode('utf-8')
            except UnicodeDecodeError:
                 try:
                      csv_content = content.decode('latin-1') # Try another common encoding
                 except UnicodeDecodeError as decode_error:
                      raise ValueError(f"Cannot decode file. Please ensure it's UTF-8 or Latin-1 encoded. Error: {decode_error}")

            # Use io.StringIO to treat the string as a file
            df = pd.read_csv(io.StringIO(csv_content))

            if 'keyword' in df.columns:
                # Convert to string, drop missing values, remove leading/trailing whitespace
                keywords = df['keyword'].dropna().astype(str).str.strip().tolist()
            elif not df.empty:
                # Use first column if 'keyword' column doesn't exist
                keywords = df.iloc[:, 0].dropna().astype(str).str.strip().tolist()
            # Remove empty strings after stripping
            keywords = [kw for kw in keywords if kw]
        except ValueError as ve:
             error_message = str(ve) # Catch specific decoding error
        except Exception as e:
            # General error catching during CSV parsing
            error_message = f"Error reading or parsing CSV: {e}"
            return [], error_message # Return empty list and error

    elif source_type == "text" and input_data:
        # Split by newline, strip whitespace, filter out empty lines
        keywords = [kw.strip() for kw in input_data.splitlines() if kw.strip()]

    # Remove duplicates from the final list
    unique_keywords = list(dict.fromkeys(keywords)) # Preserves order while removing duplicates
    return unique_keywords, error_message # Return keywords and None if no error

def get_language_list():
    """
    Returns a list of language names for the dropdown, using pycountry.
    Handles potential LookupError if locale data is missing.
    """
    default_list = ["English", "Spanish", "French", "German", "Dutch", "Italian"] # Fallback
    try:
        langs = [(lang.name, lang.alpha_2) for lang in pycountry.languages] # (Name, ISO Code)
        # Sort by name
        langs.sort(key=lambda x: x[0])
        # Extract names
        lang_names = [lang[0] for lang in langs]
        # Ensure English is present and put it first
        if "English" in lang_names:
             lang_names.remove("English")
             return ["English"] + lang_names
        else:
             # If English wasn't in the pycountry list for some reason, add it manually
             return ["English"] + lang_names
    except LookupError:
        # Fallback if pycountry data isn't available on the system
        print("Warning: pycountry locale data not found. Using a basic language list.")
        return default_list
    except Exception as e:
        # Catch any other unexpected errors during language list generation
        print(f"Error generating language list: {e}. Using a basic list.")
        return default_list

# Removed generate_language_options function (moved to app.py)
# Removed convert_df_to_csv function (moved to app.py)