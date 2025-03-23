import time
import uuid
from typing import Dict, Any, List, Optional, Tuple
import s3_utils

def initialize_game_state() -> Dict[str, Any]:
    """
    Initialize the game state with default values.
    
    Returns:
        Dict[str, Any]: The initialized game state
    """
    # Generate a unique session ID for rating analytics
    session_id = str(uuid.uuid4())
    
    return {
        'current_puzzle': None,
        'score': 0,
        'puzzles_solved': 0,
        'puzzles_skipped': 0,
        'hints_used': 0,
        'start_time': time.time(),
        'puzzle_start_time': time.time(),
        'show_hints': False,
        'game_history': [],
        'feedback_message': None,
        'feedback_type': None,  # 'success', 'error', or None
        'session_id': session_id,
        'show_rating_ui': False,
        'last_solved_puzzle': None,
        'current_ratings': None,
    }

def load_new_puzzle() -> Optional[Dict[str, Any]]:
    """
    Load a new random puzzle.
    
    Returns:
        Dict[str, Any]: The puzzle data
    """
    try:
        puzzle = s3_utils.get_random_puzzle()
        if puzzle:
            # Reset puzzle-specific state
            puzzle['show_hints'] = False
            puzzle['start_time'] = time.time()
        else:
            print("Error: s3_utils.get_random_puzzle() returned None")
        return puzzle
    except Exception as e:
        print(f"Error in load_new_puzzle: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def check_answer(puzzle_id: str, user_guess: str) -> Tuple[bool, Optional[str]]:
    """
    Check if the user's guess is correct.
    
    Args:
        puzzle_id (str): The puzzle ID
        user_guess (str): The user's guess
        
    Returns:
        Tuple[bool, Optional[str]]: (is_correct, correct_answer if incorrect)
    """
    if not user_guess.strip():
        return False, None
        
    is_correct = s3_utils.validate_answer(puzzle_id, user_guess)
    
    if is_correct:
        return True, None
    else:
        # Only return the correct answer if the user wants to skip
        return False, None

def reveal_hints(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Update the state to show hints for the current puzzle.
    
    Args:
        state (Dict[str, Any]): The current game state
        
    Returns:
        Dict[str, Any]: The updated state
    """
    if state['current_puzzle']:
        state['show_hints'] = True
        state['hints_used'] += 1
    return state

def skip_puzzle(state: Dict[str, Any]) -> Tuple[Dict[str, Any], str]:
    """
    Skip the current puzzle and load a new one.
    
    Args:
        state (Dict[str, Any]): The current game state
        
    Returns:
        Tuple[Dict[str, Any], str]: The updated state and the skipped puzzle's answer
    """
    skipped_puzzle_id = state['current_puzzle']['id']
    correct_answer = s3_utils.get_solution(skipped_puzzle_id)
    
    # Store the skipped puzzle for rating
    state['last_solved_puzzle'] = {
        'id': skipped_puzzle_id,
        'target_word': correct_answer,
        'time_to_solve': time.time() - state['puzzle_start_time'],
        'hints_used': state['show_hints'],
        'was_skipped': True
    }
    
    # Update game history
    state['game_history'].append({
        'puzzle_id': skipped_puzzle_id,
        'result': 'skipped',
        'correct_answer': correct_answer
    })
    
    # Update game metrics
    state['puzzles_skipped'] += 1
    
    # Set flag to show rating UI
    state['show_rating_ui'] = True
    
    # Set feedback message but don't load new puzzle yet
    state['feedback_message'] = f"Puzzle skipped. The answer was '{correct_answer}'."
    state['feedback_type'] = "error"
    
    return state, correct_answer

def calculate_score(time_taken: float, hints_used: bool) -> int:
    """
    Calculate the score for solving a puzzle.
    
    Args:
        time_taken (float): Time taken to solve the puzzle in seconds
        hints_used (bool): Whether hints were used
        
    Returns:
        int: The calculated score
    """
    # Base score
    base_score = 100
    
    # Time factor: Faster solutions get more points
    time_factor = max(0, min(1, 1 - (time_taken / 120)))  # Cap at 2 minutes
    time_bonus = int(50 * time_factor)
    
    # Hint penalty
    hint_penalty = 30 if hints_used else 0
    
    # Calculate final score
    final_score = base_score + time_bonus - hint_penalty
    
    return max(10, final_score)  # Minimum score of 10

def solve_puzzle(state: Dict[str, Any], user_guess: str) -> Dict[str, Any]:
    """
    Handle a correct answer and prepare for rating.
    
    Args:
        state (Dict[str, Any]): The current game state
        user_guess (str): The user's guess (correct answer)
        
    Returns:
        Dict[str, Any]: The updated game state
    """
    # Calculate time taken and score
    time_taken = time.time() - state['puzzle_start_time']
    score = calculate_score(time_taken, state['show_hints'])
    
    # Store the solved puzzle for rating
    state['last_solved_puzzle'] = {
        'id': state['current_puzzle']['id'],
        'target_word': user_guess,
        'time_to_solve': time_taken,
        'hints_used': state['show_hints'],
        'was_skipped': False
    }
    
    # Update game state
    state['score'] += score
    state['puzzles_solved'] += 1
    
    # Add to game history
    state['game_history'].append({
        'puzzle_id': state['current_puzzle']['id'],
        'result': 'solved',
        'time_taken': time_taken,
        'score': score,
        'hints_used': state['show_hints']
    })
    
    # Set flag to show rating UI
    state['show_rating_ui'] = True
    
    # Set feedback message
    state['feedback_message'] = f"Correct! The answer is '{user_guess}'. +{score} points!"
    state['feedback_type'] = "success"
    
    return state

def submit_rating(state: Dict[str, Any], difficulty_rating: int, fun_rating: int) -> Dict[str, Any]:
    """
    Submit ratings for the last solved puzzle.
    
    Args:
        state (Dict[str, Any]): The current game state
        difficulty_rating (int): Rating from 1-5 for difficulty
        fun_rating (int): Rating from 1-5 for fun
        
    Returns:
        Dict[str, Any]: The updated game state
    """
    # Check if we have a last solved puzzle
    if not state['last_solved_puzzle']:
        return state
    
    # Get info about the rated puzzle
    puzzle_id = state['last_solved_puzzle']['id']
    target_word = state['last_solved_puzzle']['target_word']
    time_to_solve = state['last_solved_puzzle']['time_to_solve']
    hints_used = state['last_solved_puzzle']['hints_used']
    was_skipped = state['last_solved_puzzle'].get('was_skipped', False)
    
    # Submit the rating
    success = s3_utils.submit_puzzle_rating(
        puzzle_id=puzzle_id,
        target_word=target_word,
        difficulty_rating=difficulty_rating,
        fun_rating=fun_rating,
        time_to_solve=time_to_solve,
        hints_used=hints_used,
        session_id=state['session_id'],
        was_skipped=was_skipped
    )
    
    # Update game history with ratings
    for entry in state['game_history']:
        if entry.get('puzzle_id') == puzzle_id and (
            (entry.get('result') == 'solved' and not was_skipped) or 
            (entry.get('result') == 'skipped' and was_skipped)
        ):
            entry['ratings'] = {
                'difficulty': difficulty_rating,
                'fun': fun_rating
            }
            break
    
    # Hide rating UI
    state['show_rating_ui'] = False
    
    # Load new puzzle
    state['current_puzzle'] = load_new_puzzle()
    state['puzzle_start_time'] = time.time()
    state['show_hints'] = False
    
    # Get ratings for the new puzzle if available
    if state['current_puzzle']:
        state['current_ratings'] = s3_utils.get_puzzle_ratings(state['current_puzzle']['id'])
    
    return state

def skip_rating(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Skip rating and load a new puzzle.
    
    Args:
        state (Dict[str, Any]): The current game state
        
    Returns:
        Dict[str, Any]: The updated game state
    """
    # Hide rating UI
    state['show_rating_ui'] = False
    
    # Load new puzzle
    state['current_puzzle'] = load_new_puzzle()
    state['puzzle_start_time'] = time.time()
    state['show_hints'] = False
    
    # Get ratings for the new puzzle if available
    if state['current_puzzle']:
        state['current_ratings'] = s3_utils.get_puzzle_ratings(state['current_puzzle']['id'])
    
    # Clear the last solved puzzle
    state['last_solved_puzzle'] = None
    
    return state 