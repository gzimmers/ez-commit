"""
Core functionality for ez-commit
"""

import git
from openai import OpenAI
from . import config

def get_git_diff() -> str:
    """Get the current git diff."""
    try:
        repo = git.Repo(search_parent_directories=True)
        
        # Get staged changes first
        staged_diff = repo.git.diff('--cached', '--text')  # Force text output
        
        # If nothing is staged, get unstaged changes
        if not staged_diff:
            diff = repo.git.diff('--text')  # Force text output
            if not diff:
                raise ValueError("No changes detected (staged or unstaged)")
            return diff
        
        return staged_diff
    
    except git.InvalidGitRepositoryError:
        raise ValueError("Not a git repository")
    except git.GitCommandError as e:
        if "binary files differ" in str(e).lower():
            raise ValueError("Binary files detected in diff. Please stage only text files.")
        raise ValueError(f"Git error: {str(e)}")

# Create a single OpenAI client instance
_openai_client = None

def get_openai_client() -> OpenAI:
    """Get or create OpenAI client instance."""
    global _openai_client
    if _openai_client is None:
        _openai_client = OpenAI(api_key=config.get_openai_api_key())
    return _openai_client

def create_commit_prompt(diff: str, system_prompt: str, additional_messages: list = None) -> list:
    """Create the messages list for the OpenAI API call."""
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Generate a commit message for the following git diff:\n\n{diff}"}
    ]
    
    if additional_messages:
        messages.extend(additional_messages)
    
    return messages

def generate_commit_message(diff: str = None, additional_messages: list = None) -> str:
    """Generate a commit message using OpenAI API."""
    if diff is None:
        diff = get_git_diff()
    
    cfg = config.validate_config()
    client = get_openai_client()
    
    messages = create_commit_prompt(diff, cfg["system_prompt"], additional_messages)
    
    try:
        response = client.chat.completions.create(
            model=cfg["openai"]["model"],
            messages=messages,
            temperature=cfg["openai"]["temperature"],
            max_tokens=cfg["openai"]["max_tokens"]
        )
        
        commit_message = response.choices[0].message.content.strip()
        if not commit_message:
            raise ValueError("Generated commit message is empty")
        
        return commit_message
    
    except Exception as e:
        raise ValueError(f"OpenAI API error: {str(e)}")

def commit_changes(message: str):
    """Commit changes with the generated message."""
    if not message or not message.strip():
        raise ValueError("Commit message cannot be empty")
        
    try:
        repo = git.Repo(search_parent_directories=True)
        
        # If nothing is staged, stage all changes
        if not repo.git.diff('--cached'):
            repo.git.add('.')
        
        # Validate that we have changes to commit
        if not repo.git.diff('--cached'):
            raise ValueError("No changes staged for commit")
            
        repo.index.commit(message)
        return True
    
    except git.InvalidGitRepositoryError:
        raise ValueError("Not a git repository")
    except git.GitCommandError as e:
        raise ValueError(f"Git error: {str(e)}")
