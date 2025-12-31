# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Monarchy is a Binairo puzzle repository that contains tools for scraping and storing binary puzzles. The project focuses on collecting puzzles from puzzle-binairo.com and maintaining them in a structured JSON format.

## Repository Structure

- **puzzles/** - Contains JSON files with puzzle data and metadata
- **scripts/** - Utility scripts for puzzle operations
  - `scrape.py` - Main scraping tool for downloading puzzles from puzzle-binairo.com
  - `solve.py` - Human-technique puzzle solver using logical deduction
  - `rank.py` - Human-difficulty ranking system based on cognitive complexity
  - `validate.py` - Comprehensive puzzle file validator with mandatory ID enforcement

## Development Commands

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
# Solve a puzzle using human techniques
python3 scripts/solve.py puzzles/6x6.json

# Show step-by-step solving process
python3 scripts/solve.py --show-steps puzzles/6x6.json

# Show which techniques were used
python3 scripts/solve.py --show-techniques puzzles/6x6.json
```

### Ranking Puzzle Difficulty
```bash
# Rank a single puzzle's human difficulty
python3 scripts/rank.py puzzles/6x6.json

# Rank multiple puzzles with detailed analysis
python3 scripts/rank.py --detailed puzzles/*.json

# Export ranking results to CSV
python3 scripts/rank.py --export-csv results.csv puzzles/*.json

# Show technique usage breakdown
python3 scripts/rank.py --technique-breakdown puzzles/*.json
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

### Human-Technique Analysis System
The solving and ranking tools focus on human-cognitive approaches:

**Solving Techniques** (`scripts/solve.py`):
- **Avoid Three Rule**: Prevent three consecutive identical digits
- **Balance Rule**: Ensure equal 0s and 1s in rows/columns
- **Duplicate Prevention**: Prevent identical rows or columns
- **Forced Moves**: Fill cells when only one value is valid

**Difficulty Ranking** (`scripts/rank.py`):
- **Technique Complexity**: Weights techniques by cognitive difficulty
- **Advanced Usage**: Measures reliance on complex pattern recognition
- **Interaction Complexity**: Analyzes how techniques combine during solving
- **Human Difficulty Scale**: 1-10 scoring based on cognitive load, not computation

**Validation System** (`scripts/validate.py`):
- **Structure Validation**: JSON format and required field checking
- **ID Enforcement**: Mandatory numeric `id` field for all puzzles
- **Solvability Testing**: Ensures puzzles are solvable with human techniques
- **Duplicate Detection**: Identifies identical puzzle content across files

### Available Puzzle Configurations
- Sizes: 6x6, 8x8, 10x10, 14x14
- Difficulties: easy, hard
- Source: puzzle-binairo.com

## Key Implementation Details

- Python 3 standard library only (no external dependencies)
- Robust error handling for network requests and data parsing
- Automatic directory creation for output files
- Grid visualization with coordinate labels (A-Z columns, 1-N rows)