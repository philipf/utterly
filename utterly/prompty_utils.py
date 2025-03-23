"""
Utility functions for working with prompty files.
"""

from pathlib import Path
from typing import List, Dict, Any

from langchain_prompty import create_chat_prompt
from langchain_prompty.utils import load
from langchain_prompty.core import Prompty


def get_prompts_directory() -> Path:
    """
    Get the path to the prompts directory.

    Returns:
        Path: Path to the prompts directory
    """
    # Assuming prompts directory is in the same directory as the application
    base_dir = Path(__file__).parent.parent
    return base_dir / "prompts"


def list_prompty_files() -> List[Dict[str, Any]]:
    """
    List all .prompty files in the prompts directory.

    Returns:
        List[Dict[str, Any]]: List of dictionaries with prompty file information
    """
    prompts_dir = get_prompts_directory()
    prompty_files = []

    for file_path in prompts_dir.glob("*.prompty"):
        try:
            # Load the prompty file to get its metadata
            prompty = load_prompty_file(file_path)

            prompty_files.append(
                {
                    "path": file_path,
                    "name": file_path.stem,
                    "description": getattr(prompty, "description", file_path.stem),
                    "prompty": prompty,
                }
            )
        except Exception as e:
            print(f"Error loading prompty file {file_path}: {str(e)}")

    return prompty_files


def load_prompty_file(path: str) -> Prompty:
    """
    Load a prompty file and return its content.

    Args:
        path: Path to the prompty file

    Returns:
        Any: Loaded prompty file
    """
    return load(path)


def create_prompt_from_prompty(path: str):
    """
    Create a chat prompt from a prompty file.

    Args:
        path: Path to the prompty file

    Returns:
        ChatPromptTemplate: Chat prompt template
    """
    return create_chat_prompt(path)
