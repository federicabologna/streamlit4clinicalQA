import pandas as pd
import streamlit as st
import os
from pymongo.mongo_client import MongoClient

# Set page configuration
st.set_page_config(layout="wide", page_title="Clinical QA Annotation")

# Custom CSS for styling
js = '''
<script>
    var body = window.parent.document.querySelector(".main");
    console.log(body);
    body.scrollTop = 0;
</script>
'''

custom_css = """
<style>
    .my-container {
        background-color: #fffee9;
        padding: 15px;
        border-radius: 5px;
        border: 1px solid #c0c0c0;
    }
    .abstract-container {
        background-color: #ecfae8;
        padding: 15px;
        border-radius: 5px;
        border: 1px solid #c0c0c0;
    }
    .answered {
        background-color: #ecfae8 !important;
    }
    .unanswered {
        background-color: #fff1f1 !important;
    }
    .my-progress {
        background-color: #86a3c3 !important;
    }
</style>
"""

st.markdown(custom_css, unsafe_allow_html=True)

uri = "mongodb+srv://fb265:Y1lWAOSUn4YEETPf@clinicalqa.302z0.mongodb.net/?retryWrites=true&w=majority&appName=clinicalQA"
# Create a new client and connect to the server
client = MongoClient(uri)
db = client["annotations"]

# Initialize session state
if 'page' not in st.session_state:
    st.session_state.page = 1
if 'annotator_id' not in st.session_state:
    st.session_state.annotator_id = None
if 'progress' not in st.session_state:
    st.session_state.progress = 0

#Get question from mongo db
annotations_per_batch = 10
total_pairs = 300

def set_page(page):
    st.session_state.page = page

def get_batch_data(key_id, batch_id):
    start_index = (batch_id - 1) * annotations_per_batch
    end_index = start_index + annotations_per_batch
    return start_index, end_index

def save_responses(): 
    if st.session_state.responses:
        collection.insert_many(st.session_state.responses)
        st.session_state.responses = []

def consent_page1():
    st.title("Quality Survey of Answers to Clinical Questions")
    with open(os.path.join(os.getcwd(), 'consent.txt'), "r") as file:
            consent_instructions = file.read()
    st.markdown(consent_instructions)
            
    # Yes/No question
    answer = st.radio(
        "I have read the above information.",
        options=["I consent to participate", "I do not consent to participate"]
    )

    if st.button("Submit"):
        if answer == "I consent to participate":
            st.session_state.consent = answer
            st.session_state.page = 2
        elif answer == "I do not consent to participate":
            st.session_state.page = 6
        st.rerun()
    # st.button("Submit", on_click=set_page, args=[page])
        
def identifiers_page2():
    st.title("Quality Survey of Answers to Clinical Questions")
    st.write("Please enter your Annotator ID to start the survey.")

    annotator_id = st.text_input("Annotator ID:")

    if st.button("Submit"):
        if annotator_id:
            st.session_state.annotator_id = annotator_id
            st.session_state.page = 3
            st.rerun()
        else:
            st.write(":orange[Please enter all the required information.]")
    
def instructions_page3():
    st.title("Quality Survey of Answers to Clinical Questions")
    
    with open(os.path.join(os.getcwd(), 'instructions.txt'), "r") as file:
            survey_instructions = file.read()
    st.markdown(survey_instructions, unsafe_allow_html=True)
    
    if st.button("Next"):
        st.session_state.page = 4
        st.rerun()

def update_selection():
    
    st.session_state.correctness = None
    st.session_state.relevance = None
    st.session_state.safety = None
    st.session_state.progress += 1
    
def questions_page4():
    st.title("Quality Survey of Answers to Clinical Questions")
    
    # establish identifiers
    annotator_id = st.session_state.annotator_id

    # find annotators' annotations in mongodb
    db = client['annotations']  # Replace with your database name
    annotator_responses = db['annotator1']
    
    not_annotated = annotator_responses.find({ 
        "$and": [
            { "correctness": ""},
            { "relevance": ""},
            { "safety": ""}
        ]
    }) 
                                             
    batch_data = not_annotated[:10]
    index = st.session_state.progress
    qa_pair = batch_data[index]
    pair_id = qa_pair.get('_id')
    
    # create table with two columns
    col1, col2 = st.columns(2)

    with col1:
        st.header("Question")
        st.write(qa_pair.get('question'))
        
    with col2:
        st.header("Answer")
        st.write(qa_pair['answer'])

    # Survey questions
    st.write("### The information provided in the answer:")
    correctness = st.radio("#### :green[aligns with current medical knowledge (correctness).]", options=["Strongly Disagree",
                                                                                   "Disagree",
                                                                                   "Neutral",
                                                                                   "Agree",
                                                                                   "Strongly Agree"], index=None, key='correctness')
    relevance = st.radio("#### :blue[addresses the specific medical question (relevance).]", options=["Strongly Disagree",
                                                                                   "Disagree",
                                                                                   "Neutral",
                                                                                   "Agree",
                                                                                   "Strongly Agree"], index=None, key='relevance')
    safety = st.radio("#### :violet[communicates contraindications or risks (safety).]", options=["Strongly Disagree",
                                                                                   "Disagree",
                                                                                   "Neutral",
                                                                                   "Agree",
                                                                                   "Strongly Agree"], index=None, key='safety')
    
    # Add a submit button
    if st.button("Submit"):
        # Check if all questions are answered
        if correctness is not None and relevance is not None and safety is not None:
            # Save user input to session state
            st.write("Saving your responses...")
            
            # ADD RATING FIELD to document
            save_response = annotator_responses.update_one(
                {"_id": pair_id},  # Filter: Find the document with _id = 1
                {"$set": {"correctness": correctness,
                          "relevance": relevance,
                          "safety": safety}}  # Update: Add 'city' field with value 'New York'
            )
            
            if st.button("Next", on_click=update_selection):

                # if annotation done is less then total number per batch
                if st.session_state.progress < annotations_per_batch: 
                    st.session_state.page = 4 # Repeat page
                    st.rerun()
                # otherwise
                else:
                    st.session_state.page = 5  # End page
                    st.rerun()
        else:
            st.markdown(":orange[**Please answer all the questions.**]")
        
def end_page5():
    st.title("Thank You!")
    st.write("You have completed the batch. Your responses have been saved.")
    
def end_page6():
    st.title("Thank You!")

# Display the appropriate page based on the session state
if st.session_state.page == 1:
    consent_page1()
if st.session_state.page == 2:
    identifiers_page2()
if st.session_state.page == 3:
    instructions_page3()
elif st.session_state.page == 4:
    questions_page4()
elif st.session_state.page == 5:
    end_page5()
elif st.session_state.page == 6:
    end_page6()

# Display progress bar
current_progress = st.session_state.progress
total_progress = annotations_per_batch
st.progress(st.session_state.progress / total_progress)
if current_progress > 0:
    st.write(f"Progress: {current_progress}/{total_progress}")
else:
    st.write(f"About to start ...")