import streamlit as st
import time
import game_logic
import s3_utils
from typing import Dict, Any

# Set page configuration
st.set_page_config(
    page_title="Word Puzzle Game",
    page_icon="🧩",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Custom CSS for styling
def load_css():
    st.markdown("""
    <style>
        /* Game title */
        .title {
            font-size: 2.5rem;
            color: #3366cc;
            text-align: center;
            margin-bottom: 1rem;
        }
        
        /* Images grid */
        .image-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            grid-gap: 10px;
            margin-bottom: 20px;
        }
        
        .image-container {
            border: 2px solid #e6e6e6;
            border-radius: 10px;
            padding: 5px;
            text-align: center;
        }
        
        .image-container img {
            max-width: 100%;
            height: auto;
            border-radius: 5px;
        }
        
        /* Input area */
        .input-area {
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 20px;
        }
        
        /* Correct answer animation */
        @keyframes correct-answer {
            0% { background-color: #ffffff; }
            50% { background-color: #90ee90; }
            100% { background-color: #ffffff; }
        }
        
        .correct-answer {
            animation: correct-answer 2s ease;
        }
        
        /* Score display */
        .score-display {
            display: flex;
            justify-content: space-between;
            background-color: #e6f3ff;
            padding: 10px 15px;
            border-radius: 10px;
            margin-bottom: 15px;
        }
        
        .score-item {
            text-align: center;
        }
        
        /* Buttons */
        .stButton button {
            width: 100%;
            border-radius: 5px;
            margin-bottom: 10px;
        }
        
        /* Hint area */
        .hint-area {
            background-color: #fff8e6;
            padding: 15px;
            border-radius: 10px;
            margin-top: 10px;
        }
        
        /* Feedback messages */
        .success-message {
            color: #28a745;
            font-weight: bold;
            padding: 10px;
            background-color: #d4edda;
            border-radius: 5px;
            margin-bottom: 10px;
        }
        
        .error-message {
            color: #dc3545;
            font-weight: bold;
            padding: 10px;
            background-color: #f8d7da;
            border-radius: 5px;
            margin-bottom: 10px;
        }
    </style>
    """, unsafe_allow_html=True)

# Initialize session state
def initialize_session_state():
    if 'game_state' not in st.session_state:
        st.session_state.game_state = game_logic.initialize_game_state()
        st.session_state.game_state['current_puzzle'] = game_logic.load_new_puzzle()
    
    if 'user_guess' not in st.session_state:
        st.session_state.user_guess = ""
    
    if 'timer_active' not in st.session_state:
        st.session_state.timer_active = True

# Handle user's guess submission
def submit_guess():
    user_guess = st.session_state.user_guess.strip()
    game_state = st.session_state.game_state
    
    if not user_guess:
        game_state['feedback_message'] = "Please enter a guess!"
        game_state['feedback_type'] = "error"
        return
    
    # Check if the answer is correct
    is_correct, _ = game_logic.check_answer(
        game_state['current_puzzle']['id'], 
        user_guess
    )
    
    if is_correct:
        # Calculate time taken and score
        time_taken = time.time() - game_state['puzzle_start_time']
        score = game_logic.calculate_score(time_taken, game_state['show_hints'])
        
        # Update game state
        game_state['score'] += score
        game_state['puzzles_solved'] += 1
        
        # Add to game history
        game_state['game_history'].append({
            'puzzle_id': game_state['current_puzzle']['id'],
            'result': 'solved',
            'time_taken': time_taken,
            'score': score,
            'hints_used': game_state['show_hints']
        })
        
        # Set feedback message
        game_state['feedback_message'] = f"Correct! The answer is '{user_guess}'. +{score} points!"
        game_state['feedback_type'] = "success"
        
        # Load a new puzzle
        game_state['current_puzzle'] = game_logic.load_new_puzzle()
        game_state['puzzle_start_time'] = time.time()
        game_state['show_hints'] = False
    else:
        # Incorrect answer
        game_state['feedback_message'] = f"'{user_guess}' is not correct. Try again!"
        game_state['feedback_type'] = "error"
    
    # Clear the input field
    st.session_state.user_guess = ""

# Handle hint button
def show_hints():
    st.session_state.game_state = game_logic.reveal_hints(st.session_state.game_state)

# Handle skip button
def skip_puzzle():
    game_state, correct_answer = game_logic.skip_puzzle(st.session_state.game_state)
    st.session_state.game_state = game_state
    st.session_state.game_state['feedback_message'] = f"Puzzle skipped. The answer was '{correct_answer}'."
    st.session_state.game_state['feedback_type'] = "error"

# Display the puzzle images in a 2x2 grid
def display_puzzle_images(puzzle: Dict[str, Any]):
    st.markdown("""
    <div class="image-grid">
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.image(
            puzzle['image_urls']['1'],
            use_column_width=True,
            caption=puzzle['descriptions']['1'] if st.session_state.game_state['show_hints'] else None
        )
        
        st.image(
            puzzle['image_urls']['3'],
            use_column_width=True,
            caption=puzzle['descriptions']['3'] if st.session_state.game_state['show_hints'] else None
        )
    
    with col2:
        st.image(
            puzzle['image_urls']['2'],
            use_column_width=True,
            caption=puzzle['descriptions']['2'] if st.session_state.game_state['show_hints'] else None
        )
        
        st.image(
            puzzle['image_urls']['4'],
            use_column_width=True,
            caption=puzzle['descriptions']['4'] if st.session_state.game_state['show_hints'] else None
        )

# Display game statistics
def display_game_stats():
    game_state = st.session_state.game_state
    
    st.markdown("""
    <div class="score-display">
        <div class="score-item">
            <h3>Score</h3>
            <p>{}</p>
        </div>
        <div class="score-item">
            <h3>Solved</h3>
            <p>{}</p>
        </div>
        <div class="score-item">
            <h3>Skipped</h3>
            <p>{}</p>
        </div>
    </div>
    """.format(
        game_state['score'],
        game_state['puzzles_solved'],
        game_state['puzzles_skipped']
    ), unsafe_allow_html=True)

# Display feedback to the user
def display_feedback():
    game_state = st.session_state.game_state
    
    if game_state['feedback_message']:
        message_type = 'success-message' if game_state['feedback_type'] == 'success' else 'error-message'
        st.markdown(f"""
        <div class="{message_type}">
            {game_state['feedback_message']}
        </div>
        """, unsafe_allow_html=True)
        
        # Clear feedback after display
        game_state['feedback_message'] = None
        game_state['feedback_type'] = None

# Main app
def main():
    load_css()
    initialize_session_state()
    
    # Title
    st.markdown('<h1 class="title">4 Images 1 Word</h1>', unsafe_allow_html=True)
    
    # Game stats
    display_game_stats()
    
    # Feedback messages
    display_feedback()
    
    # Display current puzzle
    current_puzzle = st.session_state.game_state['current_puzzle']
    if current_puzzle:
        display_puzzle_images(current_puzzle)
        
        # User input area
        st.text_input(
            "What's the word?",
            key="user_guess",
            on_change=submit_guess
        )
        
        # Action buttons
        col1, col2 = st.columns(2)
        with col1:
            st.button("Show Hints", on_click=show_hints, key="hint_button")
        with col2:
            st.button("Skip Puzzle", on_click=skip_puzzle, key="skip_button")
    else:
        st.error("Error loading puzzle. Please refresh the page.")

if __name__ == "__main__":
    main() 