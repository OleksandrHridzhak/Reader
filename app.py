import streamlit as st
import google.generativeai as genai
import json
import os
import random
import html
from typing import Dict, List, Optional

# Page configuration
st.set_page_config(
    page_title="Smart Book Shuffler",
    page_icon="📚",
    layout="wide"
)

# Custom CSS for serif font and styling
st.markdown("""
    <style>
    .reading-area {
        font-family: 'Georgia', 'Times New Roman', serif;
        font-size: 18px;
        line-height: 1.8;
        padding: 20px;
        text-align: justify;
    }
    .summary-box {
        background-color: #f0f0f0;
        padding: 15px;
        border-radius: 5px;
        margin-bottom: 20px;
        font-family: 'Georgia', 'Times New Roman', serif;
        font-style: italic;
    }
    .book-title {
        font-family: 'Georgia', 'Times New Roman', serif;
        font-size: 24px;
        font-weight: bold;
        margin-bottom: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# Constants
BOOKS_DATA_FILE = "books_data.json"
SEGMENT_WORD_COUNT = 5000

# Initialize session state
if 'books_data' not in st.session_state:
    st.session_state.books_data = {}
if 'api_key' not in st.session_state:
    st.session_state.api_key = None

def load_books_data() -> Dict:
    """Load books data from JSON file."""
    if os.path.exists(BOOKS_DATA_FILE):
        try:
            with open(BOOKS_DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            st.error(f"Error loading books data: {e}")
            return {}
    return {}

def save_books_data(data: Dict) -> None:
    """Save books data to JSON file."""
    try:
        with open(BOOKS_DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        st.error(f"Error saving books data: {e}")

def configure_gemini(api_key: str) -> bool:
    """Configure Gemini API."""
    try:
        genai.configure(api_key=api_key)
        return True
    except Exception as e:
        st.error(f"Error configuring Gemini: {e}")
        return False

def segment_book_with_gemini(book_title: str, book_content: str, api_key: str) -> List[str]:
    """
    Use Gemini to split book into logical segments of approximately 5000 words each.
    """
    configure_gemini(api_key)
    
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = f"""You are given a book titled "{book_title}". Please analyze the content and divide it into logical segments where each segment contains approximately {SEGMENT_WORD_COUNT} words.

Each segment should:
- End at a natural break point (chapter end, scene break, or paragraph boundary)
- Contain roughly {SEGMENT_WORD_COUNT} words (can vary by ±500 words for natural breaks)
- Be a complete narrative unit

Return ONLY a JSON array of strings, where each string is one segment of the book. Do not include any other text or explanation.

Book content:
{book_content}

Return format: ["segment1 text...", "segment2 text...", "segment3 text..."]
"""
        
        response = model.generate_content(prompt)
        
        # Parse the JSON response
        response_text = response.text.strip()
        # Remove markdown code blocks if present
        if response_text.startswith('```json'):
            response_text = response_text[7:]
        if response_text.startswith('```'):
            response_text = response_text[3:]
        if response_text.endswith('```'):
            response_text = response_text[:-3]
        response_text = response_text.strip()
        
        segments = json.loads(response_text)
        
        if not isinstance(segments, list) or len(segments) == 0:
            raise ValueError("Invalid response format from Gemini")
        
        return segments
    
    except Exception as e:
        st.error(f"Error segmenting book with Gemini: {e}")
        # Fallback: simple word-count based segmentation
        words = book_content.split()
        segments = []
        current_segment = []
        current_word_count = 0
        
        for word in words:
            current_segment.append(word)
            current_word_count += 1
            
            if current_word_count >= SEGMENT_WORD_COUNT:
                segments.append(' '.join(current_segment))
                current_segment = []
                current_word_count = 0
        
        # Add remaining words as last segment
        if current_segment:
            segments.append(' '.join(current_segment))
        
        return segments

def generate_summary_with_gemini(book_title: str, previous_segment: str, current_segment: str, api_key: str) -> str:
    """
    Use Gemini to generate a 2-line "Where we left off" summary.
    """
    configure_gemini(api_key)
    
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Take last 1000 words of previous segment for context
        prev_words = previous_segment.split()[-1000:]
        prev_context = ' '.join(prev_words)
        
        # Take first 500 words of current segment
        curr_words = current_segment.split()[:500]
        curr_context = ' '.join(curr_words)
        
        prompt = f"""You are reading a book titled "{book_title}". 

Based on where we left off and what comes next, write a 2-line summary (maximum 2 sentences) that reminds the reader what was happening.

Previous section ended with:
{prev_context}

Current section begins with:
{curr_context}

Write a concise 2-line summary starting with "Where we left off:" that bridges these sections.
"""
        
        response = model.generate_content(prompt)
        summary = response.text.strip()
        
        return summary
    
    except Exception as e:
        st.error(f"Error generating summary: {e}")
        return "Where we left off: Continuing from the previous segment..."

def process_uploaded_book(book_title: str, book_content: str, api_key: str) -> None:
    """
    Process an uploaded book: segment it and save to books_data.
    """
    with st.spinner(f"Processing '{book_title}'... This may take a moment."):
        segments = segment_book_with_gemini(book_title, book_content, api_key)
        
        books_data = load_books_data()
        books_data[book_title] = {
            'segments': segments,
            'current_index': 0,
            'total_segments': len(segments)
        }
        save_books_data(books_data)
        st.session_state.books_data = books_data
        
        st.success(f"✅ '{book_title}' processed! Created {len(segments)} segments.")

def get_random_unread_segment() -> Optional[tuple]:
    """
    Get a random book and its next unread segment.
    Returns: (book_title, segment_text, segment_index, is_first_segment, previous_segment)
    """
    books_data = load_books_data()
    
    if not books_data:
        return None
    
    # Filter books that have unread segments
    available_books = [
        (title, data) for title, data in books_data.items()
        if data['current_index'] < data['total_segments']
    ]
    
    if not available_books:
        return None
    
    # Pick a random book
    book_title, book_data = random.choice(available_books)
    current_index = book_data['current_index']
    segment_text = book_data['segments'][current_index]
    is_first_segment = (current_index == 0)
    previous_segment = book_data['segments'][current_index - 1] if current_index > 0 else None
    
    # Update current_index for next time
    books_data[book_title]['current_index'] = current_index + 1
    save_books_data(books_data)
    st.session_state.books_data = books_data
    
    return (book_title, segment_text, current_index, is_first_segment, previous_segment)

def calculate_progress(book_data: Dict) -> float:
    """Calculate reading progress percentage."""
    if book_data['total_segments'] == 0:
        return 0.0
    return (book_data['current_index'] / book_data['total_segments']) * 100

def reset_book_progress(book_title: str) -> None:
    """Reset reading progress for a specific book."""
    books_data = load_books_data()
    if book_title in books_data:
        books_data[book_title]['current_index'] = 0
        save_books_data(books_data)
        st.session_state.books_data = books_data

def delete_book(book_title: str) -> None:
    """Delete a book from the library."""
    books_data = load_books_data()
    if book_title in books_data:
        del books_data[book_title]
        save_books_data(books_data)
        st.session_state.books_data = books_data

# Main App
def main():
    st.title("📚 Smart Book Shuffler")
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Settings")
        
        # API Key input
        api_key = st.text_input(
            "Google Gemini API Key",
            type="password",
            value=st.session_state.api_key or "",
            help="Enter your Google Gemini API key"
        )
        
        if api_key:
            st.session_state.api_key = api_key
        
        st.divider()
        
        st.header("📤 Upload Books")
        st.write("Upload 3-4 .txt files")
        
        uploaded_files = st.file_uploader(
            "Choose text files",
            type=['txt'],
            accept_multiple_files=True,
            key="file_uploader"
        )
        
        if uploaded_files and api_key:
            for uploaded_file in uploaded_files:
                book_title = uploaded_file.name.replace('.txt', '')
                
                # Check if book already exists
                books_data = load_books_data()
                if book_title not in books_data:
                    if st.button(f"Process {book_title}", key=f"process_{book_title}"):
                        try:
                            book_content = uploaded_file.read().decode('utf-8', errors='replace')
                            process_uploaded_book(book_title, book_content, api_key)
                        except Exception as e:
                            st.error(f"Error reading {book_title}: {e}")
        
        elif uploaded_files and not api_key:
            st.warning("⚠️ Please enter your Gemini API key first!")
        
        st.divider()
        
        # Progress indicators
        st.header("📊 Reading Progress")
        books_data = load_books_data()
        
        if books_data:
            for title, data in books_data.items():
                progress = calculate_progress(data)
                st.write(f"**{title}**")
                st.progress(progress / 100)
                st.write(f"{progress:.0f}% complete ({data['current_index']}/{data['total_segments']} segments)")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("🔄", key=f"reset_{title}", help="Reset progress"):
                        reset_book_progress(title)
                        st.rerun()
                with col2:
                    if st.button("🗑️", key=f"delete_{title}", help="Delete book"):
                        delete_book(title)
                        st.rerun()
                
                st.divider()
        else:
            st.info("No books uploaded yet.")
    
    # Main content area
    books_data = load_books_data()
    
    if not books_data:
        st.info("👈 Upload some books to get started!")
    elif not api_key:
        st.warning("⚠️ Please enter your Gemini API key in the sidebar!")
    else:
        # Check if there are any unread segments
        available_books = [
            (title, data) for title, data in books_data.items()
            if data['current_index'] < data['total_segments']
        ]
        
        if not available_books:
            st.success("🎉 You've finished reading all your books!")
            st.balloons()
            if st.button("Reset All Progress"):
                for title in books_data.keys():
                    reset_book_progress(title)
                st.rerun()
        else:
            # Big "Give me something to read" button
            if st.button("📖 Give me something to read", type="primary", use_container_width=True):
                result = get_random_unread_segment()
                
                if result:
                    book_title, segment_text, segment_index, is_first_segment, previous_segment = result
                    
                    # Store in session state for display
                    st.session_state.current_display = {
                        'book_title': book_title,
                        'segment_text': segment_text,
                        'segment_index': segment_index,
                        'is_first_segment': is_first_segment,
                        'previous_segment': previous_segment
                    }
                    st.rerun()
            
            # Display the current segment if available
            if 'current_display' in st.session_state:
                display_data = st.session_state.current_display
                
                # Escape HTML to prevent XSS
                safe_book_title = html.escape(display_data['book_title'])
                st.markdown(f"<div class='book-title'>📖 {safe_book_title}</div>", unsafe_allow_html=True)
                st.write(f"*Segment {display_data['segment_index'] + 1} of {books_data[display_data['book_title']]['total_segments']}*")
                
                # Generate and display summary if not first segment
                if not display_data['is_first_segment'] and display_data['previous_segment']:
                    with st.spinner("Generating summary..."):
                        summary = generate_summary_with_gemini(
                            display_data['book_title'],
                            display_data['previous_segment'],
                            display_data['segment_text'],
                            api_key
                        )
                        # Escape HTML and preserve line breaks
                        safe_summary = html.escape(summary).replace('\n', '<br>')
                        st.markdown(f"<div class='summary-box'>{safe_summary}</div>", unsafe_allow_html=True)
                
                # Display the segment text with HTML escaping to prevent XSS, preserving formatting
                safe_segment_text = html.escape(display_data['segment_text']).replace('\n', '<br>')
                st.markdown(f"<div class='reading-area'>{safe_segment_text}</div>", unsafe_allow_html=True)
                
                # Show progress
                current_progress = calculate_progress(books_data[display_data['book_title']])
                st.progress(current_progress / 100)
                st.write(f"Progress: {current_progress:.0f}%")

if __name__ == "__main__":
    main()
