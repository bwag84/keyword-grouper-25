# app.py

import streamlit as st
import pandas as pd
from dotenv import load_dotenv
import os
import time # For progress simulation

# Import database and LLM utilities
from db_utils import add_keyword_grouping, get_existing_grouping, get_all_data
from llm_utils import get_llm_grouping

# Import specific functions from utils
from utils import parse_keywords, get_language_list # Import base function

# Load environment variables FROM .env file in the same directory
load_dotenv()

# --- App Configuration ---
st.set_page_config(page_title="Semantic Keyword Grouper", layout="wide")
st.title("🧠 Semantic Keyword Grouper")
st.markdown("""
Upload or paste keywords, choose an LLM and language, and group them based on semantic meaning.
Results are stored reliably in a database (`keyword_groups.db`). Last Updated: April 10, 2025.
""")

# --- Functions defined within app.py that need Streamlit context ---

@st.cache_data # Cache the list generation - DEFINED IN APP.PY
def generate_language_options():
    """Generates the language list by calling the utility function."""
    # This function now exists within the Streamlit script's context
    return get_language_list() # Calls the function imported from utils.py

@st.cache_data # Cache the CSV conversion - DEFINED IN APP.PY
def convert_df_to_csv(df: pd.DataFrame) -> bytes:
   """Converts DataFrame to CSV bytes, ready for download."""
   # This function now exists within the Streamlit script's context
   return df.to_csv(index=False).encode('utf-8')

# --- Global Variables & Session State ---
# Initialize session state variables if they don't exist to persist across reruns
if 'processing' not in st.session_state:
    st.session_state.processing = False # Flag to prevent multiple simultaneous runs
if 'results' not in st.session_state:
    st.session_state.results = None # Stores results of the last processing run
if 'error_message' not in st.session_state:
    st.session_state.error_message = None # Stores general error messages

# --- Sidebar for Configuration ---
with st.sidebar:
    st.header("⚙️ Configuration")

    # LLM Selection
    llm_options = ["OpenAI", "Gemini", "Claude", "Mistral"]
    selected_llm = st.radio(
        "1. Choose LLM:",
        llm_options,
        horizontal=True,
        help="Select the Large Language Model to use for grouping."
        )

    # API Key Input (Commented out - prefer .env but kept for reference)
    # st.info("API keys should ideally be set in your .env file.")
    # api_key_input = st.text_input(f"Enter {selected_llm} API Key (if not in .env)", type="password")
    # Note: Accessing the correct key based on selection needs logic if using this input

    # Language Selection
    st.markdown("---") # Separator
    language_options = generate_language_options() # Calls the cached function defined above
    selected_language = st.selectbox(
        "2. Select Keyword Language:",
        language_options,
        index=0, # Default to the first item (which should be English)
        help="Select the primary language of the keywords you are providing."
    )

    # Prompt Tuning
    st.markdown("---") # Separator
    st.subheader("🔧 Prompt Tuning (Advanced)")
    default_prompt = os.getenv("DEFAULT_LLM_PROMPT", """Analyze the following keyword: '{keyword}' (Language: {language}).
1. Determine the core semantic theme or user intent behind searching for this keyword.
2. Categorize the keyword into a 3-level hierarchy: Main Category, Sub Category 1, Sub Category 2. These categories should reflect the semantic grouping. Ensure all levels are populated, using 'General' or 'N/A' if a level isn't clearly distinct, but avoid leaving them blank.
3. Provide the output ONLY in the following JSON format, ensuring no extra text before or after the JSON block:
{{
  "main_cat": "...",
  "sub_cat_1": "...",
  "sub_cat_2": "...",
  "semantic_theme": "..."
}}""")
    custom_prompt = st.text_area(
        "LLM Prompt Template:",
        value=default_prompt,
        height=300,
        help="Use {keyword} and {language} placeholders. The LLM's response MUST be parsable JSON matching the requested structure. Changing this prompt means keywords may need re-processing."
    )
    st.caption("⚠️ Changing the prompt will result in different groupings and requires re-processing existing keywords as the 'prompt hash' used for caching will change.")

# --- Main Application Area ---

# Input Section
st.header("1. Input Keywords")
input_method = st.radio("Choose input method:", ("Upload CSV", "Paste Keywords"), horizontal=True, key="input_method")

keywords_to_process = []
input_error = None # Variable to store potential parsing errors

if input_method == "Upload CSV":
    uploaded_file = st.file_uploader(
        "Upload a CSV file",
        type=['csv'],
        help="CSV should have keywords in the first column, or a column named 'keyword'. One keyword per row."
        )
    if uploaded_file:
        # Pass the uploaded file object directly to parse_keywords
        with st.spinner("Reading CSV file..."):
             keywords_to_process, input_error = parse_keywords(uploaded_file, "csv")

        if input_error:
            st.error(f"❌ Error reading CSV: {input_error}") # Display error if parsing failed
            keywords_to_process = [] # Ensure list is empty on error
        elif not keywords_to_process:
             st.warning("⚠️ No keywords found in the uploaded CSV file.")
        else:
            st.success(f"✅ Found {len(keywords_to_process)} unique keywords in '{uploaded_file.name}'.")
            with st.expander("Preview first 5 keywords"):
                 st.text('\n'.join(keywords_to_process[:5]))


