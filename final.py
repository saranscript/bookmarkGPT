import os 
import openai 
from bs4 import BeautifulSoup 
from datetime import datetime 
import json 
import concurrent.futures 
import time
from concurrent.futures import ThreadPoolExecutor, as_completed


openai.api_key = os.getenv("OPENAI_API_KEY")

def process_anchor_tag(index, tag): 
    url = tag["href"] 
    text = tag.get_text() 
    result = getdic(url, text)
    
    if result:
        json_content = result["choices"][0]["message"]["content"] 
        parsed_content = json.loads(json_content) 
        folder_name = parsed_content.get("folder_name", "No Folder Name") 
        tags = parsed_content.get("tags", []) 
        formatted_tags = "#" + " #".join(tags)
        tag.string = text + " " + formatted_tags + " " + "#" + folder_name  

def getdic(url, text): 
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo-0613", 
            messages=[
                {
                    "role": "system",
                    "content": "You are an AI bookmark manager" 
                }, 
                {
                    "role": "assistant",
                    "content": "As an Artificial Intelligence specialist, you are provided with a URL ('" + url + "') and its corresponding anchor text ('"+ text +"'). Your task is to generate an appropriate folder name and the top three related tags for the purpose of bookmark organization. All the output should be provided in JSON format as instructed below:\n\n{\n \"folder_name\": \"<REPLACEABLE>\",\n \"tags\": [\"<REPLACEABLE>\", \"<REPLACEABLE>\", \"<REPLACEABLE>\"]\n}\n\nPlease note that the output should strictly follow the given JSON model, no additional words or explanations are necessary. The tags and folder_name should not have any space, add hyphens instead and folder_name must be a topic name and single word." 
                }
            ]
        )
        return response if "error" not in response else None
    
    except Exception as e: 
        print(f"Error: {e}")  
        return None

# Input bookark file
html_file = "out.html"

# Parse the HTML file
try: 
    with open(html_file, "r", encoding="utf-8") as file:
        soup = BeautifulSoup(file, "html.parser")  
except Exception as e: 
    print(f"Error while parsing HTML file: {e}") 
    soup = None
if soup is not None:
    anchor_tags = soup.find_all("a")
    
    # Get the count from index.txt
    with open("index.txt", "r", encoding="utf-8") as count_file:
        count = int(count_file.read())

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(process_anchor_tag, index, tag): index 
                   for index, tag in enumerate(anchor_tags[count:], count)}

        for future in as_completed(futures):
            index = futures[future]
            try:
                data = future.result()
            except Exception as exc:
                print(f'Tag generated an exception: {exc}')
            else:
                if index > 0 and index % 10 == 0:  # When 10 tasks are finished
                    # we save the current state of our Soup
                    with open("out.html", "w", encoding="utf-8") as output_file:
                        output_file.write(str(soup))
                    # and update the index
                    with open("index.txt", "w", encoding="utf-8") as output_file:
                        output_file.write(str(index + 1)) 
