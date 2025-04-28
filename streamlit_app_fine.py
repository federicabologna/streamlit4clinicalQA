import os
import json
import time
from datetime import datetime
from collections import OrderedDict
import streamlit as st
import pymongo
from pymongo.mongo_client import MongoClient
import random


# Set page configuration
st.set_page_config(layout="wide", page_title="Clinical QA - Fine Annotations")

# Initialize session state
if "page" not in st.session_state:
    st.session_state.page = 1
if "annotator_n" not in st.session_state:
    st.session_state.annotator_n = None
if "batch_n" not in st.session_state:
    st.session_state.batch_n = None
if "valid_batch_ns" not in st.session_state:
    st.session_state.valid_batch_ns = ["0", "1"]
if "annotation_id" not in st.session_state:
    st.session_state.annotation_id = None
if "responses_todo" not in st.session_state:
    st.session_state.responses_todo = []
if "responses_done" not in st.session_state:
    st.session_state.responses_done = []
if "times" not in st.session_state:
    st.session_state.times = {}

if "main_likert" not in st.session_state:
    st.session_state.main_likert = json.load(
        open(
            os.path.join(os.getcwd(), "data", f"main_likert.json"),
            "r",
            encoding="utf-8",
        )
    )
if "conf_likert" not in st.session_state:
    st.session_state.confidence_likert = json.load(
        open(
            os.path.join(os.getcwd(), "data", f"conf_likert.json"),
            "r",
            encoding="utf-8",
        )
    )
if "ease_likert" not in st.session_state:
    st.session_state.ease_likert = json.load(
        open(
            os.path.join(os.getcwd(), "data", f"ease_likert.json"),
            "r",
            encoding="utf-8",
        )
    )


def assign_states(key, corr, rel, saf, conf):
    st.session_state[f"corr_{key}"] = corr
    st.session_state[f"rel_{key}"] = rel
    st.session_state[f"saf_{key}"] = saf
    st.session_state[f"conf_{key}"] = conf


def likert2index(key):

    if key in st.session_state:
        if st.session_state[key] != None:
            if "conf" in key:
                d = st.session_state.confidence_likert
            else:
                d = st.session_state.main_likert
            s = st.session_state[key]
            return d[s]
        else:
            return None
    else:
        return None


def dispatch_batch():
    mongodb_credentials = st.secrets.mongodb_credentials
    uri = f"mongodb+srv://{mongodb_credentials}/?retryWrites=true&w=majority&appName=clinicalqa"
    client = MongoClient(uri)  # Create a new client and connect to the server
    db = client["fine2"]  # TEST DATABASE DO NOT CHANGE
    annotator_n = st.session_state.annotator_n
    batch_n = st.session_state.batch_n

    # annotator_n is the key used to access which set of annotations
    # b/c we inserted based on annotator# in upload.py
    annotations_collection = st.session_state.annotation_collection = db[
        f"annotator{annotator_n}"
    ]

    mongodb_result = [
        i
        for i in annotations_collection.find(
            {"$and": [{"rated": "No"}, {"batch_id": f"batch_{batch_n}"}]}
        )
    ]  # check if any fine annotations left
    
    grouped = OrderedDict()
    for item in mongodb_result:
        answer_id = item['answer_id']
        if answer_id not in grouped:
            grouped[answer_id] = []
        grouped[answer_id].append(item)
        
    for aid in grouped:
        grouped[aid] = sorted(grouped[aid], key=lambda x: int(x['sentence_id'].split('_')[-1]))

    clean_responses_todo = [item for group in grouped.values() for item in group]
    
    st.session_state.responses_todo = clean_responses_todo

    st.session_state.responses_left = len(st.session_state.responses_todo)


