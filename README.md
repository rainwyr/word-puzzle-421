# Quadrality

A Streamlit web application that presents users with 4 images related to a single word. The goal is to guess the word that connects all the images.

## Features

- Random puzzle selection from AWS S3 bucket
- 2x2 image grid display
- Hints system with image descriptions
- Score tracking based on time and hint usage
- Feedback for correct/incorrect answers
- Skip functionality for difficult puzzles
- Rating system for puzzles:
  - Mandatory ratings for both difficulty and fun
  - Rating submission required after each puzzle (solved or skipped)
  - Aggregate rating display for each puzzle

## Setup Instructions

### Prerequisites

- Python 3.8 or higher
- AWS account with access to the S3 bucket containing puzzle data
- AWS Access Key and Secret Key with permission to read from the bucket

### Installation

1. Clone this repository:
   ```
   git clone <repository-url>
   cd word-puzzle-421
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Set up your environment variables by creating a `.env` file:
   ```
   # Copy the example file
   cp .env.example .env
   
   # Edit the file with your actual credentials
   nano .env
   ```

4. Fill in your AWS credentials and bucket name in the `.env` file:
   ```
   AWS_ACCESS_KEY_ID=your_access_key_here
   AWS_SECRET_ACCESS_KEY=your_secret_key_here
   AWS_DEFAULT_REGION=us-east-1
   S3_BUCKET_NAME=word-puzzle-421
   ```

### Running the Application

1. Start the Streamlit app:
   ```
   streamlit run app.py
   ```

2. Open your browser and navigate to:
   ```
   http://localhost:8501
   ```

## Project Structure

- `app.py`: Main Streamlit application
- `s3_utils.py`: AWS S3 interaction functions
- `game_logic.py`: Game mechanics and state management
- `requirements.txt`: Project dependencies
- `.env.example`: Example environment variables

## Game Data Structure

The S3 bucket should contain:

- `images/`: Directory with puzzle images (4 per puzzle)
- `puzzles/`: JSON files with puzzle descriptions and image URLs
- `solutions_by_id/`: Solutions organized by puzzle ID
- `solutions_by_word/`: Solutions organized by target word
- `ratings/`: Aggregated user ratings for each puzzle
- `ratings_log/`: Detailed individual rating logs organized by time

## How to Play

1. Four images will be displayed, all related to a single word.
2. Think about what word connects all four images.
3. Enter your guess in the text input field.
4. Use "Show Hints" if you need help (this will display descriptions of the images).
5. Use "Skip Puzzle" if you want to move to a different puzzle.
6. After solving or skipping a puzzle, you must rate its difficulty (1-5 stars) and how fun it was (1-5 stars).
7. Your score is based on solving time and whether hints were used.

## Deployment

For production deployment:

1. Create a Streamlit account at [streamlit.io](https://streamlit.io/)
2. Connect your GitHub repository
3. Deploy the application
4. Set up the environment variables in the Streamlit dashboard

## License

[Insert your preferred license here]

## Acknowledgements

- Images and puzzles from [Your Source]
- Built with Streamlit 