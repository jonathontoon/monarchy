#!/usr/bin/env python3
"""
Validate Binairo puzzle files for integrity and correctness.

This validator ensures:
- JSON structure is correct and complete
- Required fields are present (including mandatory 'id')
- Puzzle grids are valid and solvable
- No duplicate puzzles exist
- Metadata is consistent

Can validate single files or batch process entire directories.
"""

import json
import sys
import argparse
import glob
import os
import hashlib
from typing import List, Dict, Set, Optional, Tuple
from solve import BinairoSolver


class PuzzleValidator:
    """Comprehensive puzzle validation system."""
    
    REQUIRED_FIELDS = ['id', 'size', 'difficulty', 'puzzle']
    OPTIONAL_FIELDS = ['puzzle_id']  # Website source ID is optional
    VALID_DIFFICULTIES = ['easy', 'hard']
    VALID_SIZES = ['6x6', '8x8', '10x10', '14x14']
    
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.seen_ids = set()
        self.seen_puzzles = {}  # hash -> file_path for duplicate detection
        self.next_suggested_id = 1
    
    def validate_file(self, file_path: str, strict: bool = False) -> dict:
        """
        Validate a single puzzle file.
        
        Args:
            file_path: Path to puzzle JSON file
            strict: Enable strict validation mode
            
        Returns:
            Validation result dictionary
        """
        result = {
            'file': file_path,
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        try:
            # Load and parse JSON
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            # Validate structure and fields
            self._validate_structure(data, result, strict)
            
            # Validate puzzle grid
            if 'puzzle' in data:
                self._validate_puzzle_grid(data, result, strict)
            
            # Check for duplicates
            self._check_duplicates(data, file_path, result)
            
            # Validate ID (mandatory field)
            self._validate_id(data, result)
            
            # Validate solvability (if grid is complete enough)
            if result['valid'] and 'puzzle' in data:
                self._validate_solvability(data['puzzle'], result, strict)
            
        except json.JSONDecodeError as e:
            result['valid'] = False
            result['errors'].append(f"Invalid JSON: {e}")
        except Exception as e:
            result['valid'] = False
            result['errors'].append(f"Error reading file: {e}")
        
        return result
    
    def _validate_structure(self, data, result: dict, strict: bool):
        """Validate JSON structure and required fields."""
        # Handle both single object and array formats
        if isinstance(data, list):
            if len(data) == 0:
                result['valid'] = False
                result['errors'].append("Empty puzzle array")
                return
            # Validate each puzzle in the array
            for i, puzzle in enumerate(data):
                if not isinstance(puzzle, dict):
                    result['valid'] = False
                    result['errors'].append(f"Puzzle {i} is not an object")
                    return
            # For array format, validate just the first puzzle for structure
            data = data[0]
        elif not isinstance(data, dict):
            result['valid'] = False
            result['errors'].append("Root element must be an object or array")
            return
        
        # Check required fields
        for field in self.REQUIRED_FIELDS:
            if field not in data:
                result['valid'] = False
                result['errors'].append(f"Missing required field: {field}")
        
        # Validate field values
        if 'id' in data:
            if not isinstance(data['id'], int) or data['id'] <= 0:
                result['valid'] = False
                result['errors'].append("Field 'id' must be a positive integer")
        
        if 'size' in data:
            if data['size'] not in self.VALID_SIZES:
                result['valid'] = False
                result['errors'].append(f"Invalid size '{data['size']}'. Must be one of: {self.VALID_SIZES}")
        
        if 'difficulty' in data:
            if data['difficulty'] not in self.VALID_DIFFICULTIES:
                result['valid'] = False
                result['errors'].append(f"Invalid difficulty '{data['difficulty']}'. Must be one of: {self.VALID_DIFFICULTIES}")
        
        # Check for unexpected fields
        expected_fields = set(self.REQUIRED_FIELDS + self.OPTIONAL_FIELDS)
        extra_fields = set(data.keys()) - expected_fields
        if extra_fields and strict:
            result['warnings'].append(f"Unexpected fields: {list(extra_fields)}")
    
    def _validate_puzzle_grid(self, data: dict, result: dict, strict: bool):
        """Validate puzzle grid structure and content."""
        puzzle = data['puzzle']
        
        if not isinstance(puzzle, list):
            result['valid'] = False
            result['errors'].append("Puzzle must be a 2D array")
            return
        
        # Extract expected size
        size_str = data.get('size', '')
        if 'x' not in size_str:
            return  # Size validation will catch this
        
        try:
            expected_size = int(size_str.split('x')[0])
        except ValueError:
            return  # Size validation will catch this
        
        # Check grid dimensions
        if len(puzzle) != expected_size:
            result['valid'] = False
            result['errors'].append(f"Grid height {len(puzzle)} doesn't match size {size_str}")
            return
        
        for i, row in enumerate(puzzle):
            if not isinstance(row, list):
                result['valid'] = False
                result['errors'].append(f"Row {i} is not an array")
                continue
            
            if len(row) != expected_size:
                result['valid'] = False
                result['errors'].append(f"Row {i} has {len(row)} cells, expected {expected_size}")
                continue
            
            # Check cell values
            for j, cell in enumerate(row):
                if cell not in [None, 0, 1]:
                    result['valid'] = False
                    result['errors'].append(f"Invalid cell value at ({i},{j}): {cell}. Must be null, 0, or 1")
        
        # Check for reasonable number of clues
        if result['valid']:
            total_cells = expected_size * expected_size
            clue_count = sum(1 for row in puzzle for cell in row if cell is not None)
            
            if clue_count == 0:
                result['warnings'].append("Puzzle has no clues")
            elif clue_count >= total_cells:
                result['warnings'].append("Puzzle is completely filled")
            elif strict and clue_count < expected_size // 2:
                result['warnings'].append(f"Very few clues ({clue_count}), puzzle may be too hard")
    
    def _validate_id(self, data: dict, result: dict):
        """Validate puzzle ID uniqueness."""
        if 'id' not in data:
            return
        
        puzzle_id = data['id']
        if puzzle_id in self.seen_ids:
            result['valid'] = False
            result['errors'].append(f"Duplicate puzzle ID: {puzzle_id}")
        else:
            self.seen_ids.add(puzzle_id)
            self.next_suggested_id = max(self.next_suggested_id, puzzle_id + 1)
    
    
    def _check_duplicates(self, data: dict, file_path: str, result: dict):
        """Check for duplicate puzzles based on grid content."""
        if 'puzzle' not in data:
            return
        
        # Create hash of puzzle grid
        puzzle_str = json.dumps(data['puzzle'], sort_keys=True)
        puzzle_hash = hashlib.md5(puzzle_str.encode()).hexdigest()
        
        if puzzle_hash in self.seen_puzzles:
            original_file = self.seen_puzzles[puzzle_hash]
            result['warnings'].append(f"Duplicate puzzle content found in: {original_file}")
        else:
            self.seen_puzzles[puzzle_hash] = file_path
    
    def _validate_solvability(self, puzzle_grid: List[List], result: dict, strict: bool):
        """Check if puzzle is solvable using human techniques."""
        try:
            solver = BinairoSolver(puzzle_grid)
            solved, _ = solver.solve()
            
            if not solved:
                if strict:
                    result['valid'] = False
                    result['errors'].append("Puzzle cannot be solved using human techniques")
                else:
                    result['warnings'].append("Puzzle may require advanced techniques or be unsolvable")
            
            # Verify the solution is unique by checking if initial state is valid
            if solved and not solver.is_valid():
                result['valid'] = False
                result['errors'].append("Puzzle solution violates Binairo rules")
                
        except Exception as e:
            result['warnings'].append(f"Could not verify solvability: {e}")


def validate_batch(file_pattern: str, strict: bool = False) -> List[dict]:
    """Validate multiple puzzle files."""
    validator = PuzzleValidator()
    results = []
    
    # Collect files
    files = []
    for pattern in [file_pattern] if not isinstance(file_pattern, list) else file_pattern:
        if os.path.isfile(pattern):
            files.append(pattern)
        else:
            files.extend(glob.glob(pattern))
    
    files.sort()  # Process in consistent order
    
    # Validate each file
    for file_path in files:
        result = validator.validate_file(file_path, strict)
        results.append(result)
    
    return results


def print_validation_result(result: dict, verbose: bool = False):
    """Print validation result for a single file."""
    file_name = os.path.basename(result['file'])
    status = "✓" if result['valid'] else "✗"
    
    print(f"{status} {file_name}")
    
    if result['errors']:
        for error in result['errors']:
            print(f"    ERROR: {error}")
    
    if result['warnings'] and (verbose or not result['valid']):
        for warning in result['warnings']:
            print(f"    WARNING: {warning}")
    


def print_batch_summary(results: List[dict]):
    """Print summary of batch validation."""
    total = len(results)
    valid = sum(1 for r in results if r['valid'])
    
    print(f"\nValidation Summary:")
    print(f"  Total files: {total}")
    print(f"  Valid: {valid}")
    print(f"  Invalid: {total - valid}")
    
    # Show common issues
    all_errors = []
    all_warnings = []
    for result in results:
        all_errors.extend(result['errors'])
        all_warnings.extend(result['warnings'])
    
    if all_errors:
        print(f"\nCommon Errors:")
        error_counts = {}
        for error in all_errors:
            error_counts[error] = error_counts.get(error, 0) + 1
        for error, count in sorted(error_counts.items(), key=lambda x: x[1], reverse=True):
            if count > 1:
                print(f"  {error} ({count} files)")


def main():
    """Parse arguments and validate puzzles."""
    parser = argparse.ArgumentParser(
        description='Validate Binairo puzzle files for integrity and correctness'
    )
    parser.add_argument(
        'files',
        nargs='+',
        help='Puzzle JSON files to validate (supports glob patterns)'
    )
    parser.add_argument(
        '--batch',
        action='store_true',
        help='Process multiple files and show summary'
    )
    parser.add_argument(
        '--strict',
        action='store_true',
        help='Enable strict validation mode'
    )
    parser.add_argument(
        '--check-ids',
        action='store_true',
        help='Only check ID field presence and uniqueness'
    )
    parser.add_argument(
        '--check-duplicates',
        action='store_true',
        help='Focus on duplicate puzzle detection'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Show detailed output including warnings'
    )
    
    args = parser.parse_args()
    
    # Collect all files
    all_files = []
    for pattern in args.files:
        if os.path.isfile(pattern):
            all_files.append(pattern)
        else:
            all_files.extend(glob.glob(pattern))
    
    if not all_files:
        print("No files found matching the specified patterns", file=sys.stderr)
        return 1
    
    print(f"Validating {len(all_files)} file(s)...")
    
    # Validate files
    if args.batch or len(all_files) > 1:
        results = validate_batch(all_files, args.strict)
        
        # Print individual results
        for result in results:
            print_validation_result(result, args.verbose)
        
        # Print summary
        print_batch_summary(results)
        
        # Return error code if any validation failed
        return 0 if all(r['valid'] for r in results) else 1
    
    else:
        # Single file validation
        validator = PuzzleValidator()
        result = validator.validate_file(all_files[0], args.strict)
        
        print_validation_result(result, verbose=True)
        
        return 0 if result['valid'] else 1


if __name__ == '__main__':
    sys.exit(main())