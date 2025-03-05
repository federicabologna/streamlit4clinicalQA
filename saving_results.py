import os
import json
from pymongo import MongoClient

def export_annotations_to_jsonl(mongo_uri, db_name, output_file):
    # Connect to MongoDB
    client = MongoClient(mongo_uri)
    db = client[db_name]
    
    # Retrieve all collections
    collection_names = db.list_collection_names()
    
    with open(os.path.join('output', output_file), 'w', encoding='utf-8') as f:
        total_docs = 0
        for collection_name in collection_names:
            collection = db[collection_name]
            documents = collection.find({"rated": "Yes"})
            for doc in documents:
                doc['_id'] = str(doc['_id'])  # Convert ObjectId to string
                f.write(json.dumps(doc) + '\n')
                total_docs += 1
    
    print(f"Exported {total_docs} documents to {output_file}")
    
    # Close the connection
    client.close()

# Example usage
uri = f"mongodb+srv://{open(os.path.join('..', '..', 'PhD', 'apikeys', 'mongodb_clinicalqa_uri.txt')).read().strip()}/?retryWrites=true&w=majority&appName=clinicalqa"
client = MongoClient(uri)
db_name = "batches"  # Database containing multiple collections
output_file = "test_results_batches.jsonl"
export_annotations_to_jsonl(uri, db_name, output_file)