import streamlit as st
import time
import game_logic
import s3_utils
from typing import Dict, Any

# Set page configuration
st.set_page_config(
    page_title="Quadrality",
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
        
        /* Fix button alignment */
        div.element-container div.row-widget.stButton {
            margin-top: 1px;
            padding-top: 2px;
        }
        
        /* Make stButton and stTextInput have the same height */
        .stButton > button {
            height: 38px;
            padding-top: 0;
            padding-bottom: 0;
            line-height: 1.6;
        }
        
        /* Remove bottom margin from text input to align with button */
        div.css-1n543e5, div.css-ocqkz7, div.css-keje6w {
            margin-bottom: 0 !important;
        }
        
        /* Fix alignment in column layout */
        div.row-widget.stHorizontal > div {
            display: flex;
            align-items: center;
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
        
        /* Rating buttons - Base style */
        .rating-area .stButton button {
            width: 100%;
            margin: 0;
            padding: 8px 16px;
            font-size: 1rem;
            transition: all 0.2s ease;
            background-color: white !important;
            color: #31333F !important;
            border: 1px solid #e6e6e6 !important;
            border-radius: 4px;
        }
        
        /* Rating buttons - Hover state */
        .rating-area .stButton button:hover:not([data-baseweb="button"].primary) {
            background-color: #f0f2f6 !important;
            border-color: #d0d3d9 !important;
        }
        
        /* Rating buttons - Selected state */
        .rating-area .stButton button[data-baseweb="button"].primary {
            background-color: #ff4b4b !important;
            color: white !important;
            border-color: #ff4b4b !important;
        }
        
        /* Rating area layout */
        .rating-area {
            background-color: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
            margin-top: 20px;
            margin-bottom: 20px;
        }
        
        .rating-title {
            font-size: 1.2rem;
            margin-bottom: 15px;
            color: #31333F;
        }
        
        .rating-label {
            font-weight: 500;
            margin-top: 15px;
            margin-bottom: 10px;
            color: #31333F;
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
        
        /* Error message */
        .error-message {
            color: #dc3545;
            font-weight: bold;
            padding: 10px;
            background-color: #f8d7da;
            border-radius: 5px;
            margin-bottom: 10px;
        }
        
        /* Current ratings display */
        .current-ratings {
            background-color: #f9f9f9;
            padding: 8px 12px;
            border-radius: 8px;
            font-size: 0.9rem;
            color: #555;
            display: inline-block;
            margin-bottom: 10px;
        }
        
        /* Override Streamlit's button styles */
        .stButton > button:active {
            background-color: #ff4b4b !important;
            color: white !important;
            border-color: #ff4b4b !important;
        }
        
        .stButton > button:focus {
            box-shadow: none !important;
        }
        
        /* Force immediate color change on click */
        .stButton > button:active,
        .stButton > button[data-baseweb="button"].primary {
            transform: none !important;
            transition: none !important;
        }
        
        /* Fix for inconsistent button styling on first click */
        .rating-area .stButton button:active,
        .rating-area .stButton button[data-baseweb="button"].primary {
            background-color: #ff4b4b !important;
            color: white !important;
            border-color: #ff4b4b !important;
        }
        
        /* Fix for Streamlit's button styling inconsistency */
        .rating-area .stButton button[data-baseweb="button"] {
            background-color: white !important;
            color: #31333F !important;
            border: 1px solid #e6e6e6 !important;
        }
        
        /* Override Streamlit's button styling for clicked buttons */
        .rating-area .stButton button[data-baseweb="button"]:active,
        .rating-area .stButton button[data-baseweb="button"].primary {
            background-color: #ff4b4b !important;
            color: white !important;
            border-color: #ff4b4b !important;
        }
    </style>
    """, unsafe_allow_html=True)

# Initialize session state
def initialize_session_state():
    if 'game_state' not in st.session_state:
        st.session_state.game_state = game_logic.initialize_game_state()
        st.session_state.game_state['current_puzzle'] = game_logic.load_new_puzzle()
        st.session_state.game_state['player_name'] = None
        st.session_state.game_state['is_first_puzzle'] = True
    
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
        # Update game state with the solved puzzle
        st.session_state.game_state = game_logic.solve_puzzle(game_state, user_guess)
    else:
        # Incorrect answer
        game_state['feedback_message'] = f"'{user_guess}' is not correct. Try again!"
        game_state['feedback_type'] = "error"

# Handle hint button
def show_hints():
    st.session_state.game_state = game_logic.reveal_hints(st.session_state.game_state)

# Handle skip button
def skip_puzzle():
    game_state, correct_answer = game_logic.skip_puzzle(st.session_state.game_state)
    st.session_state.game_state = game_state

# Display the puzzle images in a 2x2 grid
def display_puzzle_images(puzzle: Dict[str, Any]):
    st.markdown("""
    <div class="image-grid">
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.image(
            puzzle['image_urls']['1'],
            use_container_width=True,
            caption=puzzle['descriptions']['1'] if st.session_state.game_state['show_hints'] else None
        )
        
        st.image(
            puzzle['image_urls']['3'],
            use_container_width=True,
            caption=puzzle['descriptions']['3'] if st.session_state.game_state['show_hints'] else None
        )
    
    with col2:
        st.image(
            puzzle['image_urls']['2'],
            use_container_width=True,
            caption=puzzle['descriptions']['2'] if st.session_state.game_state['show_hints'] else None
        )
        
        st.image(
            puzzle['image_urls']['4'],
            use_container_width=True,
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
        message_type = game_state['feedback_type'] or "info"
        
        if message_type == "success":
            st.markdown(f"""
            <div class="success-message">
                {game_state['feedback_message']}
            </div>
            """, unsafe_allow_html=True)
        elif message_type == "error":
            st.markdown(f"""
            <div class="error-message">
                {game_state['feedback_message']}
            </div>
            """, unsafe_allow_html=True)
        else:
            st.info(game_state['feedback_message'])

# Display rating UI for a solved puzzle
def display_rating_ui():
    if not st.session_state.game_state['show_rating_ui']:
        return
    
    # Check if the puzzle was skipped or solved
    was_skipped = st.session_state.game_state['last_solved_puzzle'].get('was_skipped', False)
    
    # If puzzle was skipped, automatically skip rating and load new puzzle
    if was_skipped:
        st.session_state.game_state = game_logic.skip_rating(st.session_state.game_state)
        return
    
    puzzle_word = st.session_state.game_state['last_solved_puzzle']['target_word']
    
    st.markdown('<div class="rating-area">', unsafe_allow_html=True)
    
    st.markdown(f'<h3 class="rating-title">Rate this puzzle for "{puzzle_word}" that you solved:</h3>', unsafe_allow_html=True)
    
    # Initialize default ratings if not already set
    if 'difficulty_rating' not in st.session_state:
        st.session_state.difficulty_rating = "easy"
    if 'issue_rating' not in st.session_state:
        st.session_state.issue_rating = "no_issues"
    
    # Difficulty rating using radio buttons
    st.markdown('<p class="rating-label">How difficult was this puzzle?</p>', unsafe_allow_html=True)
    
    difficulty_options = ["Easy", "Medium", "Hard"]
    selected_difficulty = st.radio(
        "Select difficulty:",
        options=difficulty_options,
        horizontal=True,
        label_visibility="collapsed",
        key="difficulty_radio",
        index=0  # Default to "Easy"
    )
    
    # Set the difficulty rating based on the radio selection
    if selected_difficulty:
        st.session_state.difficulty_rating = selected_difficulty.lower()
    
    # Issue rating using radio buttons
    st.markdown('<p class="rating-label">Did you encounter any issues with this puzzle?</p>', unsafe_allow_html=True)
    
    issue_options = ["No Issues", "Bad Images", "Bad Puzzle"]
    selected_issue = st.radio(
        "Select issue:",
        options=issue_options,
        horizontal=True,
        label_visibility="collapsed",
        key="issue_radio",
        index=0  # Default to "No Issues"
    )
    
    # Set the issue rating based on the radio selection
    if selected_issue:
        st.session_state.issue_rating = selected_issue.lower().replace(" ", "_")
    
    # Next Puzzle button
    if st.button("Next Puzzle", key="next_puzzle", type="primary", on_click=submit_rating):
        pass  # The on_click handler will call submit_rating
    
    st.markdown('</div>', unsafe_allow_html=True)

def submit_rating():
    # If ratings are selected, submit them
    if st.session_state.get('difficulty_rating') or st.session_state.get('issue_rating'):
        # Update game state with ratings
        st.session_state.game_state = game_logic.submit_rating(
            st.session_state.game_state,
            st.session_state.get('difficulty_rating'),
            st.session_state.get('issue_rating')
        )
        
        # Set a thank you message if ratings were provided
        st.session_state.game_state['feedback_message'] = "Thank you for your feedback!"
        st.session_state.game_state['feedback_type'] = "success"
    
    # Clear the ratings
    if 'difficulty_rating' in st.session_state:
        del st.session_state.difficulty_rating
    if 'issue_rating' in st.session_state:
        del st.session_state.issue_rating
    
    # Reset rating UI and load new puzzle immediately
    st.session_state.game_state['show_rating_ui'] = False
    st.session_state.game_state['current_puzzle'] = game_logic.load_new_puzzle()

# Handle text input when Enter is pressed
def handle_text_input():
    # If the user pressed Enter in the text field, submit the guess
    if 'user_guess_input' in st.session_state and st.session_state.user_guess_input:
        st.session_state.user_guess = st.session_state.user_guess_input
        submit_guess()

# Display current puzzle ratings if available (not displayed to users, for analysis only)
def display_current_ratings():
    ratings = st.session_state.game_state.get('current_ratings')
    
    if not ratings:
        return
    
    difficulty_stats = ratings['difficulty']
    issue_stats = ratings['fun']  # We'll use the 'fun' field for issue tracking
    total_ratings = ratings['total_ratings']
    
    st.markdown(f"""
    <div class="current-ratings">
        <span>Difficulty Distribution:</span>
        <br>
        <span>Easy: {difficulty_stats.get('easy', 0)}</span>
        <span>Medium: {difficulty_stats.get('medium', 0)}</span>
        <span>Hard: {difficulty_stats.get('hard', 0)}</span>
        <br>
        <span>Issues Reported:</span>
        <br>
        <span>Bad Images: {issue_stats.get('bad_images', 0)}</span>
        <span>Bad Puzzle: {issue_stats.get('bad_puzzle', 0)}</span>
        <span>No Issues: {issue_stats.get('no_issues', 0)}</span>
        <br>
        <span>Total ratings: {total_ratings}</span>
    </div>
    """, unsafe_allow_html=True)

# Handle name submission
def submit_name():
    if 'name_input' in st.session_state and st.session_state.name_input.strip():
        st.session_state.game_state['player_name'] = st.session_state.name_input.strip()
        st.session_state.game_state['is_first_puzzle'] = False

# Main app
def main():
    # Load CSS
    load_css()
    
    # Initialize session state
    initialize_session_state()
    
    # Display the title
    st.markdown('<h1 class="title">Quadrality 🧩</h1>', unsafe_allow_html=True)
    
    try:
        # Get the current puzzle
        current_puzzle = st.session_state.game_state['current_puzzle']
        
        if current_puzzle is None:
            st.error("Error loading puzzle. Please check your AWS credentials and S3 bucket configuration.")
            return
        
        # Display game statistics
        display_game_stats()
        
        # Display the puzzle images
        display_puzzle_images(current_puzzle)
        
        # Display feedback if there is any
        display_feedback()
        
        # Check if we should show rating UI
        if st.session_state.game_state['show_rating_ui']:
            display_rating_ui()
        else:
            # User input area
            with st.container():
                st.markdown('<div class="input-area">', unsafe_allow_html=True)
                
                # Label for the input
                st.markdown('<p>What\'s the word that connects all these images?</p>', unsafe_allow_html=True)
                
                # Create a row with input field and button
                input_col, button_col = st.columns([4, 1])
                
                # User input in first column
                with input_col:
                    user_input = st.text_input("", key="user_guess_input", label_visibility="collapsed", on_change=handle_text_input)
                
                # Submit button in second column
                with button_col:
                    if st.button("Submit Guess", type="primary", on_click=submit_guess):
                        if 'user_guess_input' in st.session_state and st.session_state.user_guess_input:
                            st.session_state.user_guess = st.session_state.user_guess_input
                
                # Action buttons
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button("Show Hints", on_click=show_hints):
                        pass
                
                with col2:
                    if st.button("Skip Puzzle", on_click=skip_puzzle):
                        pass
                
                st.markdown('</div>', unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Error loading puzzle: {str(e)}\nPlease check your configuration and refresh the page.")
        st.exception(e)  # This will display the full traceback for debugging
    
    # About section in expander
    with st.expander("About This Game"):
        st.markdown("""
        ## How to Play
        
        1. Look at the four images displayed in the grid.
        2. Think of a single word that connects all four images.
        3. Type your guess and press Enter or click Submit.
        4. Use "Show Hints" for image descriptions or "Skip Puzzle" to move on.
        5. After solving, rate the difficulty and report any issues.
        
        ## Tips
        - The connecting word can be a noun, verb, or adjective.
        - Sometimes the connection is abstract or based on wordplay.
        - Take your time - there's no rush to solve.
        
        ## About Quadrality
        Quadrality is a word puzzle game that challenges you to find connections between seemingly unrelated images. Each puzzle presents four images that share a common word or concept.
        
        Enjoy the challenge!
        """)

# Run the app
if __name__ == "__main__":
    main() 