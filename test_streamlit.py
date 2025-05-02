import os
import json
import time
from datetime import datetime
import streamlit as st

with open(os.path.join('output', 'pilot', f"pilot1_fine.jsonl"), 'r', encoding='utf-8') as jsonl_file:
   data = [json.loads(line) for line in jsonl_file]

for d in data:
   st.markdown(d['answer'], unsafe_allow_html=True)
   st.markdown('\n')
   st.divider()
   
   
