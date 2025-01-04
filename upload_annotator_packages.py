import os
import json
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

uri = "mongodb+srv://fb265:Y1lWAOSUn4YEETPf@clinicalqa.302z0.mongodb.net/?retryWrites=true&w=majority&appName=clinicalqa"

# Create a new client and connect to the server
client = MongoClient(uri)

# Send a ping to confirm a successful connection
try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)

dir = os.getcwd()
data_dir = os.path.join(dir, 'data')
os.makedirs(data_dir, exist_ok=True)

db = client['annotations']  # Replace with your database name
collection = db['annotator1']  # Replace with your collection name

# Read JSONL file and insert into MongoDB
with open(os.path.join(data_dir, "annotator1.jsonl"), 'r', encoding='utf-8') as jsonl_file:
    documents = [json.loads(line) for line in jsonl_file]  # Parse each line as JSON

# Insert documents into the collection
result = collection.insert_many(documents)

print(f"Inserted {len(result.inserted_ids)} documents into the collection.")