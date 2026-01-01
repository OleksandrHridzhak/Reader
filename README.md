# 📚 Smart Book Shuffler

A Streamlit-based application that helps you read multiple books simultaneously by randomly selecting segments from your library. Powered by Google's Gemini 1.5 Flash AI for intelligent text segmentation and contextual summaries.

## Features

- **Upload Multiple Books**: Support for 3-4 .txt files
- **AI-Powered Segmentation**: Uses Google Gemini to split books into logical ~5000-word segments
- **Smart Randomization**: "Give me something to read" button picks a random unread segment
- **Context Summaries**: AI-generated "Where we left off" summaries for continuing segments
- **Progress Tracking**: Visual progress indicators for each book
- **Serif Font Reading**: Comfortable reading experience with Georgia serif font
- **Persistent Storage**: Books and progress saved in local JSON file

## Prerequisites

- Python 3.8+
- Google Gemini API key ([Get one here](https://makersuite.google.com/app/apikey))

## Installation

1. Clone this repository:
```bash
git clone https://github.com/OleksandrHridzhak/Reader.git
cd Reader
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
streamlit run app.py
```

4. Open your browser to `http://localhost:8501`

## Usage

1. **Enter API Key**: In the sidebar, enter your Google Gemini API key
2. **Upload Books**: Upload 3-4 .txt files using the file uploader
3. **Process Books**: Click the "Process [book name]" button for each uploaded book
4. **Start Reading**: Click the big "📖 Give me something to read" button
5. **Continue Reading**: Keep clicking the button to get random segments from your books

## How It Works

### Segmentation
When you upload a book, the application sends it to Google Gemini with instructions to split it into logical segments of approximately 5000 words each. The AI considers natural break points like chapter endings, scene transitions, or paragraph boundaries.

### Randomization
When you click "Give me something to read", the app:
1. Filters books that have unread segments
2. Randomly selects one book
3. Retrieves the next unread segment for that book
4. Updates the reading progress

### Context Summaries
For segments that aren't the first in a book, the app uses Gemini to generate a brief 2-line summary that reminds you what was happening in the story. This helps maintain continuity when jumping between books.

### Data Storage
All book data, segments, and reading progress are stored in `books_data.json` in the application directory. This file is automatically created and updated as you use the app.

## Project Structure

```
Reader/
├── app.py              # Main application file
├── requirements.txt    # Python dependencies
├── .gitignore         # Git ignore rules
├── README.md          # This file
└── books_data.json    # Generated: Book storage (not committed)
```

## Features in Detail

### Sidebar
- **Settings**: Google Gemini API key input
- **Upload Books**: Drag-and-drop or browse for .txt files
- **Reading Progress**: 
  - Progress bars for each book
  - Reset button (🔄) to restart a book
  - Delete button (🗑️) to remove a book

### Main Area
- **Welcome Screen**: Instructions when no books are uploaded
- **Reading Button**: Large, prominent button to get next segment
- **Book Display**: 
  - Book title and segment number
  - "Where we left off" summary (for non-first segments)
  - Segment text in serif font
  - Progress indicator

## Customization

You can customize the segment size by modifying the `SEGMENT_WORD_COUNT` constant in `app.py`:

```python
SEGMENT_WORD_COUNT = 5000  # Change this value
```

## Limitations

- Requires active internet connection for Gemini API calls
- API usage is subject to Google's rate limits and quotas
- Best suited for narrative text files (novels, stories)
- Maximum file size limited by Streamlit (200MB per file)

## Troubleshooting

**Books not processing?**
- Verify your API key is correct
- Check your internet connection
- Ensure the .txt file is properly formatted

**Segments seem odd?**
- The AI does its best to find natural breaks, but may not always be perfect
- Consider the fallback: if Gemini fails, the app uses word-count based segmentation

**Progress not saving?**
- Ensure the application has write permissions in its directory
- Check if `books_data.json` is being created

## License

This project is open source and available under the MIT License.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Acknowledgments

- Built with [Streamlit](https://streamlit.io/)
- Powered by [Google Gemini](https://deepmind.google/technologies/gemini/)
