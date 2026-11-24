AI was not used by either of us for P1.


Give me a sample API call in Python for the Google Gemini API (free tier). Make it take an image and return tags based on the image's vibe. The code should fulfill this spec:

Takes an image file path (JPG, PNG, or WEBP) and sends the image to Gemini.
Asks Gemini this prompt:
Look at this image and describe its mood and aesthetic.
Return 3 to 6 short tags that would work as music tags on Last.fm
(moods like "melancholic" or "chill", or genres like "dream pop" or "lo-fi").
Respond only with JSON: {"tags": ["tag1", "tag2", ...]}
Uses the official google-genai Python library and a Flash model that is available on the free tier. Put the model name in one variable at the top and tell me how to check that the name is current.
Uses structured output (response schema) so Gemini always returns valid JSON with a "tags" list of strings.
Cleans up the tags: lowercase, trimmed, no duplicates, at most 6.
Matches the style of my partner's Last.fm script:

Finds the .env file in the current folder or parent folders (asks for the path if not found) and loads the key with python-dotenv, using the key name GeminiKey. Raises a clear error if the key is missing. Prints progress messages, then prints the final result as formatted JSON: {"tags": [...]}

Handles errors clearly: image file not found, unsupported file type, and rate limit (429) errors.
Tell me which packages to pip install, and show an example of what the output looks like.

I've written gemini_image_tags.py to your spec. I tested it with a fake Gemini response, not a real API call. The tag cleanup worked, and so did the errors for a missing file, an unsupported type (.gif) and a 429 rate limit.

1. Install the packages
bash
pip install google-genai python-dotenv

pydantic comes with google-genai, so you don't need to install it separately.

2. Add your key to .env
GeminiKey=your_api_key_here
3. Run it
bash
python gemini_image_tags.py photos/rainy_window.jpg
Example output
Looking for .env file...
Loaded .env from: /Users/bryce/projects/mood-playlist/.env
Reading image: rainy_window.jpg (image/jpeg)
Sending image to Gemini (gemini-3.5-flash)...
Response received. Cleaning up tags...
Done!

{
  "tags": [
    "melancholic",
    "rainy day",
    "lo-fi",
    "dream pop",
    "chill"
  ]
}
How the main parts work
Structured output (#4): The script defines a small Pydantic class, TagsResponse, with one field: tags: list[str]. It passes that class to Gemini as response_schema. A response schema is a template the model's answer must follow, so Gemini has to send back JSON in that shape instead of loose text. The library then turns the reply into a TagsResponse object for you (response.parsed).
Tag cleanup (#5): clean_tags() lowercases each tag and trims the spaces. It also turns double spaces inside a tag into single ones, removes duplicates while keeping the original order, and keeps at most 6 tags.
Errors (#7): The script gives a clear message when:
the image file doesn't exist
the file type isn't JPG, PNG or WEBP
you hit a 429 rate limit
the model name isn't found (404)
the API key is bad
Google's servers have a problem
Checking the model name (#3)

The model name is in MODEL_NAME at the top of the file. I set it to gemini-3.5-flash because Google's pricing page lists it as "Free of charge" on the free tier. Google's own pages don't fully agree right now. The models page also lists newer Flash models, such as gemini-3.8-flash, but those don't appear in the pricing page's free-tier table yet. So it's worth checking the name yourself:

Open the models page and confirm the name is listed as Stable, not Preview or shut down.
Open the pricing page and confirm the "Free Tier" column for that model says Free of charge.
Run this quick check with your key to list the model names your key can use:
python
from google import genai
client = genai.Client(api_key="YOUR_KEY")
for m in client.models.list():
    if "flash" in m.name:
        print(m.name)
If the script ever stops with the "Model … was not found (404)" error, the name has been retired. Change MODEL_NAME to a current one.


My explanation for gemini_api_test_code:
The imports make the code runnable when pip install google-genai python-dotenv is ran in an venv. The variables at the top are there and are in all caps because they're not meant to change. load_api_key is there to get the api key from my .env. I just tested this by making sure my api_key wasn't null and didn't raise the error outlined in the method. load_image is the method that loads the image. It returns the image's bytes and mime type. clean_tags just makes the tags all uniform lowercase so they can be easily read. The get_image_tags calls Gemini with the prompt and notifies the user. It's in a try catch so if it doesn't work, the whole app doesn't crash. Main just does the code to display the tags. 

Write a live api call from last.fm API in python code that works for an interactive terminal, my key is in a .env
Here's the full Python code that searches for your .env file, loads LastFmKey, calls the Last.fm API, and prints 5 songs matching the "dream pop" aesthetic.
1. Install dependencies
Run this in your terminal:
pip install requests python-dotenv


2. Full Python code
Save this as lastfm_test.py in your project folder.
import osimport jsonfrom pathlib import Pathimport requestsfrom dotenv import load_dotenv# STEP 1: Find your .env file# Searches current folder and parent folderscurrent_folder = Path.cwd()script_folder = Path(__file__).resolve().parentenv_path = Nonefor folder in [script_folder, *script_folder.parents,               current_folder, *current_folder.parents]:    candidate = folder / ".env"    if candidate.is_file():        env_path = candidate        breakif env_path is None:    raise FileNotFoundError(        "Could not find .env file.\n"        f"Current folder: {current_folder}\n"        "Move your .env file into the same folder as lastfm_test.py."    )# STEP 2: Load your API keyload_dotenv(dotenv_path=env_path, override=True)API_KEY = os.getenv("LastFmKey")



3. Make sure your project looks like this
my-project/
│
├── .env
└── lastfm_test.py


Inside .env:
LastFmKey=your_actual_api_key_here


Make sure the file is named exactly .env, not .env.txt.
4. Run the code
Open your terminal in your project folder and run:
python lastfm_test.py


You should see something similar to:
API key loaded successfully!
Using .env from: /path/to/my-project/.env

Searching Last.fm for dream pop songs...

API RESPONSE:
{
  "songs": [
    {
      "name": "Space Song",
      "artist": "Beach House",
      "url": "https://www.last.fm/music/Beach+House/_/Space+Song"
    }
  ]
}


The song data above is illustrative; your actual results will come from Last.fm.
