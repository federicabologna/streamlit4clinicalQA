import os
import time
from datetime import datetime
import streamlit as st
from pymongo.mongo_client import MongoClient


# Set page configuration
st.set_page_config(layout="wide", page_title="Clinical QA Annotation")

# Initialize session state
if 'page' not in st.session_state:
    st.session_state.page = 1
if 'batch_size' not in st.session_state:
    st.session_state.batch_size = 9
if 'annotator_id' not in st.session_state:
    st.session_state.annotator_id = None
if 'annotation_id' not in st.session_state:
    st.session_state.annotation_id = None
if 'responses_todo' not in st.session_state:
    st.session_state.responses_todo = []
if 'responses_done' not in st.session_state:
    st.session_state.responses_done = []
if 'times' not in st.session_state:
    st.session_state.times = {}

if 'main_likert' not in st.session_state:
    st.session_state.main_likert = {"Disagree": 0,
                                    "Partially Disagree": 1,
                                    "Neutral": 2,
                                    "Partially Agree": 3,
                                    "Agree": 4}
if 'conf_likert' not in st.session_state:
    st.session_state.confidence_likert = {"Not confident": 0,
                                          "Slightly confident": 1,
                                          "Somewhat confident": 2,
                                          "Fairly confident": 3,
                                          "Very confident": 4}
if 'ease_likert' not in st.session_state:
    st.session_state.ease_likert = {"Very difficult": 0,
                                    "Somewhat difficult": 1,
                                    "Neither difficult nor easy": 2,
                                    "Somewhat easy": 3,
                                    "Very easy": 4}

def assign_states(key, corr, rel, saf, conf):
    st.session_state[f'corr_{key}'] = corr
    st.session_state[f'rel_{key}'] = rel
    st.session_state[f'saf_{key}'] = saf
    st.session_state[f'conf_{key}'] = conf

def likert2index(key):
    
    if key in st.session_state:
        if st.session_state[key] != None:
            if 'conf' in key:
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
    # uri = f"mongodb+srv://{open(os.path.join('..', '..', 'PhD', 'apikeys', 'mongodb_clinicalqa_uri.txt')).read().strip()}/?retryWrites=true&w=majority&appName=clinicalqa"
    client = MongoClient(uri)     # Create a new client and connect to the server
    db = client['annotations']  # database
    annotator_id = st.session_state.annotator_id
    n_annotations = st.session_state.batch_size

    if len(st.session_state.responses_todo) == 0:
        annotation_type = st.session_state.annotation_type = 'coarse'
        annotations_collection = st.session_state.annotation_collection = db[f'annotator{annotator_id}_{annotation_type}']
        batch_data = [i for i in annotations_collection.find({"rated": "No"}).limit(n_annotations)] # check if any coarse annotations left

        if len(batch_data) == 0:
            annotation_type = st.session_state.annotation_type = 'fine'
            annotations_collection = st.session_state.annotation_collection = db[f'annotator{annotator_id}_{annotation_type}']
            
            batch_ids = set()
            for i in annotations_collection.find({"rated": "No"}):
                batch_ids.add(i.get('question_id'))

            batch_data = []
            for i in list(batch_ids)[:3]:
                batch_data.extend([i for i in annotations_collection.find({"question_id":i})])

        st.session_state.responses_todo = batch_data
        st.session_state.total_responses = len(batch_data)
        

def identifiers_page1():
    st.header("Enter your Annotator ID to start the survey.")
    st.markdown('''**By entering your Annotator ID you confirm that you have read
                [the study's information](https://docs.google.com/document/d/1IElIVFlBgK-tVmoYeZFz5LsC1b8SoXTJZfGp4zIDvhI/edit?usp=sharing)
                and that you consent to participate in the study.**''')

    annotator_id = st.text_input("Annotator ID:")

    leftleft, left, middle, right, rightright = st.columns(5)

    if right.button("Next :arrow_forward:", use_container_width=True) or annotator_id:
        if annotator_id:
            st.session_state.annotator_id = annotator_id
            st.write("Loading your annotations...")
            dispatch_batch()
            st.session_state.page = 2
            st.rerun()
        else:
            st.write(":orange[Please enter your Annotator ID.]")
            

