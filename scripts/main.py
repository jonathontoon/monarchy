#!/usr/bin/env python3
"""
Unified Binairo workflow: scrape → solve → add to file → validate

This script combines all operations into a single streamlined command:
- Scrapes a puzzle from puzzle-binairo.com
- Solves it using human techniques to verify it's solvable
- Adds it to the appropriate size-based puzzle file
- Validates the updated file

Usage:
    python3 scripts/main.py                    # 6x6 easy (default)
    python3 scripts/main.py --size 8 --difficulty hard
    python3 scripts/main.py --count 3          # Multiple puzzles
"""

import sys
import os
import argparse
import time

# Add scripts directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scrape import (
    scrape_binairo, 
    get_next_puzzle_id, 
    get_size_filename, 
    load_or_create_puzzle_file, 
    save_puzzle_file,
    AVAILABLE_SIZES, 
    AVAILABLE_DIFFICULTIES, 
    BASE_URL
)
from solve import BinairoSolver
from validate import PuzzleValidator


def run_workflow(size: int, difficulty: str, puzzles_dir: str = 'puzzles', verbose: bool = False) -> bool:
    """
    Run the complete workflow for a single puzzle.
    
    Args:
        size: Puzzle size (6, 8, 10, 14)
        difficulty: Puzzle difficulty ('easy', 'hard')
        puzzles_dir: Directory to save puzzles
        verbose: Show detailed progress
        
    Returns:
        True if workflow completed successfully, False otherwise
    """
    if verbose:
        print(f"\n=== Starting workflow for {size}x{size} {difficulty} puzzle ===")
    
    # Step 1: Scrape puzzle
    if verbose:
        print("Step 1: Scraping puzzle...")
    
    url = f'{BASE_URL}/binairo-{size}x{size}-{difficulty}/'
    puzzle_data = scrape_binairo(url)
    
    if not puzzle_data:
        print(f"❌ Failed to scrape puzzle from {url}")
        return False
    
    if verbose:
        print(f"✓ Scraped puzzle (Source ID: {puzzle_data.get('puzzle_id', 'N/A')})")
    
    # Print the initial puzzle
    from scrape import grid_to_string
    print("\nInitial puzzle:")
    print(grid_to_string(puzzle_data['puzzle']))
    
    # Step 2: Solve puzzle to verify it's solvable
    if verbose:
        print("Step 2: Verifying puzzle is solvable...")
    
    solver = BinairoSolver(puzzle_data['puzzle'])
    solved, moves_log = solver.solve()
    
    if not solved:
        print(f"❌ Puzzle is not solvable using human techniques")
        return False
    
    if verbose:
        print(f"✓ Puzzle solved successfully ({len(moves_log)} moves)")
        print(f"  Techniques used: {', '.join(sorted(solver.techniques_used))}")
    
    # Print the solved puzzle
    print("\nSolved puzzle:")
    solver.print_grid()
    
    # Step 3: Add to file with proper ID
    if verbose:
        print("Step 3: Adding to puzzle file...")
    
    # Assign internal ID
    puzzle_data['id'] = get_next_puzzle_id(puzzles_dir)
    
    # Load existing puzzles and add new one
    size_filepath = get_size_filename(size, puzzles_dir)
    existing_puzzles = load_or_create_puzzle_file(size_filepath)
    all_puzzles = existing_puzzles + [puzzle_data]
    
    # Save updated file
    try:
        save_puzzle_file(size_filepath, all_puzzles)
        if verbose:
            filename = os.path.basename(size_filepath)
            print(f"✓ Added puzzle (ID {puzzle_data['id']}) to {filename} (total: {len(all_puzzles)})")
    except Exception as e:
        print(f"❌ Failed to save puzzle file: {e}")
        return False
    
    # Step 4: Validate the updated file
    if verbose:
        print("Step 4: Validating updated file...")
    
    validator = PuzzleValidator()
    result = validator.validate_file(size_filepath, strict=False)
    
    if not result['valid']:
        print(f"❌ File validation failed:")
        for error in result['errors']:
            print(f"  ERROR: {error}")
        return False
    
    if verbose:
        print("✓ File validation passed")
        if result['warnings']:
            print("  Warnings:")
            for warning in result['warnings']:
                print(f"    {warning}")
    
    print(f"✅ Workflow completed successfully! Added puzzle ID {puzzle_data['id']} to {os.path.basename(size_filepath)}")
    return True


def run_batch_workflow(sizes: list, difficulties: list, count: int, puzzles_dir: str = 'puzzles', verbose: bool = False) -> int:
    """
    Run workflow for multiple puzzles.
    
    Returns:
        Number of successfully processed puzzles
    """
    total_combinations = len(sizes) * len(difficulties)
    total_puzzles = total_combinations * count
    successful = 0
    
    print(f"Starting batch workflow: {count} puzzle(s) × {len(sizes)} size(s) × {len(difficulties)} difficulty(s) = {total_puzzles} total")
    
    for size in sizes:
        for difficulty in difficulties:
            print(f"\n--- Processing {size}x{size} {difficulty} puzzles ---")
            
            for i in range(count):
                print(f"Processing puzzle {i+1}/{count}...")
                
                success = run_workflow(size, difficulty, puzzles_dir, verbose)
                if success:
                    successful += 1
                else:
                    print(f"Failed to process {size}x{size} {difficulty} puzzle {i+1}")
                
                # Brief pause between requests
                if not (size == sizes[-1] and difficulty == difficulties[-1] and i == count - 1):
                    time.sleep(1)
    
    print(f"\n🎉 Batch workflow complete: {successful}/{total_puzzles} puzzles processed successfully")
    return successful


def main():
    """Parse arguments and run workflow."""
    parser = argparse.ArgumentParser(
        description='Unified Binairo workflow: scrape → solve → add → validate',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 scripts/main.py --count 1                    # 1 puzzle of each size/difficulty
  python3 scripts/main.py --size 8 --difficulty hard --count 1
  python3 scripts/main.py --count 3                    # 3 puzzles of each size/difficulty
  python3 scripts/main.py --size 10 --count 2 --verbose
        """
    )
    
    parser.add_argument(
        '--size',
        type=int,
        choices=AVAILABLE_SIZES,
        help=f'Puzzle size. Available: {AVAILABLE_SIZES}'
    )
    parser.add_argument(
        '--difficulty',
        type=str,
        choices=AVAILABLE_DIFFICULTIES,
        help=f'Puzzle difficulty. Available: {AVAILABLE_DIFFICULTIES}'
    )
    parser.add_argument(
        '--count',
        type=int,
        required=True,
        help='Number of puzzles to process per size/difficulty combination'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default='puzzles',
        help='Directory to save puzzles (default: puzzles)'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Show detailed progress information'
    )
    parser.add_argument(
        '--list',
        action='store_true',
        help='List available puzzle configurations and exit'
    )
    
    args = parser.parse_args()
    
    # Handle --list
    if args.list:
        print("Available configurations:")
        for size in AVAILABLE_SIZES:
            for diff in AVAILABLE_DIFFICULTIES:
                print(f"  {size}x{size} {diff}")
        return 0
    
    # Determine what to process
    sizes = [args.size] if args.size is not None else AVAILABLE_SIZES
    difficulties = [args.difficulty] if args.difficulty is not None else AVAILABLE_DIFFICULTIES
    
    successful = run_batch_workflow(sizes, difficulties, args.count, args.output_dir, args.verbose)
    return 0 if successful > 0 else 1


if __name__ == '__main__':
    sys.exit(main())