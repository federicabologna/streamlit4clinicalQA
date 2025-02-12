import os
import json
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

uri = f"mongodb+srv://{open(os.path.join('..', '..', 'PhD', 'apikeys', 'mongodb_clinicalqa_uri.txt')).read().strip()}/?retryWrites=true&w=majority&appName=clinicalqa"

# Create a new client and connect to the server
client = MongoClient(uri)

# Send a ping to confirm a successful connection
try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)

output_dir = os.path.join(os.getcwd(), 'output')
db = client['annotations']  # Replace with your database name

annotator_l = [i for i in range(1,7)]

for n in annotator_l:

    key = f'annotator{n}'
    print(key)
    # Read JSONL file and insert into MongoDB
    with open(os.path.join(output_dir, f"{key}_coarse.jsonl"), 'r', encoding='utf-8') as jsonl_file:
        coarse = [json.loads(line) for line in jsonl_file][:9]  # Parse each line as JSON

    with open(os.path.join(output_dir, f"{key}_fine.jsonl"), 'r', encoding='utf-8') as jsonl_file:
        fine = [json.loads(line) for line in jsonl_file][:51]  # Parse each line as JSON

    # Insert documents into the collection
    result_coarse = db[f'{key}_coarse'].insert_many(coarse)
    result_fine = db[f'{key}_fine'].insert_many(fine)

    print(f"Inserted {len(result_coarse.inserted_ids)} documents into the collection.")
    print(f"Inserted {len(result_fine.inserted_ids)} documents into the collection.")