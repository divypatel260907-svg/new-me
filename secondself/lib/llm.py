import os
import json
import time
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

def get_client():
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        try:
            import streamlit as st
            api_key = st.secrets.get("GROQ_API_KEY")
        except (ImportError, FileNotFoundError, Exception):
            pass
            
    if not api_key:
        raise ValueError("GROQ_API_KEY is not configured in environment, .env file, or Streamlit secrets.")
    return Groq(api_key=api_key)

def call_llm(prompt: str, system: str = "", retries: int = 3, response_format: dict = None, temperature: float = 0.1) -> str:
    """Wrapper around Groq API with retries and exponential backoff."""
    client = get_client()
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    model = "llama-3.1-8b-instant"
    
    last_error = None
    for attempt in range(retries):
        try:
            kwargs = {
                "messages": messages,
                "model": model,
                "temperature": temperature
            }
            if response_format:
                kwargs["response_format"] = response_format
                
            chat_completion = client.chat.completions.create(**kwargs)
            return chat_completion.choices[0].message.content
        except Exception as e:
            last_error = e
            time.sleep(2 ** attempt)
            
    raise RuntimeError(f"Failed to communicate with LLM after {retries} retries. Last error: {last_error}")

def classify_content(text: str) -> dict:
    """Returns {para, tags, summary} JSON."""
    system_prompt = (
        "You are an AI Librarian for a personal knowledge management system.\n"
        "Analyze the provided text and classify it into one of the PARA categories:\n"
        "- Projects: Short-term efforts with a specific goal and deadline.\n"
        "- Areas: Long-term responsibilities that require ongoing attention.\n"
        "- Resources: Topics of ongoing interest or reference materials.\n"
        "- Archives: Inactive items from other categories or low-utility content.\n\n"
        "Return a valid JSON object with the following fields:\n"
        "- \"para\": The PARA category string (exactly: Projects, Areas, Resources, or Archives)\n"
        "- \"tags\": A list of 1 to 5 relevant lowercase tags (strings)\n"
        "- \"summary\": A one-line summary of the content (string)"
    )
    
    # Simple truncation to stay safe within context window limits
    max_char_len = 12000
    if len(text) > max_char_len:
        text = text[:max_char_len] + "\n\n[Content truncated for classification]"
        
    result_str = call_llm(text, system=system_prompt, response_format={"type": "json_object"})
    return json.loads(result_str)

def synthesize_answer(context: str, question: str) -> str:
    """RAG Answer generation using retrieved notes context."""
    system_prompt = (
        "You are SecondSelf, answering from the user's personal knowledge base.\n"
        "Use ONLY the provided notes to answer. If the answer is not in the notes, say 'I don't have notes about that'.\n"
        "Cite sources using [note-id] notation."
    )
    prompt = f"Notes:\n{context}\n\nQuestion: {question}"
    return call_llm(prompt, system=system_prompt, temperature=0.3)
