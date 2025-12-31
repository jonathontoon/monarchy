#!/usr/bin/env python3
"""
Solve Binairo puzzles using human-readable logical techniques.

This solver uses only techniques that humans would naturally employ:
- Avoid Three Rule: Prevent three consecutive identical digits
- Balance Rule: Ensure equal 0s and 1s in rows/columns
- Duplicate Prevention: Prevent identical rows or columns
- Forced Moves: Fill cells when only one option remains valid

No brute force or backtracking - only logical deduction.
"""

import json
import sys
import argparse
import copy
from typing import List, Optional, Tuple, Dict, Set


class BinairoSolver:
    def __init__(self, puzzle: List[List[Optional[int]]]):
        self.grid = copy.deepcopy(puzzle)
        self.size = len(puzzle)
        self.moves_log = []
        self.techniques_used = set()
        
    def solve(self, show_steps: bool = False) -> Tuple[bool, List[str]]:
        """
        Solve the puzzle using human techniques.
        
        Returns:
            (solved, techniques_log)
        """
        progress = True
        iteration = 0
        
        while progress and not self.is_complete():
            progress = False
            iteration += 1
            
            if show_steps:
                print(f"\n--- Iteration {iteration} ---")
                self.print_grid()
            
            # Try each technique in order of complexity
            if self._apply_avoid_three_rule(show_steps):
                progress = True
            
            if self._apply_balance_rule(show_steps):
                progress = True
                
            if self._apply_duplicate_prevention(show_steps):
                progress = True
                
            if self._apply_forced_moves(show_steps):
                progress = True
        
        solved = self.is_complete() and self.is_valid()
        return solved, self.moves_log
    
    def _apply_avoid_three_rule(self, show_steps: bool = False) -> bool:
        """Prevent three consecutive identical digits."""
        progress = False
        
        # Check rows
        for r in range(self.size):
            for c in range(self.size - 2):
                if self._fill_avoid_three(r, c, r, c+1, r, c+2, "row", show_steps):
                    progress = True
        
        # Check columns
        for c in range(self.size):
            for r in range(self.size - 2):
                if self._fill_avoid_three(r, c, r+1, c, r+2, c, "column", show_steps):
                    progress = True
        
        return progress
    
    def _fill_avoid_three(self, r1: int, c1: int, r2: int, c2: int, r3: int, c3: int, 
                         direction: str, show_steps: bool) -> bool:
        """Fill a cell to avoid three consecutive identical digits."""
        cells = [(r1, c1), (r2, c2), (r3, c3)]
        values = [self.grid[r][c] for r, c in cells]
        
        # Case 1: Two identical values at positions 0,1 -> fill position 2 with opposite
        if values[0] is not None and values[1] is not None and values[2] is None:
            if values[0] == values[1]:
                fill_value = 1 - values[0]
                return self._make_move(r3, c3, fill_value, f"Avoid three in {direction}", show_steps)
        
        # Case 2: Two identical values at positions 1,2 -> fill position 0 with opposite  
        elif values[1] is not None and values[2] is not None and values[0] is None:
            if values[1] == values[2]:
                fill_value = 1 - values[1]
                return self._make_move(r1, c1, fill_value, f"Avoid three in {direction}", show_steps)
        
        # Case 3: Two identical values at positions 0,2 -> fill position 1 with opposite
        elif values[0] is not None and values[2] is not None and values[1] is None:
            if values[0] == values[2]:
                fill_value = 1 - values[0]
                return self._make_move(r2, c2, fill_value, f"Avoid three in {direction}", show_steps)
        
        return False
    
    def _apply_balance_rule(self, show_steps: bool = False) -> bool:
        """Fill remaining cells when a row/column has enough of one digit."""
        progress = False
        half_size = self.size // 2
        
        # Check rows
        for r in range(self.size):
            count_0 = sum(1 for c in range(self.size) if self.grid[r][c] == 0)
            count_1 = sum(1 for c in range(self.size) if self.grid[r][c] == 1)
            
            if count_0 == half_size:
                # Fill remaining with 1s
                for c in range(self.size):
                    if self.grid[r][c] is None:
                        if self._make_move(r, c, 1, "Balance rule (row needs 1s)", show_steps):
                            progress = True
            elif count_1 == half_size:
                # Fill remaining with 0s
                for c in range(self.size):
                    if self.grid[r][c] is None:
                        if self._make_move(r, c, 0, "Balance rule (row needs 0s)", show_steps):
                            progress = True
        
        # Check columns
        for c in range(self.size):
            count_0 = sum(1 for r in range(self.size) if self.grid[r][c] == 0)
            count_1 = sum(1 for r in range(self.size) if self.grid[r][c] == 1)
            
            if count_0 == half_size:
                # Fill remaining with 1s
                for r in range(self.size):
                    if self.grid[r][c] is None:
                        if self._make_move(r, c, 1, "Balance rule (column needs 1s)", show_steps):
                            progress = True
            elif count_1 == half_size:
                # Fill remaining with 0s
                for r in range(self.size):
                    if self.grid[r][c] is None:
                        if self._make_move(r, c, 0, "Balance rule (column needs 0s)", show_steps):
                            progress = True
        
        return progress
    
    def _apply_duplicate_prevention(self, show_steps: bool = False) -> bool:
        """Prevent duplicate rows or columns."""
        progress = False
        
        # Check for potential duplicate rows
        for r1 in range(self.size):
            for r2 in range(r1 + 1, self.size):
                if self._prevent_duplicate_rows(r1, r2, show_steps):
                    progress = True
        
        # Check for potential duplicate columns
        for c1 in range(self.size):
            for c2 in range(c1 + 1, self.size):
                if self._prevent_duplicate_columns(c1, c2, show_steps):
                    progress = True
        
        return progress
    
    def _prevent_duplicate_rows(self, r1: int, r2: int, show_steps: bool) -> bool:
        """Prevent two rows from being identical."""
        row1 = self.grid[r1]
        row2 = self.grid[r2]
        
        # Find positions where rows differ
        diff_positions = []
        none_positions_r1 = []
        none_positions_r2 = []
        
        for c in range(self.size):
            if row1[c] is None and row2[c] is None:
                continue
            elif row1[c] is None:
                none_positions_r1.append(c)
            elif row2[c] is None:
                none_positions_r2.append(c)
            elif row1[c] != row2[c]:
                diff_positions.append(c)
        
        # If rows are identical except for one None in each, fill them differently
        if len(diff_positions) == 0 and len(none_positions_r1) == 1 and len(none_positions_r2) == 1:
            c1, c2 = none_positions_r1[0], none_positions_r2[0]
            # Try filling with opposites
            for val in [0, 1]:
                if (self._is_valid_placement(r1, c1, val) and 
                    self._is_valid_placement(r2, c2, 1-val)):
                    self._make_move(r1, c1, val, f"Prevent duplicate rows {r1+1},{r2+1}", show_steps)
                    self._make_move(r2, c2, 1-val, f"Prevent duplicate rows {r1+1},{r2+1}", show_steps)
                    return True
        
        return False
    
    def _prevent_duplicate_columns(self, c1: int, c2: int, show_steps: bool) -> bool:
        """Prevent two columns from being identical."""
        col1 = [self.grid[r][c1] for r in range(self.size)]
        col2 = [self.grid[r][c2] for r in range(self.size)]
        
        # Find positions where columns differ
        diff_positions = []
        none_positions_c1 = []
        none_positions_c2 = []
        
        for r in range(self.size):
            if col1[r] is None and col2[r] is None:
                continue
            elif col1[r] is None:
                none_positions_c1.append(r)
            elif col2[r] is None:
                none_positions_c2.append(r)
            elif col1[r] != col2[r]:
                diff_positions.append(r)
        
        # If columns are identical except for one None in each, fill them differently
        if len(diff_positions) == 0 and len(none_positions_c1) == 1 and len(none_positions_c2) == 1:
            r1, r2 = none_positions_c1[0], none_positions_c2[0]
            # Try filling with opposites
            for val in [0, 1]:
                if (self._is_valid_placement(r1, c1, val) and 
                    self._is_valid_placement(r2, c2, 1-val)):
                    self._make_move(r1, c1, val, f"Prevent duplicate columns {c1+1},{c2+1}", show_steps)
                    self._make_move(r2, c2, 1-val, f"Prevent duplicate columns {c1+1},{c2+1}", show_steps)
                    return True
        
        return False
    
    def _apply_forced_moves(self, show_steps: bool = False) -> bool:
        """Fill cells where only one value is valid."""
        progress = False
        
        for r in range(self.size):
            for c in range(self.size):
                if self.grid[r][c] is None:
                    valid_values = []
                    for val in [0, 1]:
                        if self._is_valid_placement(r, c, val):
                            valid_values.append(val)
                    
                    if len(valid_values) == 1:
                        if self._make_move(r, c, valid_values[0], "Forced move (only valid option)", show_steps):
                            progress = True
        
        return progress
    
    def _is_valid_placement(self, r: int, c: int, value: int) -> bool:
        """Check if placing a value at position (r,c) is valid."""
        # Temporarily place the value
        original = self.grid[r][c]
        self.grid[r][c] = value
        
        valid = True
        
        # Check no three consecutive in row
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
            half_size = self.size // 2
            row_count = sum(1 for col in range(self.size) if self.grid[r][col] == value)
            col_count = sum(1 for row in range(self.size) if self.grid[row][c] == value)
            
            if row_count > half_size or col_count > half_size:
                valid = False
        
        # Restore original value
        self.grid[r][c] = original
        return valid
    
    def _make_move(self, r: int, c: int, value: int, technique: str, show_steps: bool) -> bool:
        """Make a move and log it."""
        if self.grid[r][c] is not None:
            return False
        
        self.grid[r][c] = value
        move_desc = f"Set ({chr(65+c)},{r+1}) = {value} [{technique}]"
        self.moves_log.append(move_desc)
        self.techniques_used.add(technique.split()[0])  # First word of technique
        
        if show_steps:
            print(f"  {move_desc}")
        
        return True
    
    def is_complete(self) -> bool:
        """Check if puzzle is completely filled."""
        for r in range(self.size):
            for c in range(self.size):
                if self.grid[r][c] is None:
                    return False
        return True
    
    def is_valid(self) -> bool:
        """Check if current state is valid."""
        half_size = self.size // 2
        
        # Check rows
        for r in range(self.size):
            row = self.grid[r]
            if row.count(0) != half_size or row.count(1) != half_size:
                return False
            
            # Check no three consecutive
            for c in range(self.size - 2):
                if row[c] == row[c+1] == row[c+2]:
                    return False
        
        # Check columns
        for c in range(self.size):
            col = [self.grid[r][c] for r in range(self.size)]
            if col.count(0) != half_size or col.count(1) != half_size:
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
    
    def print_grid(self):
        """Print current grid state."""
        print("  " + " ".join(chr(ord('A') + i) for i in range(self.size)))
        for i, row in enumerate(self.grid, 1):
            cells = " ".join(str(cell) if cell is not None else "." for cell in row)
            print(f"{i} {cells}")