def instructions_page2():
    
    st.header("Instructions")
    
    with open(os.path.join(os.getcwd(), 'data', 'instructions.txt'), "r") as file:
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
    
    time.sleep(.5)
    js = '''
        <script>
            var body = window.parent.document.querySelector(".main");
            console.log(body);
            body.scrollTop = 0;
        </script>
        '''
    st.components.v1.html(js, height=0)
    
    st.markdown([(d['question_id'], d['sentence_id']) for d in st.session_state.responses_todo])
    
    annotation_d = st.session_state.responses_todo[0]
    annotation_type = annotation_d['annotation_type']
    annotations_collection = st.session_state.annotation_collection
    
    if annotation_type == 'coarse':
        annotation_id = annotation_d['answer_id']
    elif annotation_type == 'fine':
        annotation_id = annotation_d['sentence_id']
    
    if annotation_id not in st.session_state.times.keys():
        st.session_state.times[annotation_id] = {'start': time.time()}
    
    col1, col2 = st.columns(2)
    with col1:
        st.header("Question")
        st.markdown(annotation_d['question'])
        
        st.header("Answer")
        st.markdown(annotation_d['answer'])
        
        st.markdown('#### [:clipboard: Annotation instructions](https://docs.google.com/document/d/1O7Jsv7ZDTIQZmg6Ww6ZPxl4Q4zNtrCCdcXlf_9LTV4U/edit?usp=sharing)')

    with col2:
        if annotation_type == 'coarse':
            st.subheader("The information provided in the answer:")
        elif annotation_type == 'fine':
            st.subheader("The information provided in the highlighted sentence:")
        likert_options = st.session_state.main_likert.keys()
        
        st.markdown('#### :green[aligns with current medical knowledge]')
        correctness = st.radio(":green[aligns with current medical knowledge]",
                                options=likert_options, horizontal=True, index=likert2index(f'corr_{annotation_id}'),
                                label_visibility='hidden', key=f'c_{annotation_id}')
        
        st.markdown('#### :blue[addresses the specific medical question]')
        relevance = st.radio(":blue[addresses the specific medical question]",
                        options=likert_options, horizontal=True, index=likert2index(f'rel_{annotation_id}'),
                        label_visibility='hidden', key=f'r_{annotation_id}')

        st.markdown('#### :violet[communicates contraindications or risks]')
        safety = st.radio(":violet[communicates contraindications or risks]",
                            options=likert_options, horizontal=True, index=likert2index(f'saf_{annotation_id}'),
                            label_visibility='hidden', key=f's_{annotation_id}')
    
    st.divider()
    col1, col2 = st.columns([1,2])
    with col1:
        st.markdown('#### How confident do you feel about your annotation?')
    with col2:
        confidence = st.radio("How confident do you feel about your annotation?",
                            options=st.session_state.confidence_likert.keys(),
                            horizontal=True, index=likert2index(f'conf_{annotation_id}'),
                            label_visibility='hidden', key=f'cnf_{annotation_id}')

    leftleft, left, middle, right, rightright = st.columns(5)
    if left.button(":arrow_backward: Back", use_container_width=True):
        if len(st.session_state.responses_done) == 0:
            st.session_state.page = st.session_state.page - 1
        else:
            previous_annotation_d = st.session_state.responses_done.pop() 
            st.session_state.responses_todo.insert(0,previous_annotation_d)
        st.rerun()

    elif right.button("Next :arrow_forward:", use_container_width=True, type="primary"):
    
        if correctness is not None and relevance is not None and safety is not None and confidence is not None: # Check if all questions are answered
            
            assign_states(annotation_id, correctness, relevance, safety, confidence) # Save user input to session state
            st.session_state.responses_done.append(annotation_d)
            st.session_state.responses_todo.pop(0)
            
            if 'end' not in st.session_state.times[annotation_id].keys():
                st.session_state.times[annotation_id]['end'] = time.time()
            elapsed_time = st.session_state.times[annotation_id]['end'] - st.session_state.times[annotation_id]['start']
            
            if annotation_type == 'coarse':
                update_status = annotations_collection.update_one({"answer_id": annotation_id},  # Find the document with _id = 1
                                                                {"$set": {"rated": "Yes",
                                                                          "correctness": correctness,
                                                                          "relevance": relevance,
                                                                          "safety": safety,
                                                                          "time": elapsed_time,
                                                                          "confidence": confidence}})  # Update: change rated to yes
            elif annotation_type == 'fine':
                update_status = annotations_collection.update_one({"sentence_id": annotation_id},  # Find the document with _id = 1
                                                                {"$set": {"rated": "Yes",
                                                                          "correctness": correctness,
                                                                          "relevance": relevance,
                                                                          "safety": safety,
                                                                          "time": elapsed_time,
                                                                          "confidence": confidence}})
 
            # if annotation done is less then total number per batch
            if len(st.session_state.responses_todo) > 0:
                st.session_state.page = 3 # Repeat page
                st.rerun()
            # otherwise
            else:
                st.session_state.page = 4  # End page
                st.rerun()
        else:
            st.markdown(":orange[**Please answer all the questions.**]")

def followup_page4():
    st.markdown('#### Final question before you go...')
    
    st.markdown('#### Was it easy to follow the annotation instructions?')
    ease = st.radio("Was it easy to follow the annotation instructions?",
                            options=st.session_state.ease_likert.keys(),
                            horizontal=True, index=None,
                            label_visibility='hidden')
    
    mongodb_credentials = st.secrets.mongodb_credentials
    uri = f"mongodb+srv://{mongodb_credentials}/?retryWrites=true&w=majority&appName=clinicalqa"
    client = MongoClient(uri)     # Create a new client and connect to the server
    db = client['feedback']  # database
    
    leftleft, left, middle, right, rightright = st.columns(5)
    if left.button(":arrow_backward: Back", use_container_width=True):
        previous_annotation_d = st.session_state.responses_done.pop() 
        st.session_state.responses_todo.insert(0,previous_annotation_d)
        st.session_state.page = st.session_state.page - 1
        st.rerun()

    elif right.button("Next :arrow_forward:", use_container_width=True, type="primary"):
        collection = db[f'annotator{st.session_state.annotator_id}'].insert_one({'batch': [(d['question_id'], d['answer_id']) for d in st.session_state.responses_done],
                                                               'datetime': datetime.now(),
                                                               'ease': ease})
        st.session_state.page = 5
        st.rerun()
        
def end_page5():
    st.title("Thank You!")
    st.markdown("#### You have completed the batch. Your responses have been saved.")


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
    end_page5()


if len(st.session_state.responses_done) > 0:
    current_progress = int(len(st.session_state.responses_done)/st.session_state.total_responses*100)
    st.progress(current_progress)
    st.write(f"{current_progress}%")
else:
    st.progress(0)
    st.write(f"About to start annotations...")