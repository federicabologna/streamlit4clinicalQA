import os
import streamlit as st
from pymongo.mongo_client import MongoClient

# Set page configuration
st.set_page_config(layout="wide", page_title="Clinical QA Annotation")

# Custom CSS for styling
custom_css = """
<style>
    .my-container {
        background-color: #fffee9;
        padding: 15px;
        border-radius: 5px;
        border: 1px solid #c0c0c0;
    }
    .my-progress {
        background-color: #86a3c3 !important;
    }
</style>
"""

st.markdown(custom_css, unsafe_allow_html=True)


# Initialize session state
if 'page' not in st.session_state:
    st.session_state.page = 1
if 'annotator_id' not in st.session_state:
    st.session_state.annotator_id = None
if 'progress' not in st.session_state:
    st.session_state.progress = 0
if 'responses' not in st.session_state:
    st.session_state.responses = set()

#Get question from mongo db
annotations_per_batch = 10
total_pairs = 300


def consent_page1():
    
    st.title("Quality Survey of Answers to Clinical Questions")
    with open(os.path.join(os.getcwd(), 'data', 'consent.txt'), "r") as file:
            consent_instructions = file.read()
    st.markdown(consent_instructions)
            
    # Yes/No question
    answer = st.radio(
        "I have read the above information.",
        options=["I consent to participate", "I do not consent to participate"]
    )

    st.session_state.consent = answer
    
    left, middle, right = st.columns(3)

    if right.button("Next", use_container_width=True):
        if answer == "I consent to participate":
            st.session_state.page = 2
        elif answer == "I do not consent to participate":
            st.session_state.page = 5
        st.rerun()
        

def identifiers_page2():
    st.title("Quality Survey of Answers to Clinical Questions")
    st.write("Please enter your Annotator ID to start the survey.")

    annotator_id = st.text_input("Annotator ID:")

    left, middle, right = st.columns(3)

    if left.button("Back", use_container_width=True):
        st.session_state.page = st.session_state.page - 1
        st.rerun()

    elif right.button("Next", use_container_width=True):
        if annotator_id:
            st.session_state.annotator_id = annotator_id
            st.session_state.page = 3
            st.rerun()
        else:
            st.write(":orange[Please enter all the required information.]")
            

def instructions_page3():
    st.title("Quality Survey of Answers to Clinical Questions")
    
    with open(os.path.join(os.getcwd(), 'data', 'instructions.txt'), "r") as file:
            survey_instructions = file.read()
    st.markdown(survey_instructions, unsafe_allow_html=True)
    
    left, middle, right = st.columns(3)

    if left.button("Back", use_container_width=True):
        st.session_state.page = st.session_state.page - 1
        st.rerun()

    elif right.button("Next", use_container_width=True):
        st.session_state.page = 4
        st.rerun()


def update_selection(): #remove previously selected values
    
    st.session_state.correctness = None
    st.session_state.relevance = None
    st.session_state.safety = None 
    
    n_annotations = len(list(st.session_state.responses))
    st.session_state.progress = n_annotations


def questions_page4():
    st.title("Quality Survey of Answers to Clinical Questions")
    
    # establish identifiers
    annotator_id = st.session_state.annotator_id

    # Create a new client and connect to the server
    uri = "mongodb+srv://fb265:Y1lWAOSUn4YEETPf@clinicalqa.302z0.mongodb.net/?retryWrites=true&w=majority&appName=clinicalqa"
    client = MongoClient(uri)
    # find annotators' annotations in mongodb
    db = client['annotations']  # database
    
    annotation_type = st.session_state.annotation_type = 'coarse'
    
    annotations_collection = db[f'annotator{annotator_id}_{annotation_type}']
    not_annotated = annotations_collection.find({"rated": "No"}).limit(1)
    batch_data = [i for i in not_annotated]
    
    if len(batch_data) == 0:
        annotation_type = st.session_state.annotation_type = 'fine'
        annotations_collection = db[f'annotator{annotator_id}_{annotation_type}']
        not_annotated = annotations_collection.find({"rated": "No"}).limit(1)
        batch_data = [i for i in not_annotated]

    annotation_d = batch_data[0]
    
    st.header("Question")
    st.markdown(annotation_d['question'])
    
    st.header("Answer")
    st.markdown(annotation_d['answer'])
    
    if annotation_type == 'coarse':
        st.subheader("The information provided in the answer:")
    elif annotation_type == 'fine':
        st.subheader("The information provided in the sentence:")
        
    likert_options = ["Strongly Disagree","Disagree","Neutral","Agree","Strongly Agree"]
    
    col1, col2 = st.columns(2)
    col1.markdown('#### &emsp;&emsp;:green[aligns with current medical knowledge (correctness).]')
    with col2:
        correctness = st.radio(":green[aligns with current medical knowledge (correctness).]",
                            options=likert_options, horizontal=True, index=None, label_visibility='hidden',
                            key='correctness')
    
    col1, col2 = st.columns(2)
    col1.markdown('#### &emsp;&emsp;:blue[addresses the specific medical question (relevance).]')
    with col2:
        relevance = st.radio(":blue[addresses the specific medical question (relevance).]",
                    options=likert_options, horizontal=True, index=None, label_visibility='hidden',
                    key='relevance')
    col1, col2 = st.columns(2)
    col1.markdown(' \n#### &emsp;&emsp;:violet[communicates contraindications or risks (safety).]')
    with col2:
        safety = st.radio(":violet[communicates contraindications or risks (safety).]",
                        options=likert_options, horizontal=True, index=None, label_visibility='hidden',
                        key='safety')
        
    left, middle, right = st.columns(3)

    if left.button("Back", use_container_width=True):
        st.session_state.page = st.session_state.page - 1
        st.rerun()

    elif middle.button("Save", use_container_width=True, type="primary"):
    # Check if all questions are answered
        if correctness is not None and relevance is not None and safety is not None:
            # Save user input to session state
            
            st.session_state.responses.add(annotation_d['answer_id'])
            
            if annotation_type == 'coarse':
                update_status = annotations_collection.update_one({"answer_id": annotation_d['answer_id']},  # Find the document with _id = 1
                                                                {"$set": {"rated": "Yes",
                                                                          "correctness": correctness,
                                                                          "relevance": relevance,
                                                                          "safety": safety}})  # Update: change rated to yes
            elif annotation_type == 'fine':
                update_status = annotations_collection.update_one({"sentence_id": annotation_d['sentence_id']},  # Find the document with _id = 1
                                                                {"$set": {"rated": "Yes",
                                                                          "correctness": correctness,
                                                                          "relevance": relevance,
                                                                          "safety": safety}})
            
            st.markdown("#### Your responses has been saved!\n#### Double-check your answers, once you hit the Next button you will not be able to change your answers")

                
            if right.button("Next", on_click=update_selection, use_container_width=True):
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
    if st.session_state.consent == 'I consent to participate':
        st.write("You have completed the batch. Your responses have been saved.")

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


# Display progress bar
current_progress = st.session_state.progress
total_progress = annotations_per_batch
st.progress(st.session_state.progress / total_progress)
if current_progress > 0:
    st.write(f"Progress: {current_progress}/{total_progress} question-answer pairs")
else:
    st.write(f"About to start ...")