import streamlit as st
import json
import os
import streamlit.components.v1 as components
from ask import ask
from lib.embeddings import load_embeddings
from lib.storage import load_index, RAW_DIR, WIKI_DIR
import subprocess
from capture import capture_note, capture_link

st.set_page_config(page_title="SecondSelf", page_icon="🧠", layout="wide")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

@st.cache_resource
def get_embeddings_cached():
    return load_embeddings()

@st.cache_data
def get_graph_html():
    graph_path = os.path.join(BASE_DIR, "data", "graph.json")
    if not os.path.exists(graph_path):
        return "<p style='font-family:sans-serif; padding: 20px;'>No graph data found. Run pipeline.py process to build it.</p>"
    with open(graph_path, "r", encoding="utf-8") as f:
        graph_data = f.read()

    html = f"""
<!DOCTYPE html>
<html>
<head>
    <script type="text/javascript" src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
    <style type="text/css">
        body {{ margin: 0; padding: 0; font-family: sans-serif; background-color: #fafafa; }}
        #mynetwork {{ width: 100%; height: 100vh; border: none; }}
    </style>
</head>
<body>
<div id="mynetwork"></div>
<script type="text/javascript">
    const container = document.getElementById('mynetwork');
    const options = {{
        groups: {{
            Projects: {{ color: {{ background: '#FFDDC1', border: '#FFC8A2' }} }},
            Areas: {{ color: {{ background: '#D4F0F0', border: '#8FCACA' }} }},
            Resources: {{ color: {{ background: '#CCE2CB', border: '#B6CFB6' }} }},
            Archives: {{ color: {{ background: '#E0E0E0', border: '#BDBDBD' }} }}
        }},
        physics: {{ barnesHut: {{ gravitationalConstant: -8000, springLength: 150 }}, stabilization: {{ iterations: 200 }} }},
        interaction: {{ dragNodes: true, dragView: true, zoomView: true, hover: true }},
        nodes: {{ shape: 'dot', size: 15, font: {{ size: 14, color: '#333' }}, borderWidth: 2 }},
        edges: {{ width: 1, color: '#999', smooth: {{ type: 'continuous' }} }}
    }};

    const data = {graph_data};
    
    const nodes = data.nodes.map(n => ({{
        id: n.id,
        label: n.summary.length > 25 ? n.summary.substring(0, 25) + '...' : n.summary,
        group: n.group,
        title: `<div style="max-width:300px; white-space:pre-wrap; font-family:sans-serif; padding:5px;"><strong>${{n.summary}}</strong><br><br><span style="color:#555;">${{n.content_preview}}</span></div>`
    }}));
    
    const edges = data.edges.map(e => ({{
        from: e.source,
        to: e.target
    }}));

    const graphData = {{
        nodes: new vis.DataSet(nodes),
        edges: new vis.DataSet(edges)
    }};

    const network = new vis.Network(container, graphData, options);
</script>
</body>
</html>
"""
    return html

# Ensure embeddings are loaded in background
get_embeddings_cached()

# Header layout
col1, col2 = st.columns([4, 1])
with col1:
    st.title("🧠 SecondSelf")
with col2:
    st.write("")
    if st.button("Refresh Graph"):
        st.cache_data.clear()
        st.rerun()

# Ask Your Brain section
st.subheader("Ask your brain")
with st.form("ask_form"):
    col_q, col_btn = st.columns([5, 1])
    with col_q:
        question = st.text_input("Question", label_visibility="collapsed", placeholder="Ask something...")
    with col_btn:
        submitted = st.form_submit_button("Ask")

if submitted and question:
    with st.spinner("Thinking..."):
        try:
            result = ask(question)
            st.markdown(f"**Answer:** {result.answer}")
            if result.sources:
                with st.expander("Sources"):
                    for src in result.sources:
                        st.write(f"- **{src['id']}**: {src['summary']} *(Score: {src['score']:.2f})*")
        except Exception as e:
            st.error(f"Error querying: {e}")

st.markdown("---")

# Graph section
st.subheader("Interactive Knowledge Graph")
components.html(get_graph_html(), height=600)

# Sidebar
with st.sidebar:
    st.header("Dashboard")
    
    # Stats
    st.subheader("Stats")
    index = load_index()
    raw_processed = len(index.get("raw_processed", {}))
    
    raw_count = 0
    if os.path.exists(RAW_DIR):
        raw_count = len([d for d in os.listdir(RAW_DIR) if os.path.isdir(os.path.join(RAW_DIR, d))])
        
    wiki_count = 0
    if os.path.exists(WIKI_DIR):
        for root, _, files in os.walk(WIKI_DIR):
            wiki_count += sum(1 for f in files if f.endswith(".md"))
            
    last_build = index.get('last_graph_build', 'Never')
    if last_build != 'Never':
        try:
            from datetime import datetime
            # Parse ISO and format it nicely
            dt = datetime.fromisoformat(last_build.replace('Z', '+00:00'))
            last_build = dt.strftime("%b %d, %Y at %I:%M %p")
        except:
            pass
            
    st.write(f"**Raw Captures:** {raw_count} ({raw_count - raw_processed} pending)")
    st.write(f"**Wiki Notes:** {wiki_count}")
    st.write(f"**Last Graph Build:** {last_build}")

    
    st.markdown("---")
    st.subheader("Actions")
    if st.button("Process Pipeline"):
        with st.spinner("Running pipeline (classify + link)..."):
            try:
                subprocess.run(["python", "pipeline.py", "process"], check=True, cwd=BASE_DIR)
                st.cache_data.clear()
                st.success("Pipeline complete!")
                st.rerun()
            except Exception as e:
                st.error(f"Pipeline failed: {e}")

    st.markdown("---")
    st.subheader("Capture Knowledge")
    
    capture_type = st.radio("Capture Type", ["Note", "URL"], horizontal=True)
    
    if capture_type == "Note":
        with st.form("capture_note_form"):
            note_content = st.text_area("Note Content", placeholder="Write your thought here...")
            submitted_note = st.form_submit_button("Capture Note")
            if submitted_note and note_content:
                try:
                    capture_note(note_content)
                    st.success("Note captured! Remember to process the pipeline.")
                except Exception as e:
                    st.error(f"Failed to capture note: {e}")
    else:
        with st.form("capture_url_form"):
            url_content = st.text_input("URL", placeholder="https://...")
            url_notes = st.text_input("Optional Notes", placeholder="Why is this relevant?")
            submitted_url = st.form_submit_button("Capture URL")
            if submitted_url and url_content:
                try:
                    capture_link(url_content, url_notes)
                    st.success("URL captured! Remember to process the pipeline.")
                except Exception as e:
                    st.error(f"Failed to capture URL: {e}")
