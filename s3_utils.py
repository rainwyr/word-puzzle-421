import boto3
import json
import random
import os
import uuid
import datetime
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# AWS S3 configuration
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_DEFAULT_REGION = os.getenv('AWS_DEFAULT_REGION', 'us-east-1')
S3_BUCKET_NAME = os.getenv('S3_BUCKET_NAME', 'word-puzzle-421')

# Initialize S3 client
s3_client = boto3.client(
    's3',
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_DEFAULT_REGION
)

def check_aws_configuration():
    """
    Check if AWS credentials and bucket configuration are valid.
    
    Returns:
        bool: True if configuration is valid, False otherwise
    """
    try:
        # Check if credentials are set
        if not AWS_ACCESS_KEY_ID or not AWS_SECRET_ACCESS_KEY:
            print("ERROR: AWS credentials not set. Please check your .env file.")
            return False
        
        # Check if bucket exists and is accessible
        response = s3_client.head_bucket(Bucket=S3_BUCKET_NAME)
        print(f"Successfully connected to S3 bucket: {S3_BUCKET_NAME}")
        
        # Check if puzzle directory exists
        response = s3_client.list_objects_v2(
            Bucket=S3_BUCKET_NAME,
            Prefix='puzzles/',
            MaxKeys=1
        )
        
        if 'Contents' not in response or len(response['Contents']) == 0:
            print(f"ERROR: No puzzles found in the S3 bucket: {S3_BUCKET_NAME}")
            return False
            
        return True
    except Exception as e:
        print(f"ERROR checking AWS configuration: {type(e).__name__}: {str(e)}")
        return False

# Check AWS configuration on module import
aws_config_valid = check_aws_configuration()
if not aws_config_valid:
    print("WARNING: AWS configuration is invalid. The app may not function correctly.")

