# Prerequesit Create Notion Integration
# Create a database in Notion and share to get the database ID - https://www.youtube.com/watch?v=M1gu9MDucMA&list=PLe0U7sHuld_qIILgg-2ESRCPWu-WBalFJ&index=42
"""
How to set up the Notion API
How to set up the Python code
How to create database entries
How to query the database
How to update database entries
And how to delete entries.

"""

import requests
from datetime import datetime, timezone

NOTION_TOKEN = ""
DATABASE_ID = ""

headers = {
    "Authorization": "Bearer "+NOTION_TOKEN,
    "Content-Type": "application/json",
    "Notion-Version": "2024-06-28"
}

#Creating pages in your Notion database
def create_page(data: dict):
    create_url = "https://api.notion.com/v1/pages"

    payload = {"parent": {"database_id": DATABASE_ID}, "properties": data}

    res = requests.post(create_url, headers=headers, json=payload)
    # print(res.status_code)
    return res

from datetime import datetime, timezone

title = "Test Title"
description = "Test Description"
published_date = datetime.now().astimezone(timezone.utc).isoformat()
data = {
    "URL": {"title": [{"text": {"content": description}}]},
    "Title": {"rich_text": [{"text": {"content": title}}]},
    "Published": {"date": {"start": published_date, "end": None}}
}
https://developers.notion.com/reference/intro
create_page(data)
The corresponding data fields have to correspond to your table column names.

The schema might look a bit complicated and differs for different data types (e.g. text, date, boolean etc.). To determine the exact schema, I recommend dumping the data (see next step) and inspecting the JSON file.

In our example, we create data for the URL, the Title, and the Published columns like so:

def get_pages(num_pages=None):
    """
    If num_pages is None, get all pages, otherwise just the defined number.
    """
    url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"

    get_all = num_pages is None
    page_size = 100 if get_all else num_pages

    payload = {"page_size": page_size}
    response = requests.post(url, json=payload, headers=headers)

    data = response.json()

    # Comment this out to dump all data to a file
    # import json
    # with open('db.json', 'w', encoding='utf8') as f:
    #    json.dump(data, f, ensure_ascii=False, indent=4)

    results = data["results"]
    while data["has_more"] and get_all:
        payload = {"page_size": page_size, "start_cursor": data["next_cursor"]}
        url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"
        response = requests.post(url, json=payload, headers=headers)
        data = response.json()
        results.extend(data["results"])

    return results

Querying Notion database and reading pages¶
To query your database and read all entries, we can use the following function. It uses pagination to retrieve all entries:
pages = get_pages()

for page in pages:
    page_id = page["id"]
    props = page["properties"]
    url = props["URL"]["title"][0]["text"]["content"]
    title = props["Title"]["rich_text"][0]["text"]["content"]
    published = props["Published"]["date"]["start"]
    published = datetime.fromisoformat(published)
    
Updating pages in your Notion databse¶
To update a page, we have to send a PATCH request:

def update_page(page_id: str, data: dict):
    url = f"https://api.notion.com/v1/pages/{page_id}"

    payload = {"properties": data}

    res = requests.patch(url, json=payload, headers=headers)
    return res
For example, if we want to update the Published field, we send the following data. It is the same schema as for creating the page:
    
    

update_page(page_id, update_data)

Deleting pages in your Notion database¶
Deleting a page is achieved with the same endpoint as for updating the page, but here we set the archived parameter to True:

def delete_page(page_id: str):
    url = f"https://api.notion.com/v1/pages/{page_id}"

    payload = {"archived": True}

    res = requests.patch(url, json=payload, headers=headers)
    return res