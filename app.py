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
        
        /* Rating area */
        .rating-area {
            background-color: #f0f8ff;
            padding: 15px;
            border-radius: 10px;
            margin-top: 20px;
            margin-bottom: 20px;
            text-align: center;
        }
        
        .rating-title {
            font-size: 1.2rem;
            margin-bottom: 10px;
            color: #333;
        }
        
        .rating-notice {
            color: #ff6b6b;
            font-weight: bold;
            margin: 10px 0;
        }
        
        .star-rating {
            font-size: 2rem;
            color: #ccc;
            cursor: pointer;
            display: inline-block;
            margin: 0 5px;
        }
        
        .star-rating.selected {
            color: #ffcc00;
        }
        
        .rating-label {
            font-weight: bold;
            margin-top: 10px;
            margin-bottom: 5px;
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
        
        .rating-stars {
            color: #ffcc00;
            margin-left: 5px;
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

# Submit rating
def submit_rating():
    if 'difficulty_rating' not in st.session_state or 'fun_rating' not in st.session_state:
        st.warning("Please select both difficulty and fun ratings.")
        return
    
    # Update game state with ratings
    st.session_state.game_state = game_logic.submit_rating(
        st.session_state.game_state,
        st.session_state.difficulty_rating,
        st.session_state.fun_rating
    )
    
    # Clear the ratings
    if 'difficulty_rating' in st.session_state:
        del st.session_state.difficulty_rating
    if 'fun_rating' in st.session_state:
        del st.session_state.fun_rating
    
    # Set a thank you message
    st.session_state.game_state['feedback_message'] = "Thank you for your ratings!"
    st.session_state.game_state['feedback_type'] = "success"
    
    # Reset rating UI and load new puzzle immediately
    st.session_state.game_state['show_rating_ui'] = False
    st.session_state.game_state['current_puzzle'] = game_logic.load_new_puzzle()
    
    # Streamlit will automatically rerun when session state is modified
    # Don't call st.rerun() from a callback

# Display rating UI for a solved puzzle
def display_rating_ui():
    if not st.session_state.game_state['show_rating_ui']:
        return
    
    # Check if the puzzle was skipped or solved
    was_skipped = st.session_state.game_state['last_solved_puzzle'].get('was_skipped', False)
    puzzle_word = st.session_state.game_state['last_solved_puzzle']['target_word']
    
    st.markdown('<div class="rating-area">', unsafe_allow_html=True)
    
    if was_skipped:
        st.markdown(f'<h3 class="rating-title">Rate this puzzle for "{puzzle_word}" that you skipped:</h3>', unsafe_allow_html=True)
    else:
        st.markdown(f'<h3 class="rating-title">Rate this puzzle for "{puzzle_word}" that you solved:</h3>', unsafe_allow_html=True)
    
    st.markdown('<p class="rating-notice">Please rate this puzzle to continue to the next one.</p>', unsafe_allow_html=True)
    
    # Difficulty rating
    st.markdown('<p class="rating-label">Difficulty:</p>', unsafe_allow_html=True)
    
    difficulty_col1, difficulty_col2, difficulty_col3, difficulty_col4, difficulty_col5 = st.columns(5)
    
    with difficulty_col1:
        if st.button("⭐", key="difficulty_1"):
            st.session_state.difficulty_rating = 1
    with difficulty_col2:
        if st.button("⭐", key="difficulty_2"):
            st.session_state.difficulty_rating = 2
    with difficulty_col3:
        if st.button("⭐", key="difficulty_3"):
            st.session_state.difficulty_rating = 3
    with difficulty_col4:
        if st.button("⭐", key="difficulty_4"):
            st.session_state.difficulty_rating = 4
    with difficulty_col5:
        if st.button("⭐", key="difficulty_5"):
            st.session_state.difficulty_rating = 5
    
    # Show selected difficulty
    difficulty_text = ""
    if 'difficulty_rating' in st.session_state:
        difficulty_value = st.session_state.difficulty_rating
        difficulty_text = f"Selected difficulty rating: {difficulty_value}/5"
    st.markdown(f'<p>{difficulty_text}</p>', unsafe_allow_html=True)
    
    # Fun rating
    st.markdown('<p class="rating-label">Fun:</p>', unsafe_allow_html=True)
    
    fun_col1, fun_col2, fun_col3, fun_col4, fun_col5 = st.columns(5)
    
    with fun_col1:
        if st.button("⭐", key="fun_1"):
            st.session_state.fun_rating = 1
    with fun_col2:
        if st.button("⭐", key="fun_2"):
            st.session_state.fun_rating = 2
    with fun_col3:
        if st.button("⭐", key="fun_3"):
            st.session_state.fun_rating = 3
    with fun_col4:
        if st.button("⭐", key="fun_4"):
            st.session_state.fun_rating = 4
    with fun_col5:
        if st.button("⭐", key="fun_5"):
            st.session_state.fun_rating = 5
    
    # Show selected fun rating
    fun_text = ""
    if 'fun_rating' in st.session_state:
        fun_value = st.session_state.fun_rating
        fun_text = f"Selected fun rating: {fun_value}/5"
    st.markdown(f'<p>{fun_text}</p>', unsafe_allow_html=True)
    
    # Submit button (only enabled when both ratings are selected)
    is_ready = 'difficulty_rating' in st.session_state and 'fun_rating' in st.session_state
    
    if is_ready:
        if st.button("Submit Rating & Continue", key="submit_rating", type="primary", on_click=submit_rating):
            pass  # The on_click handler will call submit_rating
    else:
        st.button("Submit Rating & Continue", key="submit_rating_disabled", disabled=True)
        st.markdown('<p class="rating-notice">Please select both difficulty and fun ratings to continue.</p>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

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
    
    difficulty_avg = ratings['difficulty']['average']
    difficulty_count = ratings['difficulty']['count']
    fun_avg = ratings['fun']['average']
    fun_count = ratings['fun']['count']
    total_ratings = ratings['total_ratings']
    
    st.markdown(f"""
    <div class="current-ratings">
        <span>Difficulty: {difficulty_avg}/5 </span>
        <span class="rating-stars">{'★' * int(round(difficulty_avg))}</span>
        <span>({difficulty_count} ratings)</span>
        <br>
        <span>Fun: {fun_avg}/5 </span>
        <span class="rating-stars">{'★' * int(round(fun_avg))}</span>
        <span>({fun_count} ratings)</span>
        <br>
        <span>Total user ratings: {total_ratings}</span>
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
                
                # Show name input for first puzzle
                if st.session_state.game_state['is_first_puzzle']:
                    st.markdown('<p>Welcome! Please enter your name to begin:</p>', unsafe_allow_html=True)
                    with st.form("name_form"):
                        name_input = st.text_input("Your Name", key="name_input", label_visibility="collapsed")
                        if st.form_submit_button("Start Playing", type="primary", on_click=submit_name):
                            if not name_input.strip():
                                st.error("Please enter your name to continue!")
                
                # Show puzzle input if not first puzzle or name is set
                if not st.session_state.game_state['is_first_puzzle']:
                    # Label for the input
                    st.markdown(f'<p>Welcome back, {st.session_state.game_state["player_name"]}! What\'s the word that connects all these images?</p>', unsafe_allow_html=True)
                    
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
        
        1. Look at the four images.
        2. Think of a single word that connects all four images.
        3. Type your guess in the input field and press Enter.
        4. If you're stuck, use the "Show Hints" button to see image descriptions.
        5. Use the "Skip Puzzle" button to move to a new puzzle.
        6. After solving a puzzle, you can rate its difficulty and fun factor.
        
        ## Scoring
        - Base score: 100 points per puzzle
        - Time bonus: Up to 50 extra points for solving quickly
        - Hint penalty: -30 points if hints are used
        """)

# Run the app
if __name__ == "__main__":
    main() 