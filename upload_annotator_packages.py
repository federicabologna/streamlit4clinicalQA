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


def upload_pilot(pilot_name):
    db = client[pilot_name]  # Replace with your database name
    annotators = [f'annotator{n}' for n in range(1,7)]
    for annotator in annotators:
        key = f'{annotator}'
        with open(os.path.join(output_dir, 'pilot', f"{pilot_name}.jsonl"), 'r', encoding='utf-8') as jsonl_file:
            batches = [json.loads(line) for line in jsonl_file]
        result = db[key].insert_many(batches)
        print(key)
        print(f"Inserted {len(result.inserted_ids)} documents into the collection.")


def upload_annotations(typ):

    db = client[typ]  # Replace with your database name

    annotator_l = [i for i in range(1,7)]
    for n in annotator_l:

        key = f'annotator{n}'
        print(key)
        # Read JSONL file and insert into MongoDB
        with open(os.path.join(output_dir, 'all', f"{key}_{typ}_sampled.jsonl"), 'r', encoding='utf-8') as jsonl_file:
            annotations = [json.loads(line) for line in jsonl_file]  # Parse each line as JSON

        # Insert documents into the collection
        result = db[f'{key}'].insert_many(annotations)

        print(f"Inserted {len(result.inserted_ids)} documents into the collection.")

if __name__ == "__main__":
    upload_pilot('pilot1_fine')
    # upload_annotations('fine2')