def identifiers_page1():
    st.header("Enter your Annotator #, Password, and Batch # to start the survey.")
    st.markdown(
        """**By entering your identifiers you confirm that you have read
                [the study's information](https://docs.google.com/document/d/1IElIVFlBgK-tVmoYeZFz5LsC1b8SoXTJZfGp4zIDvhI/edit?usp=sharing)
                and that you consent to participate in the study.**"""
    )

    # st.markdown('''### Instructions for testers:
    # Valid Annotator #: 2, 3, 4, 5, 6
    # Passwords:
    # * Annotator #2: tiger
    # * Annotator #3: panda
    # * Annotator #4: elephant
    # * Annotator #5: flamingo
    # * Annotator #6: dolphin
    # Valid Batch #: 0

    # If you receive the message: "You have completed all your fine annotation" all fine annotations in that annotator # package have been done. Please test a different annotator #
    # If you finish a batch you should see the message: You have completed the batch.''')

    annotator_n = st.text_input("Annotator #:")
    if annotator_n:
        if int(annotator_n) < 0 and int(annotator_n) > 6:
            st.write(":orange[Invalid Annotator #]")

    animals = json.load(
        open(os.path.join(os.getcwd(), "data", f"animals.json"), "r", encoding="utf-8")
    )
    password = st.text_input("Password:")
    if annotator_n and password and password != animals[str(annotator_n)]:
        st.write(":orange[Incorrect Password]")

    valid = st.session_state.valid_batch_ns
    batch_number = st.text_input("Batch #:")
    if batch_number and batch_number not in valid:
        st.write(":orange[Invalid Batch #]")

    leftleft, left, middle, right, rightright = st.columns(5)
    cond1 = (
        right.button("Next :arrow_forward:", use_container_width=True)
        and annotator_n
        and password
        and batch_number
        and password == animals[str(annotator_n)]
        and batch_number in valid
    )
    cond2 = (
        annotator_n
        and password
        and batch_number
        and password == animals[str(annotator_n)]
        and batch_number in valid
    )

    if cond1 or cond2:
        if annotator_n:
            st.session_state.annotator_n = annotator_n
            st.session_state.batch_n = batch_number
            st.write("Loading your annotations...")
            dispatch_batch()
            if len(st.session_state.responses_todo) > 0:
                st.session_state.page = 2
            else:
                st.session_state.page = 6
            st.rerun()
    else:
        st.write(":orange[Please enter the requested information.]")


def instructions_page2():

    with open(os.path.join(os.getcwd(), "data", "instructions.txt"), "r") as file:
        survey_instructions = file.read()
    st.markdown(survey_instructions, unsafe_allow_html=True)

    leftleft, left, middle, right, rightright = st.columns(5)
    if left.button(":arrow_backward: Back", use_container_width=True):
        st.session_state.page = st.session_state.page - 1
        st.rerun()

    elif right.button("Next :arrow_forward:", use_container_width=True):
        st.session_state.page = 3
        st.rerun()


def questions_page3():
    time.sleep(0.5)
    js = """
        <script>
            window.scrollTo({ top: 0, behavior: 'smooth' });
        </script>
        """
    st.components.v1.html(js, height=0)

    # Uncomment to check if sentences are displaying in the correct order.
    st.markdown([d["sentence_id"] for d in st.session_state.responses_todo])
    # st.markdown([d["answer_id"] for d in st.session_state.responses_todo])

    annotation_d = st.session_state.responses_todo[0]
    annotation_type = "fine"
    annotations_collection = st.session_state.annotation_collection

    annotation_id = annotation_d["sentence_id"]
    if annotation_id not in st.session_state.times.keys():
        st.session_state.times[annotation_id] = {"start": time.time()}

    col1, col2 = st.columns(2)
    with col1:
        st.header("Question")
        st.markdown(annotation_d["question"])

        st.header("Answer")

        st.markdown(annotation_d["answer"])

    with col2:
        st.subheader("The information provided in the answer:")
        likert_options = st.session_state.main_likert.keys()

        st.markdown("#### :green[aligns with current medical knowledge]")
        correctness = st.radio(
            ":green[aligns with current medical knowledge]",
            options=likert_options,
            horizontal=True,
            index=likert2index(
                f"corr_{annotation_id}"
            ),  # dynamically changes based on which annotation you're on
            label_visibility="hidden",
            key=f"c_{annotation_id}",
        )

        st.markdown("#### :blue[addresses the specific medical question]")
        relevance = st.radio(
            ":blue[addresses the specific medical question]",
            options=likert_options,
            horizontal=True,
            index=likert2index(f"rel_{annotation_id}"),
            label_visibility="hidden",
            key=f"r_{annotation_id}",
        )

        st.markdown("#### :violet[communicates contraindications or risks]")
        safety = st.radio(
            ":violet[communicates contraindications or risks]",
            options=likert_options,
            horizontal=True,
            index=likert2index(f"saf_{annotation_id}"),
            label_visibility="hidden",
            key=f"s_{annotation_id}",
        )

    with st.expander(":clipboard: **See Annotation Instructions**"):
        with open(os.path.join(os.getcwd(), "data", "instructions.txt"), "r") as file:
            survey_instructions = file.read()
        st.markdown(survey_instructions, unsafe_allow_html=True)

    col1, col2 = st.columns([1, 2])
    with col1:
        st.markdown("#### How confident do you feel about your annotation?")
    with col2:
        confidence = st.radio(
            "How confident do you feel about your annotation?",
            options=st.session_state.confidence_likert.keys(),
            horizontal=True,
            index=likert2index(f"conf_{annotation_id}"),
            label_visibility="hidden",
            key=f"cnf_{annotation_id}",
        )

    leftleft, left, middle, right, rightright = st.columns(5)
    if left.button(":arrow_backward: Back", use_container_width=True):
        if len(st.session_state.responses_done) == 0:
            st.session_state.page = st.session_state.page - 1
        else:
            previous_annotation_d = st.session_state.responses_done.pop()
            st.session_state.responses_todo.insert(0, previous_annotation_d)
        st.rerun()

    elif right.button("Next :arrow_forward:", use_container_width=True, type="primary"):

        if (
            correctness is not None
            and relevance is not None
            and safety is not None
            and confidence is not None
        ):  # Check if all questions are answered

            assign_states(
                annotation_id, correctness, relevance, safety, confidence
            )  # Save user input to session state
            st.session_state.responses_done.append(annotation_d)
            st.session_state.responses_todo.pop(0)

            if "end" not in st.session_state.times[annotation_id].keys():
                st.session_state.times[annotation_id]["end"] = time.time()
            elapsed_time = (
                st.session_state.times[annotation_id]["end"]
                - st.session_state.times[annotation_id]["start"]
            )

            update_status = annotations_collection.update_one(
                {"sentence_id": annotation_id},  # Find the document with _id = 1
                {
                    "$set": {
                        "rated": "Yes",
                        "correctness": correctness,
                        "relevance": relevance,
                        "safety": safety,
                        "time": elapsed_time,
                        "confidence": confidence,
                    }
                },
            )  # Update: change rated to yes

            # if annotation to do is more than 0
            if len(st.session_state.responses_todo) > 0:
                st.session_state.page = 3  # Repeat page
                st.rerun()
            # otherwise
            else:
                st.session_state.page = 4  # End page
                st.rerun()
        else:
            st.markdown(":orange[**Please answer all the questions.**]")


