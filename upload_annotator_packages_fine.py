import os
import json
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

uri = f"mongodb+srv://{open(os.path.join('..', 'mongodb_clinicalqa_uri.txt')).read().strip()}/?retryWrites=true&w=majority&appName=clinicalqa"

# Create a new client and connect to the server
client = MongoClient(uri)

# Send a ping to confirm a successful connection
try:
    client.admin.command("ping")
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)

output_dir = os.path.join(os.getcwd(), "output")


# def upload_pilot():
#     db = client["fine-test"]  # Replace with your database name
#     annotators = [f"annotator{n}" for n in range(1, 7)]
#     for annotator in annotators:
#         for annotation_type in ["`coarse`"]:  # ,'fine']:
#             key = f"{annotator}_{annotation_type}"
#             with open(
#                 os.path.join(
#                     output_dir, "pilot", f"batches_pilot_{annotation_type}.jsonl"
#                 ),
#                 "r",
#                 encoding="utf-8",
#             ) as jsonl_file:
#                 batches = [json.loads(line) for line in jsonl_file]
#             result = db[key].insert_many(batches)
#             print(key)
#             print(f"Inserted {len(result.inserted_ids)} documents into the collection.")


def upload_annotations(typ):

    db = client["fine-test"]  # Replace with your database name

    annotator_l = [i for i in range(1, 2)]
    for n in annotator_l:

        key = f"annotator{n}"
        print(key)
        # Read JSONL file and insert into MongoDB
        with open(
            os.path.join(output_dir, "all", f"{key}_{typ}.jsonl"), "r", encoding="utf-8"
        ) as jsonl_file:
            annotations = [
                json.loads(line) for line in jsonl_file
            ]  # Parse each line as JSON

        # Insert documents into the collection
        result = db[f"{key}"].insert_many(annotations)

        print(f"Inserted {len(result.inserted_ids)} documents into the collection.")


def read_annotations():
    db = client["fine-test"]
    annotator_l = [i for i in range(1, 2)]
    for n in annotator_l:
        key = f"annotator{n}"
        print(f"Reading documents from collection: {key}")
        documents = db[key].find({"rated": "Yes"})
        for doc in documents:
            print(doc)


def delete_annotations():
    db = client["fine-test"]
    annotator_l = [i for i in range(1, 2)]
    for n in annotator_l:
        key = f"annotator{n}"
        result = db[key].delete_many({})


if __name__ == "__main__":
    # upload_pilot()
    upload_annotations("fine")
    # read_annotations()
    # delete_annotations()
