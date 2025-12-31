# AGENTS.md - Monarchy Project Guide

## Project Overview
Monarchy is a Binairo puzzle scraper and solver. It contains:
- **puzzles/**: JSON puzzle data (Binairo grid puzzles)
- **scripts/**: Python utilities for scraping puzzles from puzzle-binairo.com

## Running Commands

### Scraping
- **Scrape puzzle**: `python3 scripts/scrape.py --size 6 --difficulty easy`
- **Scrape with output**: `python3 scripts/scrape.py --size 6 --difficulty easy --output puzzles/6x6.json`
- **List available puzzles**: `python3 scripts/scrape.py --list`
- **View grid without saving**: `python3 scripts/scrape.py --size 6 --no-grid`

### Solving
- **Solve puzzle**: `python3 scripts/solve.py puzzles/6x6.json`
- **Solve with steps**: `python3 scripts/solve.py puzzles/6x6.json --show-steps`
- **Show solving techniques**: `python3 scripts/solve.py puzzles/6x6.json --show-techniques`

### Validation
- **Validate single puzzle**: `python3 scripts/validate.py puzzles/6x6.json`
- **Validate multiple puzzles**: `python3 scripts/validate.py puzzles/*.json --batch`
- **Strict validation**: `python3 scripts/validate.py puzzles/*.json --strict`
- **Check puzzle IDs**: `python3 scripts/validate.py puzzles/*.json --check-ids`
- **Find duplicates**: `python3 scripts/validate.py puzzles/*.json --check-duplicates`

### Ranking
- **Rank puzzle difficulty**: `python3 scripts/rank.py puzzles/6x6.json`
- **Detailed analysis**: `python3 scripts/rank.py puzzles/6x6.json --detailed`
- **Analyze multiple**: `python3 scripts/rank.py puzzles/*.json --detailed`
- **Export results to CSV**: `python3 scripts/rank.py puzzles/*.json --export-csv results.csv`
- **Show technique breakdown**: `python3 scripts/rank.py puzzles/*.json --technique-breakdown`

## Python Code Style
- Python 3 with docstrings (Google style) for all functions and modules
- Use `sys.stderr` for error output, `print()` for normal output
- Handle exceptions explicitly with try/except blocks
- Use `argparse` for CLI arguments
- File operations use `os.path` and proper directory creation

## Data Format
Puzzle JSON contains:
```json
{
  "id": 1,
  "size": "6x6",
  "difficulty": "easy",
  "puzzle_id": "4793631",
  "puzzle": [[row_as_list], ...]
}
```
- Grid values: 0, 1, or null (empty/unknown)
- `id`: Unique identifier for puzzle (mandatory)
- `puzzle_id`: Source ID from puzzle-binairo.com (optional)

## Script Descriptions

### scrape.py
Scrapes Binairo puzzles from puzzle-binairo.com and decodes task strings using run-length encoding.
- Supports puzzle sizes: 6x6, 8x8, 10x10, 14x14
- Supports difficulties: easy, hard
- Decodes run-length encoded task strings into 2D grids

### solve.py
Solves Binairo puzzles using human-readable logical techniques (no brute force).
- Techniques: Avoid Three Rule, Balance Rule, Duplicate Prevention, Forced Moves
- Tracks solving steps and techniques used
- Provides detailed output including solution grid and move sequence

### validate.py
Validates puzzle file integrity and correctness.
- Checks JSON structure and required fields (id, size, difficulty, puzzle)
- Validates puzzle grid dimensions and cell values
- Detects duplicate puzzles by content hash
- Tests solvability using human techniques
- Supports batch validation with summary reports

### rank.py
Ranks puzzle difficulty based on human-solving complexity.
- Assigns difficulty scores 1-10 based on human cognitive complexity
- Analyzes technique variety, sequence, and interaction
- Supports single and batch analysis with CSV export
- Provides human-readable analysis summaries

## Encoding Details
Puzzle task strings use run-length encoding:
- Digits (0/1): place value, advance 1 cell
- Letters (a-z): skip cells (a=1, b=2, ..., z=26)
- Grid scanned left→right, top→bottom (row-major order)
