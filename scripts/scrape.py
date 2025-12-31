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


def get_next_puzzle_id(puzzles_dir: str = 'puzzles') -> int:
    """
    Determine the next available puzzle ID by scanning existing files.
    
    Returns:
        Next available integer ID
    """
    max_id = 0
    
    if not os.path.exists(puzzles_dir):
        return 1
    
    for filename in os.listdir(puzzles_dir):
        if filename.endswith('.json'):
            try:
                with open(os.path.join(puzzles_dir, filename), 'r') as f:
                    data = json.load(f)
                    if 'id' in data and isinstance(data['id'], int):
                        max_id = max(max_id, data['id'])
            except Exception:
                continue  # Skip files that can't be read or parsed
    
    return max_id + 1


def get_size_filename(size: int, puzzles_dir: str = 'puzzles') -> str:
    """
    Get filename for puzzles of a given size.
    
    Args:
        size: Puzzle size (e.g., 6)
        puzzles_dir: Directory to save puzzles
        
    Returns:
        Filename path for size-specific puzzle collection
    """
    filename = f"{size}x{size}.json"
    return os.path.join(puzzles_dir, filename)


def load_or_create_puzzle_file(filepath: str) -> list:
    """
    Load existing puzzle file or create empty array.
    
    Args:
        filepath: Path to puzzle file
        
    Returns:
        List of existing puzzles (empty if file doesn't exist)
    """
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
                # Handle both old single-object and new array formats
                if isinstance(data, dict):
                    return [data]  # Convert single object to array
                elif isinstance(data, list):
                    return data
                else:
                    print(f"Warning: Unexpected data format in {filepath}, starting fresh")
                    return []
        except Exception as e:
            print(f"Warning: Could not read {filepath}: {e}, starting fresh")
            return []
    else:
        return []


def save_puzzle_file(filepath: str, puzzles: list):
    """
    Save puzzle array to file.
    
    Args:
        filepath: Path to save file
        puzzles: List of puzzle objects
    """
    os.makedirs(os.path.dirname(filepath) or '.', exist_ok=True)
    with open(filepath, 'w') as f:
        json.dump(puzzles, f, indent=2)


