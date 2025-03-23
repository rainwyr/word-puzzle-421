# Word Puzzle Game - Product Specification

## Overview
A web-based game where users are presented with 4 images related to a single word. The goal is to guess the word that connects all images.

## Data Structure
- **Images**: Stored in S3 under `images/` with filenames that contain a UUID and image number (1-4)
- **Puzzles**: JSON files in `puzzles/` containing image descriptions and URLs without answers
- **Solutions**: Available in two formats:
  - By ID: Maps puzzle UUIDs to solutions
  - By Word: Organizes puzzles by their target word

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

### 4. Backend System
- Python functions to interact with S3 bucket
- Key functionalities:
  - Fetch random puzzle
  - Validate user answers
  - Provide hints (descriptions)
  - Track game statistics

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
7. Style the application for visual appeal
8. Deploy to Streamlit Cloud
9. Gather feedback and iterate 