else: # Paste Keywords
    pasted_keywords = st.text_area(
        "Paste keywords (one per line, max 250):",
        height=150,
        key="pasted_keywords_area"
        )
    if pasted_keywords:
        all_pasted, input_error = parse_keywords(pasted_keywords, "text")

        if input_error: # Should be less likely for text input
            st.error(f"Error processing pasted text: {input_error}")
            keywords_to_process = []
        elif len(all_pasted) > 250:
            st.warning(f"⚠️ Input limit reached. Processing the first 250 unique keywords ({len(all_pasted)} found).")
            keywords_to_process = all_pasted[:250]
        else:
            keywords_to_process = all_pasted

        if keywords_to_process and not input_error:
            st.success(f"✅ Ready to process {len(keywords_to_process)} unique keywords.")
        elif not keywords_to_process and not input_error:
             st.warning("⚠️ Please paste some keywords.")


# Grouping Activation Button
st.header("2. Process Keywords")
st.markdown("Click the button below to start grouping the provided keywords using the selected LLM and prompt.")

# Disable button if already processing, if there are no keywords, or if there was an input error
process_button_disabled = st.session_state.processing or not keywords_to_process or input_error is not None

if st.button("✨ Group Keywords Semantically ✨", disabled=process_button_disabled, type="primary"):

    if not keywords_to_process: # Should be caught by disabled state, but double-check
         st.warning("Please provide keywords via upload or pasting before processing.")
    elif input_error: # Should also be caught by disabled state
         st.error(f"Cannot proceed due to input error: {input_error}")
    else:
        # --- Start Processing ---
        st.session_state.processing = True
        st.session_state.results = [] # Clear previous results
        st.session_state.error_message = None # Clear previous general errors
        total_keywords = len(keywords_to_process)
        processed_count = 0
        errors = 0
        llm_calls = 0
        cache_hits = 0

        # Display progress bar and status text
        st.info(f"Starting processing for {total_keywords} keywords using {selected_llm}...")
        progress_bar = st.progress(0)
        status_text = st.empty() # Placeholder to update status dynamically

        start_time = time.time()

        # --- Keyword Processing Loop ---
        for i, keyword in enumerate(keywords_to_process):
            current_progress = (i + 1) / total_keywords
            status_text.text(f"⚙️ Processing keyword {i+1}/{total_keywords}: '{keyword}' (Cache Hits: {cache_hits}, LLM Calls: {llm_calls}, Errors: {errors})")
            progress_bar.progress(current_progress)

            # 1. Check Cache (Database) first to save API calls and ensure reliability
            try:
                existing = get_existing_grouping(keyword, selected_language, custom_prompt)
            except Exception as db_err:
                 st.error(f"Database error checking cache for '{keyword}': {db_err}")
                 errors += 1
                 # Optionally add placeholder error result
                 st.session_state.results.append({"keyword": keyword, "language": selected_language, "main_cat": "DB_ERROR", "sub_cat_1": "DB_ERROR", "sub_cat_2": "DB_ERROR", "semantic_theme": f"DB Check Error: {db_err}"})
                 continue # Skip to next keyword

            if existing:
                # Cache Hit! Use existing data
                cache_hits += 1
                grouping_data = {
                    "keyword": keyword,
                    "language": selected_language,
                    "main_cat": existing.get('main_cat', 'N/A'), # Use .get for safety
                    "sub_cat_1": existing.get('sub_cat_1', 'N/A'),
                    "sub_cat_2": existing.get('sub_cat_2', 'N/A'),
                    "semantic_theme": existing.get('semantic_theme', 'N/A'),
                    "_source": "cache" # Add metadata for clarity
                }
                st.session_state.results.append(grouping_data)
                processed_count += 1
            else:
                # 2. Cache Miss: Call LLM
                llm_calls += 1
                try:
                    # Add a small delay to be kind to APIs, prevent rate limits
                    time.sleep(0.5) # Adjust as needed (0.5s to 1s is often safe)

                    llm_result = get_llm_grouping(keyword, selected_language, selected_llm, custom_prompt)

                    # 3. Parse LLM Response and Validate
                    if llm_result and isinstance(llm_result, dict) and \
                       'main_cat' in llm_result and 'sub_cat_1' in llm_result and \
                       'sub_cat_2' in llm_result and 'semantic_theme' in llm_result:

                        # Ensure all fields are populated strings (as requested in prompt instructions)
                        main_cat = str(llm_result.get('main_cat', 'Uncategorized')).strip() or 'Uncategorized'
                        sub_cat_1 = str(llm_result.get('sub_cat_1', 'General')).strip() or 'General'
                        sub_cat_2 = str(llm_result.get('sub_cat_2', 'Detail')).strip() or 'Detail'
                        semantic_theme = str(llm_result.get('semantic_theme', 'N/A')).strip() or 'N/A'

                        # 4. Store valid result in DB
                        try:
                             add_keyword_grouping(
                                 keyword, selected_language, custom_prompt,
                                 main_cat, sub_cat_1, sub_cat_2, semantic_theme
                             )
                        except Exception as db_add_err:
                             st.error(f"Database error saving result for '{keyword}': {db_add_err}")
                             errors += 1
                             # Still add to session results, but mark as DB error source
                             st.session_state.results.append({"keyword": keyword, "language": selected_language, "main_cat": main_cat, "sub_cat_1": sub_cat_1, "sub_cat_2": sub_cat_2, "semantic_theme": semantic_theme, "_source": "llm_db_error"})
                             continue # Skip adding to processed_count if DB save failed maybe? Or count it? Currently counted.

                        # Add successful LLM result to session results
                        grouping_data = {
                            "keyword": keyword, "language": selected_language,
                            "main_cat": main_cat, "sub_cat_1": sub_cat_1,
                            "sub_cat_2": sub_cat_2, "semantic_theme": semantic_theme,
                            "_source": "llm" # Add metadata
                        }
                        st.session_state.results.append(grouping_data)
                        processed_count += 1

                    else:
                        # Handle invalid/incomplete LLM response
                        st.warning(f"⚠️ LLM response for '{keyword}' was incomplete or not valid JSON. Check LLM logs/prompt. Response: {llm_result}")
                        errors += 1
                        st.session_state.results.append({"keyword": keyword, "language": selected_language, "main_cat": "LLM_ERROR", "sub_cat_1": "LLM_ERROR", "sub_cat_2": "LLM_ERROR", "semantic_theme": f"Invalid/Incomplete LLM Response: {str(llm_result)[:100]}...", "_source": "llm_error"})

                except Exception as e:
                    # Handle errors during the LLM call itself
                    st.error(f"❌ Error processing keyword '{keyword}' with {selected_llm}: {e}")
                    errors += 1
                    st.session_state.results.append({"keyword": keyword, "language": selected_language, "main_cat": "LLM_ERROR", "sub_cat_1": "LLM_ERROR", "sub_cat_2": "LLM_ERROR", "semantic_theme": f"API/Processing Error: {e}", "_source": "llm_error"})


        # --- Processing Finished ---
        end_time = time.time()
        elapsed_time = end_time - start_time
        status_text.success(f"✅ Processing Complete! ({elapsed_time:.2f}s) | Processed: {processed_count}, Cache Hits: {cache_hits}, LLM Calls: {llm_calls}, Errors: {errors}")
        st.session_state.processing = False
        # Rerun to update the display below the button correctly
        st.rerun()