def scrape_multiple_puzzles(sizes: list, difficulties: list, count: int, output_dir: str = 'puzzles') -> int:
    """
    Scrape multiple puzzles for given size/difficulty combinations.
    
    Args:
        sizes: List of sizes to scrape
        difficulties: List of difficulties to scrape  
        count: Number of puzzles per combination
        output_dir: Output directory
        
    Returns:
        Number of successfully scraped puzzles
    """
    import time
    
    total_combinations = len(sizes) * len(difficulties)
    total_puzzles = total_combinations * count
    successful = 0
    
    print(f"Starting batch scrape: {count} puzzle(s) × {len(sizes)} size(s) × {len(difficulties)} difficulty(s) = {total_puzzles} total")
    
    # Group scraping by size to append to same file
    for size in sizes:
        size_filepath = get_size_filename(size, output_dir)
        existing_puzzles = load_or_create_puzzle_file(size_filepath)
        new_puzzles = []
        
        print(f"\n--- Scraping {size}x{size} puzzles ---")
        print(f"  Existing puzzles in file: {len(existing_puzzles)}")
        
        for difficulty in difficulties:
            print(f"  Scraping {count} {difficulty} puzzle(s)...")
            
            for i in range(count):
                url = f'{BASE_URL}/binairo-{size}x{size}-{difficulty}/'
                puzzle_data = scrape_binairo(url)
                
                if not puzzle_data:
                    print(f"    Failed to scrape {difficulty} puzzle {i+1}/{count}")
                    continue
                
                # We'll assign IDs later when we save all puzzles
                
                # Add to new puzzles list
                new_puzzles.append(puzzle_data)
                successful += 1
                print(f"    {difficulty} {i+1}/{count}: scraped")
                
                # Brief pause to be respectful to the server
                if not (difficulty == difficulties[-1] and i == count - 1):  # Don't sleep after last puzzle
                    time.sleep(1)
        
        # Assign IDs and save all puzzles for this size
        if new_puzzles:
            # Assign sequential IDs starting from next available
            next_id = get_next_puzzle_id(output_dir)
            for j, puzzle in enumerate(new_puzzles):
                puzzle['id'] = next_id + j
                
            all_puzzles = existing_puzzles + new_puzzles
            try:
                save_puzzle_file(size_filepath, all_puzzles)
                filename = os.path.basename(size_filepath)
                id_range = f"{next_id}-{next_id + len(new_puzzles) - 1}" if len(new_puzzles) > 1 else str(next_id)
                print(f"  Saved {len(new_puzzles)} new puzzles (IDs {id_range}) to {filename} (total: {len(all_puzzles)})")
            except Exception as e:
                print(f"  Failed to save {filename}: {e}")
                successful -= len(new_puzzles)  # Rollback success count
    
    print(f"\nBatch complete: {successful}/{total_puzzles} puzzles scraped successfully")
    return successful


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
        choices=AVAILABLE_SIZES,
        help=f'Puzzle size (if not specified with --count>1, scrapes all sizes)',
    )
    parser.add_argument(
        '--difficulty',
        type=str,
        choices=AVAILABLE_DIFFICULTIES,
        help=f'Puzzle difficulty (if not specified with --count>1, scrapes all difficulties)',
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
        help='Output file for puzzle JSON (only for single puzzle)',
    )
    parser.add_argument(
        '--count',
        type=int,
        default=1,
        help='Number of puzzles to scrape per size/difficulty combination (default: 1)',
    )

    args = parser.parse_args()

    # Handle --list
    if args.list:
        print("Available configurations:")
        for size in AVAILABLE_SIZES:
            for diff in AVAILABLE_DIFFICULTIES:
                print(f"  {size}x{size} {diff}")
        return 0

    # Determine mode: batch (multiple puzzles) vs single puzzle
    is_batch_mode = (args.count > 1) or (args.size is None and args.difficulty is None and args.count == 1)
    
    if is_batch_mode:
        # Batch mode: scrape multiple combinations
        sizes = [args.size] if args.size is not None else AVAILABLE_SIZES
        difficulties = [args.difficulty] if args.difficulty is not None else AVAILABLE_DIFFICULTIES
        
        if args.output:
            print("Warning: --output ignored in batch mode (auto-generating filenames)")
        
        successful = scrape_multiple_puzzles(sizes, difficulties, args.count)
        return 0 if successful > 0 else 1
    
    else:
        # Single puzzle mode (original behavior)
        # Use defaults if not specified
        size = args.size if args.size is not None else 6
        difficulty = args.difficulty if args.difficulty is not None else 'easy'
        
        # Scrape puzzle
        url = f'{BASE_URL}/binairo-{size}x{size}-{difficulty}/'
        puzzle_data = scrape_binairo(url)

        if not puzzle_data:
            return 1

        # Assign internal ID
        puzzle_data['id'] = get_next_puzzle_id()

        # Print info
        print(f"ID: {puzzle_data['id']}")
        print(f"Size: {puzzle_data['size']}")
        print(f"Difficulty: {puzzle_data['difficulty']}")
        print(f"Source ID: {puzzle_data['puzzle_id']}")

        if puzzle_data['puzzle'] and not args.no_grid:
            print("\nPuzzle Grid:")
            print(grid_to_string(puzzle_data['puzzle']))

        # Save to appropriate size file (or custom output)
        if args.output:
            # Custom single file output
            with open(args.output, 'w') as f:
                json.dump(puzzle_data, f, indent=2)
            print(f"\nSaved to: {args.output}")
        else:
            # Add to size-based collection
            size_filepath = get_size_filename(size)
            existing_puzzles = load_or_create_puzzle_file(size_filepath)
            all_puzzles = existing_puzzles + [puzzle_data]
            
            save_puzzle_file(size_filepath, all_puzzles)
            filename = os.path.basename(size_filepath)
            print(f"\nAdded to {filename} (total puzzles: {len(all_puzzles)})")

        return 0


if __name__ == '__main__':
    sys.exit(main())