def load_puzzle(file_path: str) -> dict:
    """Load puzzle from JSON file."""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading puzzle: {e}", file=sys.stderr)
        return None


def main():
    """Parse arguments and solve puzzle."""
    parser = argparse.ArgumentParser(
        description='Solve Binairo puzzles using human logical techniques'
    )
    parser.add_argument(
        'puzzle_file',
        help='Path to puzzle JSON file'
    )
    parser.add_argument(
        '--show-steps',
        action='store_true',
        help='Show step-by-step solving process'
    )
    parser.add_argument(
        '--show-techniques',
        action='store_true',
        help='Show techniques used in solving'
    )
    
    args = parser.parse_args()
    
    # Load puzzle
    puzzle_data = load_puzzle(args.puzzle_file)
    if not puzzle_data:
        return 1
    
    puzzle_grid = puzzle_data.get('puzzle')
    if not puzzle_grid:
        print("No puzzle grid found in file", file=sys.stderr)
        return 1
    
    # Print initial info
    print(f"Puzzle ID: {puzzle_data.get('id', 'N/A')}")
    print(f"Size: {puzzle_data.get('size', 'Unknown')}")
    print(f"Difficulty: {puzzle_data.get('difficulty', 'Unknown')}")
    print(f"Source ID: {puzzle_data.get('puzzle_id', 'N/A')}")
    
    print("\nInitial Grid:")
    solver = BinairoSolver(puzzle_grid)
    solver.print_grid()
    
    # Solve
    print(f"\nSolving using human techniques...")
    solved, moves_log = solver.solve(args.show_steps)
    
    if solved:
        print(f"\n✓ Puzzle solved successfully!")
        print(f"\nFinal Grid:")
        solver.print_grid()
        
        if args.show_techniques:
            print(f"\nTechniques used: {', '.join(sorted(solver.techniques_used))}")
            print(f"Total moves: {len(moves_log)}")
            
            if not args.show_steps:
                print(f"\nMove sequence:")
                for i, move in enumerate(moves_log, 1):
                    print(f"  {i:2}. {move}")
    else:
        print(f"\n✗ Could not solve puzzle using human techniques alone")
        print(f"Partial solution:")
        solver.print_grid()
        
        if moves_log:
            print(f"\nProgress made ({len(moves_log)} moves):")
            for move in moves_log[-5:]:  # Show last 5 moves
                print(f"  {move}")
    
    return 0 if solved else 1


if __name__ == '__main__':
    sys.exit(main())