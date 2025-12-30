#!/usr/bin/env python3
"""
Scrape Binairo puzzle from puzzle-binairo.com
Extracts: size, difficulty, puzzle ID, and puzzle grid
"""

import urllib.request
import re
import sys
import base64
import argparse
import json
import os
from html.parser import HTMLParser

# Available puzzle sizes and difficulties
AVAILABLE_SIZES = [6, 8, 10, 14]
AVAILABLE_DIFFICULTIES = ['easy', 'hard']





def decode_task(task_str, size):
    """
    Decode the task string from puzzle-binairo into a grid.
    Task format: numbers (0 or 1) followed by column letters indicating runs.
    e.g., '0b11h11e0b0a1h00' means:
    - 0 in column a, then switch to column b (letter indicates column change)
    - 11 in column b, then switch to column h
    - etc.
    
    Args:
        task_str: The encoded task string
        size: Grid size (e.g., 6 for 6x6)
        
    Returns:
        2D list representing the puzzle grid (None for empty cells)
    """
    # Initialize empty grid
    grid = [[None for _ in range(size)] for _ in range(size)]
    
    # Parse the task string
    col_order = 'abcdefghijklmnopqrst'[:size]
    current_col_idx = 0
    row_counts = [0] * size
    
    i = 0
    while i < len(task_str):
        char = task_str[i]
        
        # Check if it's a column letter
        if char in col_order:
            current_col_idx = ord(char) - ord('a')
        # Check if it's a digit (0 or 1)
        elif char in '01':
            value = int(char)
            row = row_counts[current_col_idx]
            if row < size:
                grid[row][current_col_idx] = value
                row_counts[current_col_idx] += 1
        
        i += 1
    
    return grid


def grid_to_string(grid):
    """
    Convert a grid to a readable string representation.
    """
    result = []
    result.append("  " + " ".join(chr(ord('A') + i) for i in range(len(grid[0]))))
    for i, row in enumerate(grid):
        row_str = str(i + 1) + " "
        row_str += " ".join(str(cell) if cell is not None else "." for cell in row)
        result.append(row_str)
    return "\n".join(result)


def scrape_binairo(url):
    """
    Scrape puzzle information and data from a Binairo puzzle page.
    
    Args:
        url: The URL of the puzzle page
        
    Returns:
        dict: Contains 'size', 'difficulty', 'puzzle_id', and 'puzzle' (grid)
    """
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            html_content = response.read().decode('utf-8')
    except Exception as e:
        print(f"Error fetching URL: {e}", file=sys.stderr)
        return None
    
    # Extract puzzle info from text content
    match = re.search(r'(\d+)x(\d+)\s+(\w+)\s+Binairo.*?Puzzle\s+ID:\s*<span[^>]*>([^<]+)</span>', html_content, re.DOTALL)
    
    if not match:
        print("Could not find puzzle information on page", file=sys.stderr)
        return None
    
    width, height, difficulty, puzzle_id = match.groups()
    width, height = int(width), int(height)
    puzzle_id = puzzle_id.replace(',', '')
    
    # Extract task string (puzzle encoding)
    task_match = re.search(r"task = '([^']+)'", html_content)
    puzzle_grid = None
    if task_match:
        task_str = task_match.group(1)
        puzzle_grid = decode_task(task_str, width)
    
    return {
        'size': f"{width}x{height}",
        'difficulty': difficulty.lower(),
        'puzzle_id': puzzle_id,
        'puzzle': puzzle_grid
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Scrape Binairo puzzles from puzzle-binairo.com')
    parser.add_argument(
        '--size',
        type=int,
        default=6,
        choices=AVAILABLE_SIZES,
        help=f'Puzzle size (default: 6). Available: {AVAILABLE_SIZES}'
    )
    parser.add_argument(
        '--difficulty',
        type=str,
        default='easy',
        choices=AVAILABLE_DIFFICULTIES,
        help=f'Puzzle difficulty (default: easy). Available: {AVAILABLE_DIFFICULTIES}'
    )
    parser.add_argument(
        '--no-grid',
        action='store_true',
        help='Do not print the puzzle grid'
    )
    parser.add_argument(
        '--list',
        action='store_true',
        help='List all available puzzle sizes and difficulties'
    )
    parser.add_argument(
        '--output',
        type=str,
        default=None,
        help='Output file path for puzzle JSON (default: /puzzles/{size}x{size}.json)'
    )
    
    args = parser.parse_args()
    
    if args.list:
        print("Available puzzle configurations:")
        for size in AVAILABLE_SIZES:
            for diff in AVAILABLE_DIFFICULTIES:
                print(f"  {size}x{size} - {diff}")
        sys.exit(0)
    
    # Set default output path based on size if not specified
    if not args.output:
        args.output = f'/puzzles/{args.size}x{args.size}.json'
    
    url = f'https://www.puzzle-binairo.com/binairo-{args.size}x{args.size}-{args.difficulty}/'
    
    puzzle_data = scrape_binairo(url)
    
    if puzzle_data:
        print(f"Size: {puzzle_data['size']}")
        print(f"Difficulty: {puzzle_data['difficulty']}")
        print(f"Puzzle ID: {puzzle_data['puzzle_id']}")
        
        # Display grid if available
        if puzzle_data['puzzle'] and not args.no_grid:
            print("\nPuzzle Grid:")
            print(grid_to_string(puzzle_data['puzzle']))
        
        # Save to file
        if args.output:
            output_dir = os.path.dirname(args.output)
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
            
            with open(args.output, 'w') as f:
                json.dump({
                    'size': puzzle_data['size'],
                    'difficulty': puzzle_data['difficulty'],
                    'puzzle_id': puzzle_data['puzzle_id'],
                    'puzzle': puzzle_data['puzzle']
                }, f, indent=2)
            
            print(f"Saved to: {args.output}")
    else:
        sys.exit(1)