def get_puzzle_ids() -> List[str]:
    """
    Get all puzzle IDs from the S3 bucket.
    
    Returns:
        List[str]: A list of puzzle IDs
    """
    try:
        # List all objects in the puzzles/ directory
        response = s3_client.list_objects_v2(
            Bucket=S3_BUCKET_NAME,
            Prefix='puzzles/'
        )
        
        # Extract puzzle IDs from the filenames
        puzzle_ids = []
        for obj in response.get('Contents', []):
            key = obj['Key']
            if key.endswith('.json'):
                puzzle_id = key.split('/')[-1].replace('.json', '')
                puzzle_ids.append(puzzle_id)
        
        if not puzzle_ids:
            print(f"Warning: No puzzle files found in S3 bucket '{S3_BUCKET_NAME}' under 'puzzles/' prefix")
        
        return puzzle_ids
    except Exception as e:
        print(f"Error getting puzzle IDs: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Check if credentials are missing
        if not AWS_ACCESS_KEY_ID or not AWS_SECRET_ACCESS_KEY:
            print("Missing AWS credentials. Please check your .env file.")
        
        # Check if bucket name is valid
        print(f"Using S3 bucket name: {S3_BUCKET_NAME}")
        
        return []

def get_random_puzzle() -> Optional[Dict[str, Any]]:
    """
    Get a random puzzle from the S3 bucket.
    
    Returns:
        Dict[str, Any]: A puzzle dictionary with images and descriptions
    """
    try:
        puzzle_ids = get_puzzle_ids()
        if not puzzle_ids:
            print("No puzzle IDs found in S3, falling back to example puzzle")
            return load_example_puzzle()
        
        # Select a random puzzle ID
        random_id = random.choice(puzzle_ids)
        print(f"Selected random puzzle ID: {random_id}")
        
        return get_puzzle_by_id(random_id)
    except Exception as e:
        print(f"Error in get_random_puzzle: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return load_example_puzzle()

def get_puzzle_by_id(puzzle_id: str) -> Optional[Dict[str, Any]]:
    """
    Get a puzzle by its ID.
    
    Args:
        puzzle_id (str): The puzzle ID
        
    Returns:
        Dict[str, Any]: The puzzle data
    """
    try:
        # Get the puzzle JSON file
        response = s3_client.get_object(
            Bucket=S3_BUCKET_NAME,
            Key=f'puzzles/{puzzle_id}.json'
        )
        
        # Parse the JSON
        puzzle_data = json.loads(response['Body'].read().decode('utf-8'))
        
        # Add the puzzle ID to the data
        puzzle_data['id'] = puzzle_id
        
        # Add the full image URLs
        for key, image_name in puzzle_data.get('image_urls', {}).items():
            puzzle_data['image_urls'][key] = generate_image_url(image_name)
        
        return puzzle_data
    except Exception as e:
        print(f"Error getting puzzle {puzzle_id}: {e}")
        return None

def validate_answer(puzzle_id: str, guess: str) -> bool:
    """
    Validate the user's guess against the correct answer.
    
    Args:
        puzzle_id (str): The puzzle ID
        guess (str): The user's guess
        
    Returns:
        bool: True if the guess is correct, False otherwise
    """
    try:
        # Special handling for fallback puzzles
        if puzzle_id == "dummy-puzzle":
            return guess.lower() == "apple"
        
        # Try to load from example solution for the example puzzle
        if puzzle_id == "2d5a7f8e-9b3c-4d12-a8f6-1e2c3b4d5e6f":
            try:
                with open("example_solution.json", 'r') as f:
                    solution_data = json.load(f)
                return solution_data.get('target_word', '').lower() == guess.lower()
            except:
                # Hardcoded fallback for the example puzzle
                return guess.lower() == "base"
        
        # Normal S3 solution path
        # Get the solution JSON file
        response = s3_client.get_object(
            Bucket=S3_BUCKET_NAME,
            Key=f'solutions_by_id/{puzzle_id}.json'
        )
        
        # Parse the JSON
        solution_data = json.loads(response['Body'].read().decode('utf-8'))
        
        # Compare the guess with the target word (case-insensitive)
        return solution_data.get('target_word', '').lower() == guess.lower()
    except Exception as e:
        print(f"Error validating answer for puzzle {puzzle_id}: {type(e).__name__}: {str(e)}")
        # For unknown puzzles, always return false
        return False

def get_solution(puzzle_id: str) -> Optional[str]:
    """
    Get the solution for a puzzle.
    
    Args:
        puzzle_id (str): The puzzle ID
        
    Returns:
        str: The target word
    """
    try:
        # Special handling for fallback puzzles
        if puzzle_id == "dummy-puzzle":
            return "apple"
            
        # Try to load from example solution for the example puzzle
        if puzzle_id == "2d5a7f8e-9b3c-4d12-a8f6-1e2c3b4d5e6f":
            try:
                with open("example_solution.json", 'r') as f:
                    solution_data = json.load(f)
                return solution_data.get('target_word', 'base')
            except:
                # Hardcoded fallback for the example puzzle
                return "base"
        
        # Normal S3 path
        # Get the solution JSON file
        response = s3_client.get_object(
            Bucket=S3_BUCKET_NAME,
            Key=f'solutions_by_id/{puzzle_id}.json'
        )
        
        # Parse the JSON
        solution_data = json.loads(response['Body'].read().decode('utf-8'))
        
        return solution_data.get('target_word', '')
    except Exception as e:
        print(f"Error getting solution for puzzle {puzzle_id}: {type(e).__name__}: {str(e)}")
        return "unknown"

def generate_image_url(image_name: str) -> str:
    """
    Generate a pre-signed URL for an image.
    
    Args:
        image_name (str): The image filename
        
    Returns:
        str: The pre-signed URL
    """
    try:
        # Generate a pre-signed URL for the image
        url = s3_client.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': S3_BUCKET_NAME,
                'Key': f'images/{image_name}'
            },
            ExpiresIn=3600  # URL expires in 1 hour
        )
        return url
    except Exception as e:
        print(f"Error generating URL for image {image_name}: {e}")
        return ""

