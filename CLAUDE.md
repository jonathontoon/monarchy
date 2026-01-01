# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Monarchy is a Binairo puzzle repository that contains tools for scraping and storing binary puzzles. The project focuses on collecting puzzles from puzzle-binairo.com and maintaining them in a structured JSON format.

## Repository Structure

- **puzzles/** - Contains JSON files with puzzle data and metadata
- **scripts/** - Utility scripts for puzzle operations
  - `main.py` - Unified workflow script for complete puzzle acquisition process
  - `scrape.py` - Main scraping tool for downloading puzzles from puzzle-binairo.com
  - `solve.py` - Algorithmic puzzle solver for validation
  - `validate.py` - Comprehensive puzzle file validator with mandatory ID enforcement

## Development Commands

### Unified Workflow
```bash
# Run complete workflow (scrape → solve → add to file → validate)
python3 scripts/main.py

# Specific size and difficulty
python3 scripts/main.py --size 8 --difficulty hard

# Add multiple puzzles
python3 scripts/main.py --count 3

# Verbose output showing all steps
python3 scripts/main.py --verbose
```

### Running the Scraper
```bash
# Scrape a 6x6 easy puzzle (default)
python3 scripts/scrape.py

# Scrape specific size and difficulty
python3 scripts/scrape.py --size 8 --difficulty hard

# List available configurations
python3 scripts/scrape.py --list

# Save to custom file
python3 scripts/scrape.py --output custom_puzzle.json

# Show help
python3 scripts/scrape.py --help
```

### Solving Puzzles
```bash
# Solve a puzzle algorithmically
python3 scripts/solve.py puzzles/6x6.json

# Show step-by-step solving process
python3 scripts/solve.py --show-steps puzzles/6x6.json
```

### Validating Puzzles
```bash
# Validate a single puzzle file
python3 scripts/validate.py puzzles/6x6.json

# Batch validate all puzzles
python3 scripts/validate.py --batch puzzles/*.json

# Strict validation with detailed output
python3 scripts/validate.py --strict --verbose puzzles/*.json

# Check for duplicate puzzles
python3 scripts/validate.py --check-duplicates puzzles/*.json
```

## Code Architecture

### Puzzle Data Format
Puzzles are stored as JSON files with the following structure:
- `id`: **Mandatory** numeric internal identifier (unique within collection)
- `size`: Grid dimensions (e.g., "6x6")
- `difficulty`: "easy" or "hard"
- `puzzle_id`: Optional unique identifier from the source website
- `puzzle`: 2D array where `null` represents empty cells, `0`/`1` are clues

**Example:**
```json
{
  "id": 1,
  "size": "6x6",
  "difficulty": "easy",
  "puzzle_id": "4605673",
  "puzzle": [[0, null, null, 0, 1, 1], ...]
}
```

### Scraping System
The scraper (`scripts/scrape.py`) implements:
- **Task String Decoding**: Uses run-length encoding where digits (0/1) are clues and letters (a-z) represent skip counts
- **Grid Processing**: Converts flat encoded strings to 2D grids in row-major order
- **Error Handling**: Validates puzzle data and provides meaningful error messages
- **Flexible Output**: Supports custom file paths and console display options

### Solving and Validation System
The solving and validation tools ensure puzzle integrity:

**Solving Engine** (`scripts/solve.py`):
- **Algorithmic Solver**: Uses backtracking and constraint propagation
- **Rule Enforcement**: Ensures no three consecutive identical digits
- **Balance Checking**: Verifies equal 0s and 1s in rows/columns
- **Uniqueness Validation**: Prevents duplicate rows or columns

**Validation System** (`scripts/validate.py`):
- **Structure Validation**: JSON format and required field checking
- **ID Enforcement**: Mandatory numeric `id` field for all puzzles
- **Solvability Testing**: Ensures puzzles are solvable and have unique solutions
- **Duplicate Detection**: Identifies identical puzzle content across files

### Available Puzzle Configurations
- Sizes: 6x6, 8x8, 10x10
- Difficulties: easy, hard
- Source: puzzle-binairo.com

## Key Implementation Details

- Python 3 standard library only (no external dependencies)
- Robust error handling for network requests and data parsing
- Automatic directory creation for output files
- Grid visualization with coordinate labels (A-Z columns, 1-N rows)