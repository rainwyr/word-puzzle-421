import boto3
import json
import random
import os
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
        
        return puzzle_ids
    except Exception as e:
        print(f"Error getting puzzle IDs: {e}")
        return []

def get_random_puzzle() -> Optional[Dict[str, Any]]:
    """
    Get a random puzzle from the S3 bucket.
    
    Returns:
        Dict[str, Any]: A puzzle dictionary with images and descriptions
    """
    puzzle_ids = get_puzzle_ids()
    if not puzzle_ids:
        return None
    
    # Select a random puzzle ID
    random_id = random.choice(puzzle_ids)
    return get_puzzle_by_id(random_id)

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
        print(f"Error validating answer for puzzle {puzzle_id}: {e}")
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
        # Get the solution JSON file
        response = s3_client.get_object(
            Bucket=S3_BUCKET_NAME,
            Key=f'solutions_by_id/{puzzle_id}.json'
        )
        
        # Parse the JSON
        solution_data = json.loads(response['Body'].read().decode('utf-8'))
        
        return solution_data.get('target_word', '')
    except Exception as e:
        print(f"Error getting solution for puzzle {puzzle_id}: {e}")
        return None

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