def load_example_puzzle() -> Dict[str, Any]:
    """
    Load the example puzzle as a fallback when S3 is not available.
    
    Returns:
        Dict[str, Any]: The example puzzle data
    """
    try:
        # Path to example puzzle file
        example_puzzle_path = "example_puzzle.json"
        
        # Check if the file exists
        if not os.path.exists(example_puzzle_path):
            print(f"Error: Example puzzle file not found at {example_puzzle_path}")
            return create_dummy_puzzle()
        
        # Load the example puzzle
        with open(example_puzzle_path, 'r') as f:
            puzzle_data = json.load(f)
        
        # Add placeholder URLs for images (locally served images)
        for key in puzzle_data.get('image_urls', {}):
            # Use placeholders that would be valid in Streamlit
            puzzle_data['image_urls'][key] = f"https://via.placeholder.com/300?text=Example+Image+{key}"
        
        print("Successfully loaded example puzzle as fallback")
        return puzzle_data
    except Exception as e:
        print(f"Error loading example puzzle: {type(e).__name__}: {str(e)}")
        return create_dummy_puzzle()

def create_dummy_puzzle() -> Dict[str, Any]:
    """
    Create a dummy puzzle as a last resort fallback.
    
    Returns:
        Dict[str, Any]: A simple dummy puzzle
    """
    print("Creating dummy puzzle as ultimate fallback")
    return {
        "id": "dummy-puzzle",
        "descriptions": {
            "1": "A round fruit with red or green skin",
            "2": "A tech company with a fruit logo",
            "3": "A famous city nicknamed 'The Big Apple'",
            "4": "The fruit mentioned in the story of Adam and Eve"
        },
        "image_urls": {
            "1": "https://via.placeholder.com/300?text=Apple+Fruit",
            "2": "https://via.placeholder.com/300?text=Apple+Company",
            "3": "https://via.placeholder.com/300?text=New+York",
            "4": "https://via.placeholder.com/300?text=Garden+of+Eden"
        }
    }

# Rating Functions

def get_puzzle_ratings(puzzle_id: str) -> Optional[Dict[str, Any]]:
    """
    Get ratings for a puzzle.
    
    Args:
        puzzle_id (str): The puzzle ID
        
    Returns:
        Dict[str, Any]: The ratings data, or None if no ratings exist
    """
    try:
        # Get the ratings JSON file
        response = s3_client.get_object(
            Bucket=S3_BUCKET_NAME,
            Key=f'ratings/{puzzle_id}.json'
        )
        
        # Parse the JSON
        ratings_data = json.loads(response['Body'].read().decode('utf-8'))
        return ratings_data
    except Exception as e:
        print(f"Info: No ratings found for puzzle {puzzle_id}: {type(e).__name__}: {str(e)}")
        return None

