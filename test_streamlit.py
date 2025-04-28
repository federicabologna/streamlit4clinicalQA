import os
import json
import time
from datetime import datetime
import streamlit as st

with open(os.path.join('data', f"wrong_ones.json"), 'r', encoding='utf-8') as json_file:
   data = json.load(json_file)

for key, value in data.items():
   for tup in value:
      st.markdown(tup[1])
      st.markdown('\n')
      st.divider()
   
   