# Display results from the latest run (if any)
if st.session_state.results is not None: # Check if results exist in state
    st.header("3. Grouping Results (Latest Run)")
    if st.session_state.results: # Check if the results list is not empty
        results_df = pd.DataFrame(st.session_state.results)
        # Define desired column order, including the _source metadata if needed
        display_cols = ['main_cat', 'sub_cat_1', 'sub_cat_2', 'keyword', 'language', 'semantic_theme', '_source']
        # Filter out columns that might not exist if _source wasn't added in all cases
        display_cols = [col for col in display_cols if col in results_df.columns]
        st.dataframe(results_df[display_cols])
        st.caption(f"Displaying {len(results_df)} results from the last processing run.")
    elif not st.session_state.processing: # Only show 'no results' if not currently processing
        st.info("No results were generated in the last run, or only errors occurred.")

# Display general error messages if any
if st.session_state.error_message:
    st.error(st.session_state.error_message)


# --- Database Explorer Section ---
st.header("📊 Database Explorer")
st.markdown("View and export all grouped keywords currently stored in the database.")

# Add a refresh button for the database view
if st.button("🔄 Refresh Database View"):
    # Clear specific caches if needed, though Streamlit usually handles reruns well
    # get_all_data might benefit from @st.cache_data in db_utils if reads are slow & frequent
    st.rerun() # Rerun the script to fetch fresh data

try:
    # Fetch all data from the database
    all_db_data = get_all_data() # This function is in db_utils.py

    if not all_db_data.empty:
        st.dataframe(all_db_data, use_container_width=True)
        st.caption(f"Total records in database: {len(all_db_data)}")

        # CSV Export Button for the *entire* database
        st.subheader("Export Full Database")
        csv_data = convert_df_to_csv(all_db_data) # Calls the cached function defined in app.py

        # Get database name from environment or use default for filename
        db_file_name_base = os.getenv("DATABASE_NAME", "keyword_groups.db").split('.')[0]

        st.download_button(
           label="📥 Download Full Database as CSV",
           data=csv_data,
           file_name=f'{db_file_name_base}_export_{time.strftime("%Y%m%d_%H%M%S")}.csv', # Add timestamp
           mime='text/csv',
           key='download_db_csv'
        )
    else:
        st.info("ℹ️ The keyword database is currently empty. Process some keywords to populate it.")
except Exception as e:
    st.error(f"❌ Failed to load or display data from database: {e}")
    st.exception(e) # Show full traceback for debugging if needed