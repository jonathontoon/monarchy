#!/usr/bin/env python3
"""
Scrape Binairo puzzles from puzzle-binairo.com.

The puzzle grid is encoded as a task string using run-length encoding:
- Digits (0/1) are placed left→right, top→bottom
- Letters (a-z) represent skips, where a=1, b=2, c=3, … z=26
"""

import urllib.request
import re
import sys
import argparse
import json
import os

AVAILABLE_SIZES = [6, 8, 10, 14]
AVAILABLE_DIFFICULTIES = ['easy', 'hard']
BASE_URL = 'https://www.puzzle-binairo.com'


def decode_task(task_str, width, height):
    """
    Decode binairo task string using run-length encoding.

    The grid is scanned left→right, top→bottom (row-major order):
    - Digits (0/1): place value, advance 1 cell
    - Letters (a-z): skip N empty cells, where a=1, b=2, … z=26

    Args:
        task_str: The encoded task string
        width: Grid width
        height: Grid height

    Returns:
        2D list where None represents empty cells, 0/1 are clues

    Raises:
        ValueError: If task string is invalid or doesn't match grid size
    """
    total_cells = width * height
    flat_grid = [None] * total_cells
    pos = 0

    for char in task_str:
        if char in '01':
            if pos >= total_cells:
                raise ValueError(f"Task overruns grid at position {pos}")
            flat_grid[pos] = int(char)
            pos += 1
        elif 'a' <= char <= 'z':
            skip = ord(char) - ord('a') + 1
            pos += skip
            if pos > total_cells:
                raise ValueError(f"Skip overruns grid at position {pos}")
        else:
            raise ValueError(f"Unexpected character in task: '{char}'")

    if pos != total_cells:
        raise ValueError(f"Task ended at position {pos}, expected {total_cells}")

    # Convert flat grid to 2D
    return [flat_grid[r * width:(r + 1) * width] for r in range(height)]


def grid_to_string(grid):
    """Format grid for console display."""
    lines = ["  " + " ".join(chr(ord('A') + i) for i in range(len(grid[0])))]
    for i, row in enumerate(grid, 1):
        cells = " ".join(str(cell) if cell is not None else "." for cell in row)
        lines.append(f"{i} {cells}")
    return "\n".join(lines)


def scrape_binairo(url):
    """
    Scrape a Binairo puzzle from its URL.

    Args:
        url: Full URL to the puzzle page

    Returns:
        dict with keys: size, difficulty, puzzle_id, puzzle (2D grid)
        None if scraping fails
    """
    # Fetch HTML
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            html = response.read().decode('utf-8')
    except Exception as e:
        print(f"Error fetching URL: {e}", file=sys.stderr)
        return None

    # Extract size and difficulty from URL
    match = re.search(r'binairo-(\d+)x(\d+)-(\w+)', url)
    if not match:
        print("Invalid puzzle URL format", file=sys.stderr)
        return None

    size = int(match.group(1))
    difficulty = match.group(3).lower()

    # Extract puzzle ID
    match = re.search(r'Puzzle ID:\s*<span[^>]*>([^<]+)</span>', html)
    puzzle_id = match.group(1).replace(',', '') if match else None

    # Extract and decode task string
    match = re.search(r"task = '([^']+)'", html)
    if not match:
        print("Could not find puzzle data in HTML", file=sys.stderr)
        return None

    try:
        puzzle = decode_task(match.group(1), size, size)
    except ValueError as e:
        print(f"Error decoding puzzle: {e}", file=sys.stderr)
        return None

    return {
        'size': f"{size}x{size}",
        'difficulty': difficulty,
        'puzzle_id': puzzle_id,
        'puzzle': puzzle,
    }


def main():
    """Parse arguments and scrape puzzle."""
    parser = argparse.ArgumentParser(
        description='Scrape Binairo puzzles from puzzle-binairo.com'
    )
    parser.add_argument(
        '--size',
        type=int,
        default=6,
        choices=AVAILABLE_SIZES,
        help=f'Puzzle size (default: 6)',
    )
    parser.add_argument(
        '--difficulty',
        type=str,
        default='easy',
        choices=AVAILABLE_DIFFICULTIES,
        help=f'Puzzle difficulty (default: easy)',
    )
    parser.add_argument(
        '--no-grid',
        action='store_true',
        help='Do not print the puzzle grid',
    )
    parser.add_argument(
        '--list',
        action='store_true',
        help='List available puzzle sizes and difficulties',
    )
    parser.add_argument(
        '--output',
        type=str,
        help='Output file for puzzle JSON',
    )

    args = parser.parse_args()

    # Handle --list
    if args.list:
        print("Available configurations:")
        for size in AVAILABLE_SIZES:
            for diff in AVAILABLE_DIFFICULTIES:
                print(f"  {size}x{size} {diff}")
        return 0

    # Set default output path
    output_path = args.output or f'puzzles/{args.size}x{args.size}.json'

    # Scrape puzzle
    url = f'{BASE_URL}/binairo-{args.size}x{args.size}-{args.difficulty}/'
    puzzle_data = scrape_binairo(url)

    if not puzzle_data:
        return 1

    # Print info
    print(f"Size: {puzzle_data['size']}")
    print(f"Difficulty: {puzzle_data['difficulty']}")
    print(f"Puzzle ID: {puzzle_data['puzzle_id']}")

    if puzzle_data['puzzle'] and not args.no_grid:
        print("\nPuzzle Grid:")
        print(grid_to_string(puzzle_data['puzzle']))

    # Save to file
    os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(puzzle_data, f, indent=2)

    print(f"\nSaved to: {output_path}")
    return 0


if __name__ == '__main__':
    sys.exit(main())
