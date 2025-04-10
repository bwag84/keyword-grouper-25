# Goal

The goal is to create a Streamlit application that reliably groups keywords. Reliable meaning that the input and output are always the same. Input is either a CSV with keywords, or entered by a user in a field. Output is written to a SQL database. There will be a button with an option to export the database as CSV.

# Grouping

Grouping by matching keywords word for word is not what we want. We want group on semantic meaning. 

Semantic grouping means organizing keywords based on their meaning and the user's underlying intent, rather than just the exact words used. It's about understanding what the searcher is really looking for.

This is why we will use an LLM API. This will be used to interpret meaning.


# Expected output

Since we will be using the output to upload to different tools we need a coherent database structure. 

We need to able to drill down into categories. So we would need at least three levels. Main category and two subcategories. 

All cells must be populated, so the columns will have duplicate values.
- Column 1: main_cat
- Column 2: sub_cat_1
- Column 3: sub_cat_2
- Column 4: the keywords
- Column 5: language per keyword
- Column 6: Semantic theme. A short description of the intention of the keyword group.
- Column 7: date of addition to the database


# Tool features

The tool will have the following features:

- Ability to upload a CSV with keywords
- Ability to paste up to 250 keywords in a field
- Button to activate the grouping
- LLM selection
	- Claude
	- OpenAI
	- Gemini
	- Mistral
- Language selection in a drop down.
	- Default: English
	- The drop down will contain all languages in the world
	- The dropdown can be controlled by typing
- It will have a database explorer
	- A field that allows you to view results in browser
- CSV export for the for the database
- Use python_dotenv
- Use pandas
- Prompt tuning: a text field that contains the version of the prompt for the LLM. Users can adjust on the fly by typing in a new prompt.
- 

## Other

Suggest requirements.txt
Suggest a .env


# Example

Example Scenario:

Imagine you run an online store selling gardening supplies, and you've brainstormed or researched a list of potential keywords people might search for:

Initial Ungrouped Keyword List:

vegetable seeds for sale
buy tomato seeds online
best soil for raised beds
how to start a vegetable garden
organic potting mix
heirloom tomato seeds
raised garden bed kits
garden soil delivery
what soil do vegetables need
buy raised garden bed
pepper seeds for sale
compost for garden
starting seeds indoors tips
cheap vegetable seeds
Semantic Grouping Applied:

Now, let's group these based on the meaning and likely user intent:

Group 1: Buying Seeds (Transactional Intent)

Semantic Theme: User wants to purchase specific types of seeds.
Keywords:
vegetable seeds for sale
buy tomato seeds online
heirloom tomato seeds
pepper seeds for sale
cheap vegetable seeds

Group 2: Buying Soil & Compost (Transactional Intent)
Semantic Theme: User wants to purchase soil or compost.
Keywords:
organic potting mix
garden soil delivery
compost for garden

Group 3: Buying Raised Garden Beds (Transactional Intent)
Semantic Theme: User wants to purchase raised garden beds.
Keywords:
raised garden bed kits
buy raised garden bed
Group 4: Soil Information & Advice (Informational Intent)

Semantic Theme: User is researching the best type of soil for their needs.
Keywords:
best soil for raised beds
what soil do vegetables need
Group 5: Gardening How-To & Advice (Informational Intent)

Semantic Theme: User is looking for instructions or tips on how to garden.
Keywords:
how to start a vegetable garden
starting seeds indoors tips