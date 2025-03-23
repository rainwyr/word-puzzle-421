import time
from typing import Dict, Any, List, Optional, Tuple
import s3_utils

def initialize_game_state() -> Dict[str, Any]:
    """
    Initialize the game state with default values.
    
    Returns:
        Dict[str, Any]: The initialized game state
    """
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
    }

def load_new_puzzle() -> Optional[Dict[str, Any]]:
    """
    Load a new random puzzle.
    
    Returns:
        Dict[str, Any]: The puzzle data
    """
    puzzle = s3_utils.get_random_puzzle()
    if puzzle:
        # Reset puzzle-specific state
        puzzle['show_hints'] = False
        puzzle['start_time'] = time.time()
    return puzzle

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
    
    # Update game history
    state['game_history'].append({
        'puzzle_id': skipped_puzzle_id,
        'result': 'skipped',
        'correct_answer': correct_answer
    })
    
    # Update game metrics
    state['puzzles_skipped'] += 1
    
    # Load a new puzzle
    state['current_puzzle'] = load_new_puzzle()
    state['puzzle_start_time'] = time.time()
    state['show_hints'] = False
    
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