def followup_page4():
    st.markdown("#### Final question before you go...")

    st.markdown("#### Was it easy to follow the annotation instructions?")
    ease = st.radio(
        "Was it easy to follow the annotation instructions?",
        options=st.session_state.ease_likert.keys(),
        horizontal=True,
        index=None,
        label_visibility="hidden",
    )

    # mongodb_credentials = st.secrets.mongodb_credentials
    # uri = f"mongodb+srv://{mongodb_credentials}/?retryWrites=true&w=majority&appName=clinicalqa"
    uri = f"mongodb+srv://{open(os.path.join('..', 'mongodb_clinicalqa_uri.txt')).read().strip()}/?retryWrites=true&w=majority&appName=clinicalqa"
    client = MongoClient(uri)  # Create a new client and connect to the server
    db = client["feedback"]  # database

    leftleft, left, middle, right, rightright = st.columns(5)
    if left.button(":arrow_backward: Back", use_container_width=True):
        previous_annotation_d = st.session_state.responses_done.pop()
        st.session_state.responses_todo.insert(0, previous_annotation_d)
        st.session_state.page = st.session_state.page - 1
        st.rerun()

    elif right.button("Next :arrow_forward:", use_container_width=True, type="primary"):
        collection = db[f"annotator{st.session_state.annotator_n}"].insert_one(
            {
                "batch": [
                    (d["question_id"], d["sentence_id"])
                    for d in st.session_state.responses_done
                ],
                "datetime": datetime.now(),
                "ease": ease,
            }
        )
        st.session_state.page = 5
        st.rerun()


def batch_end_page5():
    st.title("Thank You!")
    st.markdown("#### You have completed the batch. Your responses have been saved.")


def fine_end_page6():
    st.title("Thank You!")
    st.markdown("#### You have completed all your fine annotations.")


# Display the appropriate page based on the session state
if st.session_state.page == 1:
    identifiers_page1()
if st.session_state.page == 2:
    instructions_page2()
elif st.session_state.page == 3:
    questions_page3()
elif st.session_state.page == 4:
    followup_page4()
elif st.session_state.page == 5:
    batch_end_page5()
elif st.session_state.page == 6:
    fine_end_page6()


if len(st.session_state.responses_done) > 0:
    current_progress = int(
        len(st.session_state.responses_done) / st.session_state.responses_left * 100
    )
    st.progress(current_progress)
    st.write(f"{current_progress}%")
else:
    st.progress(0)
    st.write(f"About to start annotations...")
