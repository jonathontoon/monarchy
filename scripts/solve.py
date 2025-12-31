#!/usr/bin/env python3
"""
Solve Binairo puzzles using constraint satisfaction and backtracking.

This solver uses a reliable algorithmic approach:
- Constraint satisfaction with backtracking
- Solution uniqueness verification
- Fast constraint checking
- No human-logic complexity

Guarantees finding the unique solution if one exists.
"""

import json
import sys
import argparse
import copy
import time
from typing import List, Optional, Tuple


class SolverMetrics:
    """Track performance metrics during solving."""
    
    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.constraint_propagation_time = 0.0
        self.backtracking_time = 0.0
        self.backtrack_attempts = 0
        self.forced_moves_found = 0
        self.constraint_checks = 0
        self.cell_placements = 0
        
    def start_solving(self):
        """Mark start of solving process."""
        self.start_time = time.perf_counter()
    
    def end_solving(self):
        """Mark end of solving process."""
        self.end_time = time.perf_counter()
    
    def get_total_time(self) -> float:
        """Get total solving time in seconds."""
        if self.start_time is None or self.end_time is None:
            return 0.0
        return self.end_time - self.start_time
    
    def format_summary(self) -> str:
        """Format brief summary for always-visible display."""
        total_time = self.get_total_time()
        return f"Solved in {total_time:.3f}s with {self.backtrack_attempts:,} backtracking attempts"
    
    def format_metrics(self) -> str:
        """Format detailed metrics for verbose display."""
        total_time = self.get_total_time()
        lines = [
            f"Total solving time: {total_time:.3f}s",
            f"├─ Constraint propagation: {self.constraint_propagation_time:.3f}s ({self.constraint_propagation_time/total_time*100:.1f}%)",
            f"└─ Backtracking: {self.backtracking_time:.3f}s ({self.backtracking_time/total_time*100:.1f}%)",
            f"Backtracking attempts: {self.backtrack_attempts:,}",
            f"Forced moves found: {self.forced_moves_found}",
            f"Constraint checks: {self.constraint_checks:,}",
            f"Cell placements: {self.cell_placements}"
        ]
        return "\n".join(lines)


