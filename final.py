import os
import openai
from bs4 import BeautifulSoup
from datetime import datetime
import json
import concurrent.futures
import time

openai.api_key = os.getenv("OPENAI_API_KEY")

# Define a function to process a single anchor tag
def process_anchor_tag(index, tag):
    url = tag["href"]
    text = tag.get_text()
    result = getdic(url, text)
    
    if result is not None:
        json_content = result["choices"][0]["message"]["content"]
        parsed_content = json.loads(json_content)
        folder_name = parsed_content.get("folder_name", "No Folder Name")
        tags = parsed_content.get("tags", [])
        formatted_tags = "#" + " #".join(tags)

        tag.string = text + " " + formatted_tags + " " + "#" + folder_name

# Function to get OpenAI response
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
                    "content": "As an Artificial Intelligence specialist, you are provided with a URL ('" + url + "') and its corresponding anchor text ('"+ text +"'). Your task is to generate an appropriate folder name and the top three related tags for the purpose of bookmark organization. All the output should be provided in JSON format as instructed below:\n\n{\n  \"folder_name\": \"<REPLACEABLE>\",\n  \"tags\": [\"<REPLACEABLE>\", \"<REPLACEABLE>\", \"<REPLACEABLE>\"]\n}\n\nPlease note that the output should strictly follow the given JSON model, no additional words or explanations are necessary. The tags and folder_name should not have any space, add hyphens instead and folder_name must be a topic name and single word."
                }
            ],
            temperature=1,
            max_tokens=256,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0
        )
        
        if "error" in response:
            # Handle API response error here
            print(f"API Error: {response['error']['message']}")
            return None
        else:
            return response
    except Exception as e:
        # Handle other exceptions (e.g., network issues)
        print(f"Error: {e}")
        return None

# Input bookark file
html_file = "out.html"

flag = True

while flag:

    # Parse the HTML file
    try:
        with open(html_file, "r", encoding="utf-8") as file:
            soup = BeautifulSoup(file, "html.parser")
    except Exception as e:
        print(f"Error while parsing HTML file: {e}")
        soup = None

    if soup is not None:
        anchor_tags = soup.find_all("a")

        # Initialize a list to store futures
        futures = []

        with open("index.txt", "r", encoding="utf-8") as count_file:
            count = int(count_file.read())

        start_time = time.time()
        max_execution_time = 150  # 150 seconds

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            for index, tag in enumerate(anchor_tags[count:], count):
                future = executor.submit(process_anchor_tag, index, tag)
                futures.append(future)

                # If the length of futures is a multiple of 10, wait for them to complete
                if len(futures) % 10 == 0:
                    # Wait for the last 10 submitted tasks to complete before saving
                    concurrent.futures.wait(futures[-10:])

                    # Check if the execution time exceeds the threshold
                    if time.time() - start_time >= max_execution_time:
                        print("Process took too long. Restarting from the last index.")
                        flag = True
                        break
                    else:
                        flag = False

                    # save for each 10 responses
                    with open("out.html", "w", encoding="utf-8") as output_file:
                        output_file.write(str(soup))

                    # counter to continue form where it was stopped
                    with open("index.txt", "w", encoding="utf-8") as output_file:
                        output_file.write(str(index))
                time.sleep(1)
            

        if(flag == True):
            continue
print("Its done!!!")