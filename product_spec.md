# Word Puzzle Game - Product Specification

## Overview
A web-based game where users are presented with 4 images related to a single word. The goal is to guess the word that connects all images.

## Data Structure
- **Images**: Stored in S3 under `images/` with filenames that contain a UUID and image number (1-4)
- **Puzzles**: JSON files in `puzzles/` containing image descriptions and URLs without answers
- **Solutions**: Available in two formats:
  - By ID: Maps puzzle UUIDs to solutions
  - By Word: Organizes puzzles by their target word
- **Ratings**: JSON files in `ratings/` containing user ratings for difficulty and fun
  - Format: `{puzzle_id}.json` containing aggregated ratings
  - Each file stores the average ratings and count of ratings

## Core Features

### 1. Puzzle Selection & Gameplay
- Random puzzle selection from S3 bucket
- Display 4 images in a 2x2 grid
- Text input field for users to submit their guess
- Feedback on correct/incorrect answers
- Optional hints (show descriptions if user is stuck)

### 2. User Interface
- Clean, responsive design for all device sizes
- Game header with logo and navigation
- Main game area with images and input field
- Score/progress tracking
- Animation for correct answers

### 3. Game Mechanics
- Input validation for answers (case-insensitive)
- Score tracking (session-based)
- Timer option for challenge mode
- "Skip" button to move to next puzzle
- "Hint" button to reveal descriptions
- Mandatory user rating system for puzzles:
  - Difficulty rating (1-5 stars)
  - Fun rating (1-5 stars)
  - Ratings required after both puzzle completion and skipping
  - Users cannot proceed to the next puzzle without submitting ratings

### 4. Backend System
- Python functions to interact with S3 bucket
- Key functionalities:
  - Fetch random puzzle
  - Validate user answers
  - Provide hints (descriptions)
  - Track game statistics
  - Save and retrieve user ratings

### 5. Technical Implementation
- **Framework**: Streamlit for both frontend and backend
- **Language**: Python 3.8+
- **AWS Integration**: Boto3 for S3 access
- **Image Handling**: Pillow for image processing (if needed)
- **Hosting**: Streamlit Cloud, Python Anywhere, or Heroku
- **State Management**: Streamlit session state for game progress
- **Styling**: Custom CSS via st.markdown or Streamlit theming

### 6. Future Enhancements
- User accounts & persistent scores
- Daily challenges
- Difficulty levels
- Leaderboards
- Share functionality for social media
- Create-your-own puzzle feature

## Implementation Plan
1. Set up Python environment with Streamlit and Boto3
2. Create S3 integration functions for puzzle fetching
3. Build core Streamlit UI components
4. Implement game flow and answer validation
5. Add session-based scoring and progress tracking
6. Incorporate hints and feedback systems
7. Add user rating functionality for puzzles
8. Style the application for visual appeal
9. Deploy to Streamlit Cloud
10. Gather feedback and iterate

## User Rating System Specification

### Rating Collection
- After a user correctly solves or skips a puzzle, prompt them to rate:
  - Difficulty (1-5 stars)
  - Fun factor (1-5 stars)
- Ratings are mandatory; users must provide both ratings to proceed to the next puzzle
- Simple, intuitive star-based interface

### Rating Storage
- Ratings stored in S3 under `ratings/` directory
- Each puzzle has its own rating file: `{puzzle_id}.json`
- Rating file structure:
  ```json
  {
    "puzzle_id": "unique-puzzle-id",
    "target_word": "solution-word",
    "difficulty": {
      "average": 3.5,
      "count": 24
    },
    "fun": {
      "average": 4.2,
      "count": 24
    },
    "total_ratings": 24,
    "last_updated": "2023-03-24T12:34:56Z"
  }
  ```
  
### Enhanced Rating Analytics
- Detailed individual ratings stored in `ratings_log/` directory
- Logs organized in time-based batches: `ratings_log/YYYY-MM-DD-HH.json`
- Each log entry contains:
  ```json
  {
    "log_id": "uuid-for-this-entry",
    "puzzle_id": "puzzle-uuid",
    "target_word": "solution-word",
    "timestamp": "2023-03-24T12:34:56Z",
    "session_id": "anonymous-session-identifier",
    "ratings": {
      "difficulty": 4,
      "fun": 5
    },
    "metadata": {
      "time_to_solve": 45.2,
      "hints_used": true,
      "was_skipped": false,
      "platform": "mobile/desktop",
      "browser": "chrome/safari/etc"
    }
  }
  ```
- Batched writes to minimize S3 operations
- Provides data for future analytics:
  - Rating trends over time
  - Correlation between difficulty ratings and solve time
  - Comparison between ratings for solved vs. skipped puzzles
  - User engagement patterns
  - Puzzle popularity metrics by word

### Rating Display
- When a puzzle is loaded, show current average ratings if available
- After solving or skipping a puzzle, show the rating UI and require user input
- The system displays the target word in the rating UI to remind users what they're rating
- Users cannot proceed to the next puzzle without providing both difficulty and fun ratings
- Include aggregate statistics in the game UI
- Use a visual star representation for intuitive understanding 