class BinairoSolver:
    def __init__(self, puzzle: List[List[Optional[int]]]):
        self.grid = copy.deepcopy(puzzle)
        self.size = len(puzzle)
        self.half_size = self.size // 2
        self.moves_log = []
        self.techniques_used = {"Algorithmic"}  # For compatibility with main.py
        self.metrics = SolverMetrics()
        
    def solve(self, verbose: bool = False) -> Tuple[bool, List[str]]:
        """
        Solve the puzzle using constraint satisfaction and backtracking.
        
        Args:
            verbose: Show detailed solving process (steps, metrics, techniques)
        
        Returns:
            (solved, moves_log)
        """
        self.metrics.start_solving()
        
        if verbose:
            print("Starting algorithmic solver...")
            self.print_grid()
        
        # Find empty cells
        empty_cells = []
        for r in range(self.size):
            for c in range(self.size):
                if self.grid[r][c] is None:
                    empty_cells.append((r, c))
        
        if not empty_cells:
            # Already complete - check if valid
            solved = self.is_valid()
            return solved, self.moves_log
        
        if verbose:
            print(f"Found {len(empty_cells)} empty cells to fill")
        
        # Apply initial constraint propagation
        propagation_start = time.perf_counter()
        progress = True
        while progress:
            progress = False
            if self._apply_forced_moves(verbose):
                progress = True
                # Update empty cells list
                empty_cells = [(r, c) for r, c in empty_cells if self.grid[r][c] is None]
        
        self.metrics.constraint_propagation_time += time.perf_counter() - propagation_start
        
        if not empty_cells:
            # Solved by constraint propagation alone
            self.metrics.end_solving()
            solved = self.is_valid()
            if verbose:
                print(f"\nPerformance Metrics:")
                print(self.metrics.format_metrics())
            return solved, self.moves_log
        
        # Sort empty cells by constraint level (most constrained first)
        empty_cells = self._sort_by_constraints(empty_cells)
        
        if verbose:
            print(f"Applying backtracking to {len(empty_cells)} remaining cells")
        
        # Apply backtracking
        original_grid = copy.deepcopy(self.grid)
        backtrack_start = time.perf_counter()
        solved = self._backtrack(empty_cells, 0, verbose)
        self.metrics.backtracking_time += time.perf_counter() - backtrack_start
        
        self.metrics.end_solving()
        
        if solved and self.is_valid():
            if verbose:
                print(f"\nPerformance Metrics:")
                print(self.metrics.format_metrics())
            return True, self.moves_log
        else:
            self.grid = original_grid
            if verbose:
                print(f"\nPerformance Metrics (failed attempt):")
                print(self.metrics.format_metrics())
            return False, self.moves_log
    
    def _apply_forced_moves(self, verbose: bool = False) -> bool:
        """Apply constraint propagation to find forced moves."""
        progress = False
        
        for r in range(self.size):
            for c in range(self.size):
                if self.grid[r][c] is not None:
                    continue
                
                valid_values = []
                for val in [0, 1]:
                    if self._is_valid_placement(r, c, val):
                        valid_values.append(val)
                
                if len(valid_values) == 1:
                    # Forced move
                    val = valid_values[0]
                    self.grid[r][c] = val
                    self.moves_log.append(f"Set ({chr(65+c)},{r+1}) = {val} [Forced by constraints]")
                    self.metrics.forced_moves_found += 1
                    self.metrics.cell_placements += 1
                    if verbose:
                        print(f"  Forced: ({chr(65+c)},{r+1}) = {val}")
                    progress = True
                elif len(valid_values) == 0:
                    # Invalid state - no valid values
                    return False
        
        return progress
    
    def _sort_by_constraints(self, empty_cells: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
        """Sort empty cells by constraint level (most constrained first)."""
        def constraint_count(cell):
            r, c = cell
            valid_count = 0
            for val in [0, 1]:
                if self._is_valid_placement(r, c, val):
                    valid_count += 1
            return valid_count
        
        return sorted(empty_cells, key=constraint_count)
    
    def _backtrack(self, empty_cells: List[Tuple[int, int]], index: int, verbose: bool = False) -> bool:
        """Recursive backtracking solver."""
        self.metrics.backtrack_attempts += 1
        
        if index >= len(empty_cells):
            # All cells filled - check validity
            return self.is_valid()
        
        r, c = empty_cells[index]
        
        # Try both values
        for val in [0, 1]:
            if self._is_valid_placement(r, c, val):
                # Place value
                self.grid[r][c] = val
                self.moves_log.append(f"Set ({chr(65+c)},{r+1}) = {val} [Backtrack {index+1}/{len(empty_cells)}]")
                self.metrics.cell_placements += 1
                
                if verbose and index < 10:  # Limit output for deep recursion
                    print(f"    Try: ({chr(65+c)},{r+1}) = {val}")
                
                # Recurse
                if self._backtrack(empty_cells, index + 1, verbose):
                    return True
                
                # Backtrack
                self.grid[r][c] = None
                if self.moves_log and self.moves_log[-1].startswith(f"Set ({chr(65+c)},{r+1}) = {val}"):
                    self.moves_log.pop()
                
                if verbose and index < 10:
                    print(f"    Backtrack: ({chr(65+c)},{r+1})")
        
        return False
    
    def _is_valid_placement(self, r: int, c: int, value: int) -> bool:
        """Check if placing a value at position (r,c) is valid."""
        self.metrics.constraint_checks += 1
        
        # Temporarily place the value
        original = self.grid[r][c]
        self.grid[r][c] = value
        
        valid = True
        
        # Check no three consecutive in row
        if valid:
            for start_c in range(max(0, c-2), min(self.size-2, c+1)):
                if (self.grid[r][start_c] is not None and 
                    self.grid[r][start_c] == self.grid[r][start_c+1] == self.grid[r][start_c+2]):
                    valid = False
                    break
        
        # Check no three consecutive in column
        if valid:
            for start_r in range(max(0, r-2), min(self.size-2, r+1)):
                if (self.grid[start_r][c] is not None and 
                    self.grid[start_r][c] == self.grid[start_r+1][c] == self.grid[start_r+2][c]):
                    valid = False
                    break
        
        # Check balance doesn't exceed half
        if valid:
            row_count = sum(1 for col in range(self.size) if self.grid[r][col] == value)
            col_count = sum(1 for row in range(self.size) if self.grid[row][c] == value)
            
            if row_count > self.half_size or col_count > self.half_size:
                valid = False
        
        # Restore original value
        self.grid[r][c] = original
        return valid
    
    def is_complete(self) -> bool:
        """Check if puzzle is completely filled."""
        for r in range(self.size):
            for c in range(self.size):
                if self.grid[r][c] is None:
                    return False
        return True
    
    def is_valid(self) -> bool:
        """Check if current state is valid and complete."""
        if not self.is_complete():
            return False
        
        # Check rows
        for r in range(self.size):
            row = self.grid[r]
            if row.count(0) != self.half_size or row.count(1) != self.half_size:
                return False
            
            # Check no three consecutive
            for c in range(self.size - 2):
                if row[c] == row[c+1] == row[c+2]:
                    return False
        
        # Check columns
        for c in range(self.size):
            col = [self.grid[r][c] for r in range(self.size)]
            if col.count(0) != self.half_size or col.count(1) != self.half_size:
                return False
            
            # Check no three consecutive
            for r in range(self.size - 2):
                if col[r] == col[r+1] == col[r+2]:
                    return False
        
        # Check no duplicate rows
        for r1 in range(self.size):
            for r2 in range(r1 + 1, self.size):
                if self.grid[r1] == self.grid[r2]:
                    return False
        
        # Check no duplicate columns
        for c1 in range(self.size):
            for c2 in range(c1 + 1, self.size):
                col1 = [self.grid[r][c1] for r in range(self.size)]
                col2 = [self.grid[r][c2] for r in range(self.size)]
                if col1 == col2:
                    return False
        
        return True
    
    def count_solutions(self, max_count: int = 2) -> int:
        """Count the number of solutions. Returns 0, 1, or max_count."""
        empty_cells = []
        for r in range(self.size):
            for c in range(self.size):
                if self.grid[r][c] is None:
                    empty_cells.append((r, c))
        
        if not empty_cells:
            return 1 if self.is_valid() else 0
        
        # Sort by constraints for efficiency
        empty_cells = self._sort_by_constraints(empty_cells)
        
        original_grid = copy.deepcopy(self.grid)
        solutions = self._count_solutions_recursive(empty_cells, 0, max_count)
        self.grid = original_grid
        
        return solutions
    
    def _count_solutions_recursive(self, empty_cells: List[Tuple[int, int]], index: int, max_count: int) -> int:
        """Recursive solution counter."""
        if index >= len(empty_cells):
            return 1 if self.is_valid() else 0
        
        r, c = empty_cells[index]
        solution_count = 0
        
        for val in [0, 1]:
            if self._is_valid_placement(r, c, val):
                self.grid[r][c] = val
                
                count = self._count_solutions_recursive(empty_cells, index + 1, max_count)
                solution_count += count
                
                # Early termination if we've found enough solutions
                if solution_count >= max_count:
                    self.grid[r][c] = None
                    return max_count
                
                self.grid[r][c] = None
        
        return solution_count
    
    def print_grid(self):
        """Print current grid state."""
        print("  " + " ".join(chr(ord('A') + i) for i in range(self.size)))
        for i, row in enumerate(self.grid, 1):
            cells = " ".join(str(cell) if cell is not None else "." for cell in row)
            print(f"{i} {cells}")


def load_puzzles(file_path: str) -> list:
    """Load puzzle(s) from JSON file. Handles both single objects and arrays."""
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
            # Handle both old single-object and new array formats
            if isinstance(data, dict):
                return [data]  # Convert single object to array
            elif isinstance(data, list):
                return data
            else:
                print(f"Error: Unexpected data format in {file_path}", file=sys.stderr)
                return []
    except Exception as e:
        print(f"Error loading puzzle: {e}", file=sys.stderr)
        return []


def main():
    """Parse arguments and solve puzzle."""
    parser = argparse.ArgumentParser(
        description='Solve Binairo puzzles using constraint satisfaction and backtracking'
    )
    parser.add_argument(
        'puzzle_file',
        help='Path to puzzle JSON file (can contain single puzzle or array)'
    )
    parser.add_argument(
        '--puzzle-id',
        type=int,
        help='Specific puzzle ID to solve (if file contains multiple puzzles)'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Show detailed output: step-by-step solving, performance metrics, and techniques used'
    )
    
    args = parser.parse_args()
    
    # Load puzzles
    puzzles = load_puzzles(args.puzzle_file)
    if not puzzles:
        return 1
    
    # Select specific puzzle or first one
    if args.puzzle_id:
        puzzle_data = next((p for p in puzzles if p.get('id') == args.puzzle_id), None)
        if not puzzle_data:
            print(f"No puzzle found with ID {args.puzzle_id}", file=sys.stderr)
            available_ids = [p.get('id', 'N/A') for p in puzzles]
            print(f"Available IDs: {available_ids}", file=sys.stderr)
            return 1
    else:
        if len(puzzles) > 1:
            print(f"File contains {len(puzzles)} puzzles. Using first puzzle (ID: {puzzles[0].get('id', 'N/A')}).")
            print(f"Use --puzzle-id to select a specific puzzle.")
        puzzle_data = puzzles[0]
    
    puzzle_grid = puzzle_data.get('puzzle')
    if not puzzle_grid:
        print("No puzzle grid found in selected puzzle", file=sys.stderr)
        return 1
    
    # Print initial info
    print(f"Puzzle ID: {puzzle_data.get('id', 'N/A')}")
    print(f"Size: {puzzle_data.get('size', 'Unknown')}")
    print(f"Difficulty: {puzzle_data.get('difficulty', 'Unknown')}")
    print(f"Source ID: {puzzle_data.get('puzzle_id', 'N/A')}")
    
    print("\nInitial Grid:")
    solver = BinairoSolver(puzzle_grid)
    solver.print_grid()
    
    # Always verify solution uniqueness
    print("\nVerifying solution uniqueness...")
    solution_count = solver.count_solutions(3)
    if solution_count == 0:
        print("❌ No solutions exist")
        return 1
    elif solution_count == 1:
        print("✓ Exactly one solution exists")
    elif solution_count >= 2:
        print(f"⚠️  Multiple solutions exist (found at least {solution_count})")
        return 1
    print()
    
    # Set verbose mode
    verbose = args.verbose
    
    # Solve
    print(f"Solving using constraint satisfaction...")
    solved, moves_log = solver.solve(verbose)
    
    if solved:
        print(f"\n✓ Puzzle solved successfully!")
        print(solver.metrics.format_summary())
        print(f"\nFinal Grid:")
        solver.print_grid()
        
        if verbose:
            print(f"\nAlgorithm: Constraint satisfaction with backtracking")
            print(f"Total moves: {len(moves_log)}")
            print(f"Techniques used: {', '.join(solver.techniques_used)}")
            
            print(f"\nMove sequence:")
            for i, move in enumerate(moves_log, 1):
                print(f"  {i:2}. {move}")
    else:
        print(f"\n✗ Could not solve puzzle")
        print(f"Final state:")
        solver.print_grid()
        
        if verbose and moves_log:
            print(f"\nProgress made ({len(moves_log)} moves):")
            for move in moves_log[-5:]:  # Show last 5 moves
                print(f"  {move}")
    
    return 0 if solved else 1


if __name__ == '__main__':
    sys.exit(main())