def submit_puzzle_rating(puzzle_id: str, target_word: str, difficulty_rating: int, fun_rating: int, 
                        time_to_solve: float, hints_used: bool, session_id: str, was_skipped: bool = False) -> bool:
    """
    Submit a rating for a puzzle and update aggregate ratings.
    
    Args:
        puzzle_id (str): The puzzle ID
        target_word (str): The solution word
        difficulty_rating (int): Rating from 1-5 for difficulty
        fun_rating (int): Rating from 1-5 for fun
        time_to_solve (float): Time taken to solve in seconds
        hints_used (bool): Whether hints were used
        session_id (str): Anonymous session identifier
        was_skipped (bool): Whether the puzzle was skipped
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # First log the individual rating
        log_individual_rating(
            puzzle_id=puzzle_id,
            target_word=target_word,
            difficulty_rating=difficulty_rating,
            fun_rating=fun_rating,
            time_to_solve=time_to_solve,
            hints_used=hints_used,
            session_id=session_id,
            was_skipped=was_skipped
        )
        
        # Then update the aggregate ratings
        # Get current ratings if they exist
        current_ratings = get_puzzle_ratings(puzzle_id)
        
        if current_ratings:
            # Update existing ratings
            difficulty_count = current_ratings['difficulty']['count']
            difficulty_avg = current_ratings['difficulty']['average']
            fun_count = current_ratings['fun']['count']
            fun_avg = current_ratings['fun']['average']
            total = current_ratings['total_ratings']
            
            # Calculate new averages
            new_difficulty_avg = ((difficulty_avg * difficulty_count) + difficulty_rating) / (difficulty_count + 1)
            new_fun_avg = ((fun_avg * fun_count) + fun_rating) / (fun_count + 1)
            
            # Create updated ratings object
            updated_ratings = {
                "puzzle_id": puzzle_id,
                "target_word": target_word,
                "difficulty": {
                    "average": round(new_difficulty_avg, 2),
                    "count": difficulty_count + 1
                },
                "fun": {
                    "average": round(new_fun_avg, 2),
                    "count": fun_count + 1
                },
                "total_ratings": total + 1,
                "last_updated": datetime.datetime.utcnow().isoformat()
            }
        else:
            # Create new ratings object
            updated_ratings = {
                "puzzle_id": puzzle_id,
                "target_word": target_word,
                "difficulty": {
                    "average": difficulty_rating,
                    "count": 1
                },
                "fun": {
                    "average": fun_rating,
                    "count": 1
                },
                "total_ratings": 1,
                "last_updated": datetime.datetime.utcnow().isoformat()
            }
        
        # Save the updated ratings
        s3_client.put_object(
            Bucket=S3_BUCKET_NAME,
            Key=f'ratings/{puzzle_id}.json',
            Body=json.dumps(updated_ratings, indent=2),
            ContentType='application/json'
        )
        
        print(f"Successfully updated ratings for puzzle {puzzle_id}")
        return True
    except Exception as e:
        print(f"Error submitting rating for puzzle {puzzle_id}: {type(e).__name__}: {str(e)}")
        
        # Save to local file as fallback
        try:
            ratings_dir = "local_ratings"
            os.makedirs(ratings_dir, exist_ok=True)
            
            with open(f"{ratings_dir}/{puzzle_id}.json", 'w') as f:
                if current_ratings:
                    # Update existing ratings
                    difficulty_count = current_ratings['difficulty']['count']
                    difficulty_avg = current_ratings['difficulty']['average']
                    fun_count = current_ratings['fun']['count']
                    fun_avg = current_ratings['fun']['average']
                    total = current_ratings['total_ratings']
                    
                    # Calculate new averages
                    new_difficulty_avg = ((difficulty_avg * difficulty_count) + difficulty_rating) / (difficulty_count + 1)
                    new_fun_avg = ((fun_avg * fun_count) + fun_rating) / (fun_count + 1)
                    
                    # Create updated ratings object
                    updated_ratings = {
                        "puzzle_id": puzzle_id,
                        "target_word": target_word,
                        "difficulty": {
                            "average": round(new_difficulty_avg, 2),
                            "count": difficulty_count + 1
                        },
                        "fun": {
                            "average": round(new_fun_avg, 2),
                            "count": fun_count + 1
                        },
                        "total_ratings": total + 1,
                        "last_updated": datetime.datetime.utcnow().isoformat()
                    }
                else:
                    # Create new ratings object
                    updated_ratings = {
                        "puzzle_id": puzzle_id,
                        "target_word": target_word,
                        "difficulty": {
                            "average": difficulty_rating,
                            "count": 1
                        },
                        "fun": {
                            "average": fun_rating,
                            "count": 1
                        },
                        "total_ratings": 1,
                        "last_updated": datetime.datetime.utcnow().isoformat()
                    }
                
                json.dump(updated_ratings, f, indent=2)
            print(f"Saved ratings to local file as fallback for puzzle {puzzle_id}")
        except Exception as local_err:
            print(f"Error saving ratings locally: {local_err}")
        
        return False

def log_individual_rating(puzzle_id: str, target_word: str, difficulty_rating: int, fun_rating: int, 
                         time_to_solve: float, hints_used: bool, session_id: str, was_skipped: bool = False) -> bool:
    """
    Log an individual rating to the ratings log.
    
    Args:
        puzzle_id (str): The puzzle ID
        target_word (str): The solution word
        difficulty_rating (int): Rating from 1-5 for difficulty
        fun_rating (int): Rating from 1-5 for fun
        time_to_solve (float): Time taken to solve in seconds
        hints_used (bool): Whether hints were used
        session_id (str): Anonymous session identifier
        was_skipped (bool): Whether the puzzle was skipped
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Create log entry
        now = datetime.datetime.utcnow()
        timestamp = now.isoformat()
        
        # Create log key based on current hour
        log_key = f"ratings_log/{now.strftime('%Y-%m-%d-%H')}.json"
        
        # Create the log entry
        log_entry = {
            "log_id": str(uuid.uuid4()),
            "puzzle_id": puzzle_id,
            "target_word": target_word,
            "timestamp": timestamp,
            "session_id": session_id,
            "ratings": {
                "difficulty": difficulty_rating,
                "fun": fun_rating
            },
            "metadata": {
                "time_to_solve": time_to_solve,
                "hints_used": hints_used,
                "was_skipped": was_skipped,
                "platform": "unknown",  # Could be determined from user agent
                "browser": "unknown"    # Could be determined from user agent
            }
        }
        
        # Try to get existing log file
        try:
            response = s3_client.get_object(
                Bucket=S3_BUCKET_NAME,
                Key=log_key
            )
            
            # Parse existing logs
            existing_logs = json.loads(response['Body'].read().decode('utf-8'))
            
            # Append new log
            existing_logs.append(log_entry)
            
            # Save updated logs
            s3_client.put_object(
                Bucket=S3_BUCKET_NAME,
                Key=log_key,
                Body=json.dumps(existing_logs, indent=2),
                ContentType='application/json'
            )
        except:
            # File doesn't exist, create new log file with single entry
            s3_client.put_object(
                Bucket=S3_BUCKET_NAME,
                Key=log_key,
                Body=json.dumps([log_entry], indent=2),
                ContentType='application/json'
            )
        
        print(f"Successfully logged individual rating for puzzle {puzzle_id}")
        return True
    except Exception as e:
        print(f"Error logging individual rating for puzzle {puzzle_id}: {type(e).__name__}: {str(e)}")
        
        # Save to local file as fallback
        try:
            logs_dir = "local_rating_logs"
            os.makedirs(logs_dir, exist_ok=True)
            
            now = datetime.datetime.utcnow()
            log_file = f"{logs_dir}/{now.strftime('%Y-%m-%d-%H')}.json"
            
            # Create the log entry
            log_entry = {
                "log_id": str(uuid.uuid4()),
                "puzzle_id": puzzle_id,
                "target_word": target_word,
                "timestamp": now.isoformat(),
                "session_id": session_id,
                "ratings": {
                    "difficulty": difficulty_rating,
                    "fun": fun_rating
                },
                "metadata": {
                    "time_to_solve": time_to_solve,
                    "hints_used": hints_used,
                    "was_skipped": was_skipped,
                    "platform": "unknown", 
                    "browser": "unknown"  
                }
            }
            
            # Check if file exists
            if os.path.exists(log_file):
                with open(log_file, 'r') as f:
                    try:
                        existing_logs = json.load(f)
                    except:
                        existing_logs = []
                
                existing_logs.append(log_entry)
                
                with open(log_file, 'w') as f:
                    json.dump(existing_logs, f, indent=2)
            else:
                with open(log_file, 'w') as f:
                    json.dump([log_entry], f, indent=2)
                    
            print(f"Saved rating log to local file as fallback")
        except Exception as local_err:
            print(f"Error saving rating log locally: {local_err}")
        
        return False 