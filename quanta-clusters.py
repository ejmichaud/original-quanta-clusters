"""
This script loads the clusters and corresponding contexts from the data folder and
displays them in a Streamlit app. 
"""

from collections import defaultdict
import json
import os
import numpy as np
import streamlit as st
from streamlit_shortcuts import add_keyboard_shortcuts

def tokens_to_html(tokens, max_len=150):
    """Given a list of tokens (strings), returns HTML for displaying the tokenized text."""
    newline_tokens = ['\n', '\r', '\r\n', '\v', '\f']
    html = ""
    txt = ""
    if len(tokens) > max_len:
        html += '<span>...</span>'
    tokens = tokens[-max_len:]
    for i, token in enumerate(tokens):
        background_color = "white" if i != len(tokens) - 1 else "#FF9999"
        txt += token
        if all([c in newline_tokens for c in token]):
            # replace all instances with ⏎
            token_rep = len(token) * "⏎"
            brs = "<br>" * len(token)
            html += (
                f'<span style="border: 1px solid #DDD; '
                f'background-color: {background_color}; white-space: pre-wrap;">'
                f'{token_rep}</span>{brs}'
            )
        else:
            # Escape problematic characters
            token = token.replace("$", "\$")
            token = token.replace("&", "&amp;")
            token = token.replace("_", "\_")
            token = token.replace("*", "\*")
            token = token.replace("`", "\`")
            html += (
                f'<span style="border: 1px solid #DDD; '
                f'background-color: {background_color}; white-space: pre-wrap;">'
                f'{token}</span>'
            )
    if "</" in txt:
        return "CONTEXT NOT LOADED FOR SECURITY REASONS SINCE IT CONTAINS HTML CODE (could contain javascript)."
    else:
        return html


# Create sidebar for selecting clusters file and cluster
st.sidebar.header('LLM skill clusters')

# Add paper reference and description
st.sidebar.markdown("""
This visualization accompanies the paper 
[The Quantization Model of Neural Scaling](https://arxiv.org/abs/2303.13506).

This interface allows you to explore clusters of skill "quanta" for pythia-70m. The most interesting clusters, for n_clusters=400, are at index 50 and 100 (a coincidence that these ended up being such whole numbers).
""")

# Load the ERIC clusters file
cluster_file = "ERIC-QUANTA-CLUSTERS-GRADIENTS.json"
with open(cluster_file) as f:
    clusters = json.load(f)

cluster_sizes = sorted(list(clusters.keys()), key=int)
default_n_clusters = '400' if '400' in cluster_sizes else cluster_sizes[0]
n_clusters = st.sidebar.selectbox('Select number of clusters', cluster_sizes, index=cluster_sizes.index(default_n_clusters))
n_clusters = str(n_clusters)

# clusters_data is a tuple: (labels_list, other_info)
labels_list, _ = clusters[n_clusters]

# Create a mapping from each actual cluster ID to the list of example indices that have that ID
cluster_to_tokens = defaultdict(list)
for i, cluster_id in enumerate(labels_list):
    cluster_to_tokens[cluster_id].append(i)

# Sort cluster IDs by the size of their token list (largest first) and assign a rank
new_index_old_index = {
    i: cluster_id
    for i, cluster_id in enumerate(
        sorted(cluster_to_tokens, key=lambda k: len(cluster_to_tokens[k]), reverse=True)
    )
}

# Use a single session state key for the cluster index.
# The key name depends on n_clusters so that switching n_clusters resets the index.
session_key = f"cluster_idx_{n_clusters}"
if session_key not in st.session_state:
    st.session_state[session_key] = int(n_clusters) // 8

# Bind the selectbox directly to the session state key.
cluster_idx = st.sidebar.selectbox(
    'Select cluster index',
    options=list(range(int(n_clusters))),
    index=st.session_state[session_key],
    key=session_key
)

# Define arrow-key callbacks that update the same session state value.
def prev_cluster():
    if st.session_state[session_key] > 0:
        st.session_state[session_key] -= 1

def next_cluster():
    if st.session_state[session_key] < int(n_clusters) - 1:
        st.session_state[session_key] += 1

if st.sidebar.button('Previous cluster', on_click=prev_cluster):
    pass
if st.sidebar.button('Next cluster', on_click=next_cluster):
    pass

# Add keyboard shortcuts
add_keyboard_shortcuts({
    "ArrowLeft": "Previous cluster",
    "ArrowRight": "Next cluster"
})
st.sidebar.write("You can use the left and right arrow keys to move quickly between clusters.")

# Load contexts file
context_filename = "ERIC-QUANTA-CONTEXTS.json"
with open(context_filename) as f:
    samples = json.load(f)

idx_to_token_idx = list(samples.keys())

# Use the current session state's cluster index when displaying the cluster.
current_idx = st.session_state[session_key]
current_cluster_id = new_index_old_index[current_idx]
st.write(f"## Cluster {current_idx}")

for i in cluster_to_tokens[current_cluster_id]:
    sample = samples[idx_to_token_idx[i]]
    context = sample['context']
    y = sample['answer']
    tokens = context + [y]
    html = tokens_to_html(tokens)
    st.write("-----------------------------------------------------------")
    st.write(html, unsafe_allow_html=True)
