import argparse
from typing import List, Dict, Any

from lib.models import AskResult
from lib.embeddings import embed_text, load_embeddings, find_similar
from lib.storage import read_wiki_notes
from lib.llm import synthesize_answer

def ask(question: str, top_k: int = 5) -> AskResult:
    # Embed question
    question_vector = embed_text(question)
    
    # Retrieve top-K notes by cosine similarity
    all_embeddings = load_embeddings()
    if not all_embeddings:
        return AskResult(answer="I don't have notes about that", sources=[])
        
    similar_ids_scores = find_similar("query", question_vector, all_embeddings, threshold=0.0, top_k=top_k)
    
    if not similar_ids_scores:
        return AskResult(answer="I don't have notes about that", sources=[])
        
    # Get the actual notes
    all_notes = read_wiki_notes()
    notes_dict = {n.id: n for n in all_notes}
    
    retrieved_notes = []
    sources = []
    
    # Max context ~6000 tokens (truncate long notes)
    # The API rate limit is 6000 tokens per minute.
    # To be safe, we limit to 12000 characters (~3000 tokens)
    char_limit = 12000
    current_chars = 0
    
    for note_id, score in similar_ids_scores:
        if note_id in notes_dict:
            note = notes_dict[note_id]
            # Format note according to prompt expectation (including [note-id])
            note_content = f"[{note.id}]\n{note.summary}\n{note.body}"
            
            # Truncate if exceeds remaining chars
            if current_chars + len(note_content) > char_limit:
                remaining = char_limit - current_chars
                if remaining > 100:
                    note_content = note_content[:remaining] + "...[truncated]"
                else:
                    break
                    
            retrieved_notes.append(note_content)
            current_chars += len(note_content)
            
            sources.append({
                "id": note.id,
                "summary": note.summary,
                "score": score
            })
            
    if not retrieved_notes:
        return AskResult(answer="I don't have notes about that", sources=[])
        
    context_str = "\n\n".join(retrieved_notes)
    
    # Call synthesize_answer
    answer = synthesize_answer(context_str, question)
    
    return AskResult(answer=answer, sources=sources)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ask your brain a question")
    parser.add_argument("question", help="The question to ask")
    parser.add_argument("--top_k", type=int, default=5, help="Number of notes to retrieve")
    args = parser.parse_args()
    
    result = ask(args.question, args.top_k)
    print(f"\nQuestion: {args.question}")
    print(f"\nAnswer: {result.answer}")
    print("\nSources:")
    for source in result.sources:
        print(f" - [{source['id']}] {source['summary']} (score: {source['score']:.2f})")
