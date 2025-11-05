"""
File renamer module for Telegram chat analyzer.
Renames input files to include chat name and date range.
"""

import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Tuple, Optional


class FileRenamer:
    """Handles renaming of Telegram chat export files with meaningful names."""
    
    def __init__(self, input_dir: str = "data/input"):
        """Initialize the file renamer.
        
        Args:
            input_dir: Directory containing input files
        """
        self.input_dir = Path(input_dir)
    
    def extract_chat_info(self, file_path: Path) -> Tuple[str, str, str]:
        """Extract chat name and date range from a Telegram export file.
        
        Args:
            file_path: Path to the JSON file
            
        Returns:
            Tuple of (chat_name, start_date, end_date)
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            chat_name = data.get('name', 'Unknown Chat')
            messages = data.get('messages', [])
            
            if not messages:
                return chat_name, "unknown", "unknown"
            
            # Get first and last message dates
            first_date = messages[0].get('date', '')
            last_date = messages[-1].get('date', '')
            
            return chat_name, first_date, last_date
            
        except Exception as e:
            print(f"Error reading file {file_path}: {e}")
            return "Unknown Chat", "unknown", "unknown"
    
    def format_filename(self, chat_name: str, start_date: str, end_date: str) -> str:
        """Format the filename with chat name and date range.
        
        Args:
            chat_name: Name of the chat
            start_date: Start date of the chat
            end_date: End date of the chat
            
        Returns:
            Formatted filename
        """
        # Clean chat name for filename
        clean_name = re.sub(r'[^\w\s-]', '', chat_name)
        clean_name = re.sub(r'[-\s]+', '_', clean_name)
        
        # Format dates
        def format_date(date_str: str) -> str:
            if date_str == "unknown":
                return "unknown"
            try:
                # Parse ISO format date
                dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                return dt.strftime('%Y%m%d')
            except:
                return "unknown"
        
        start_formatted = format_date(start_date)
        end_formatted = format_date(end_date)
        
        if start_formatted == "unknown" or end_formatted == "unknown":
            return f"{clean_name}.json"
        elif start_formatted == end_formatted:
            return f"{clean_name}_{start_formatted}.json"
        else:
            return f"{clean_name}_{start_formatted}-{end_formatted}.json"
    
    def rename_file(self, filename: str = "result.json") -> Optional[str]:
        """Rename a file in the input directory.
        
        Args:
            filename: Name of the file to rename
            
        Returns:
            New filename if successful, None if failed
        """
        file_path = self.input_dir / filename
        
        if not file_path.exists():
            print(f"File {file_path} not found")
            return None
        
        # Extract chat information
        chat_name, start_date, end_date = self.extract_chat_info(file_path)
        
        # Generate new filename
        new_filename = self.format_filename(chat_name, start_date, end_date)
        new_file_path = self.input_dir / new_filename
        
        # Check if target file already exists
        if new_file_path.exists():
            print(f"Target file {new_filename} already exists")
            return None
        
        try:
            # Rename the file
            file_path.rename(new_file_path)
            print(f"Renamed {filename} to {new_filename}")
            print(f"Chat: {chat_name}")
            print(f"Date range: {start_date} to {end_date}")
            return new_filename
            
        except Exception as e:
            print(f"Error renaming file: {e}")
            return None
    
    def rename_all_files(self) -> list:
        """Rename all JSON files in the input directory.
        
        Returns:
            List of new filenames
        """
        renamed_files = []
        
        for file_path in self.input_dir.glob("*.json"):
            if file_path.name != "result.json":  # Skip already renamed files
                continue
                
            new_filename = self.rename_file(file_path.name)
            if new_filename:
                renamed_files.append(new_filename)
        
        return renamed_files


def main():
    """Main function for command line usage."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Rename Telegram chat export files")
    parser.add_argument("--input-dir", default="data/input", 
                       help="Input directory containing files to rename")
    parser.add_argument("--file", default="result.json",
                       help="Specific file to rename")
    parser.add_argument("--all", action="store_true",
                       help="Rename all JSON files in input directory")
    
    args = parser.parse_args()
    
    renamer = FileRenamer(args.input_dir)
    
    if args.all:
        renamed_files = renamer.rename_all_files()
        print(f"Renamed {len(renamed_files)} files: {renamed_files}")
    else:
        new_filename = renamer.rename_file(args.file)
        if new_filename:
            print(f"Successfully renamed to: {new_filename}")
        else:
            print("Failed to rename file")


if __name__ == "__main__":
    main()
