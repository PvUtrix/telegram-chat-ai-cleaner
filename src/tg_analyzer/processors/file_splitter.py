"""
File splitting utility for large output files
"""

import logging
from pathlib import Path
from typing import List, Optional, Tuple

logger = logging.getLogger(__name__)

# 1MB in bytes
MB_SIZE = 1024 * 1024


def split_file_if_needed(
    file_path: str,
    content: str,
    max_size: int = MB_SIZE,
    interactive: bool = True,
    prompt_callback: Optional[callable] = None
) -> Tuple[bool, List[str]]:
    """
    Check if a file is over max_size and optionally split it into multiple files.
    
    Args:
        file_path: Path to the file to check/split
        content: Content to write to the file
        max_size: Maximum file size in bytes (default: 1MB)
        interactive: Whether to prompt user if file is too large
        prompt_callback: Optional callback function to prompt user. 
                        Should return True to split, False to keep as is.
                        If None, defaults to asking via console.
    
    Returns:
        Tuple of (was_split: bool, file_paths: List[str])
        - was_split: True if file was split, False if kept as single file
        - file_paths: List of file paths (original or split files)
    """
    content_size = len(content.encode('utf-8'))
    
    # If file is not too large, write normally
    if content_size <= max_size:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return False, [file_path]
    
    # File is too large
    if interactive:
        should_split = _prompt_for_split(file_path, content_size, prompt_callback)
        if not should_split:
            # User chose to keep as single file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return False, [file_path]
    
    # Split the file
    return True, _split_file_content(file_path, content, max_size)


def _prompt_for_split(
    file_path: str,
    content_size: int,
    prompt_callback: Optional[callable] = None
) -> bool:
    """
    Prompt user whether to split the file.
    
    Args:
        file_path: Path to the file
        content_size: Size of content in bytes
        prompt_callback: Optional callback to prompt user
    
    Returns:
        True if user wants to split, False otherwise
    """
    if prompt_callback:
        return prompt_callback(file_path, content_size)
    
    # Default: ask via console (for CLI)
    try:
        import click
        from rich.console import Console
        
        console = Console()
        size_mb = content_size / MB_SIZE
        
        console.print(f"\n[yellow]⚠️  File size warning:[/yellow]")
        console.print(f"  Output file would be {size_mb:.2f} MB (over 1 MB limit)")
        console.print(f"  File: {Path(file_path).name}")
        console.print()
        
        return click.confirm("Split file into multiple 1MB files?", default=True)
    except ImportError:
        # Fallback: always split if no interactive prompt available
        logger.warning(f"File {file_path} is {content_size} bytes (over 1MB), splitting automatically")
        return True


def _split_file_content(file_path: str, content: str, max_size: int) -> List[str]:
    """
    Split file content into multiple files, each under max_size.
    
    Args:
        file_path: Original file path
        content: Content to split
        max_size: Maximum size per file in bytes
    
    Returns:
        List of file paths for split files
    """
    file_path_obj = Path(file_path)
    base_name = file_path_obj.stem
    extension = file_path_obj.suffix
    directory = file_path_obj.parent
    
    # Split content into chunks
    chunks = _split_text_by_size(content, max_size)
    
    # Create split files
    split_files = []
    for i, chunk in enumerate(chunks, 1):
        if len(chunks) == 1:
            # Only one chunk (shouldn't happen if content is truly over max_size, but handle it)
            # Use original filename since we're not actually splitting
            split_file = file_path
        else:
            # Multiple chunks, add part number
            split_file = directory / f"{base_name}_part{i:03d}{extension}"
        
        with open(split_file, 'w', encoding='utf-8') as f:
            f.write(chunk)
        
        split_files.append(str(split_file))
        chunk_size_mb = len(chunk.encode('utf-8')) / MB_SIZE
        logger.info(f"Created split file: {split_file} ({chunk_size_mb:.2f} MB)")
    
    return split_files


def _split_text_by_size(text: str, max_size: int) -> List[str]:
    """
    Split text into chunks, each under max_size bytes.
    Attempts to split at line boundaries to avoid breaking content.
    
    Args:
        text: Text to split
        max_size: Maximum size per chunk in bytes
    
    Returns:
        List of text chunks
    """
    chunks = []
    current_chunk = []
    current_size = 0
    
    lines = text.split('\n')
    
    for line in lines:
        line_bytes = (line + '\n').encode('utf-8')
        line_size = len(line_bytes)
        
        # If single line is larger than max_size, split it
        if line_size > max_size:
            # Save current chunk if it has content
            if current_chunk:
                chunks.append('\n'.join(current_chunk))
                current_chunk = []
                current_size = 0
            
            # Split the large line into smaller pieces
            large_line_chunks = _split_large_line(line, max_size)
            chunks.extend(large_line_chunks)
            continue
        
        # Check if adding this line would exceed max_size
        if current_size + line_size > max_size and current_chunk:
            # Save current chunk
            chunks.append('\n'.join(current_chunk))
            current_chunk = [line]
            current_size = line_size
        else:
            # Add line to current chunk
            current_chunk.append(line)
            current_size += line_size
    
    # Add remaining chunk
    if current_chunk:
        chunks.append('\n'.join(current_chunk))
    
    return chunks if chunks else ['']  # Return at least one empty chunk


def _split_large_line(line: str, max_size: int) -> List[str]:
    """
    Split a single line that exceeds max_size into multiple chunks.
    
    Args:
        line: Line to split
        max_size: Maximum size per chunk in bytes
    
    Returns:
        List of line chunks
    """
    chunks = []
    remaining = line
    
    while remaining:
        # Try to find a good break point (space or punctuation)
        chunk_bytes = remaining.encode('utf-8')[:max_size]
        
        # If remaining fits in one chunk, use it all
        if len(remaining.encode('utf-8')) <= max_size:
            chunks.append(remaining)
            break
        
        # Try to find a good break point
        chunk_text = chunk_bytes.decode('utf-8', errors='ignore')
        
        # Look for last space or punctuation
        break_point = max(
            chunk_text.rfind(' '),
            chunk_text.rfind(','),
            chunk_text.rfind('.'),
            chunk_text.rfind(';'),
            chunk_text.rfind(':'),
            max_size // 2  # Fallback: at least half way
        )
        
        if break_point > max_size // 2:
            # Found a good break point
            chunk = remaining[:break_point + 1]
            remaining = remaining[break_point + 1:]
        else:
            # No good break point, split at max_size
            chunk = remaining[:max_size]
            remaining = remaining[max_size:]
        
        chunks.append(chunk)
    
    return chunks

