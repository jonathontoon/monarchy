# AGENTS.md - Monarchy Project Guide

## Project Overview
Monarchy is a Binairo puzzle scraper and solver. It contains:
- **puzzles/**: JSON puzzle data (Binairo grid puzzles)
- **scripts/**: Python utilities for scraping puzzles from puzzle-binairo.com

## Running Commands
- **Scrape puzzle**: `python3 scripts/scrape.py --size 6 --difficulty easy`
- **Scrape with output**: `python3 scripts/scrape.py --size 6 --difficulty easy --output puzzles/6x6.json`
- **List available puzzles**: `python3 scripts/scrape.py --list`
- **View grid without saving**: `python3 scripts/scrape.py --size 6 --no-grid`

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
  "size": "6x6",
  "difficulty": "easy",
  "puzzle_id": "4793631",
  "puzzle": [[row_as_list], ...]
}
```
Grid values: 0, 1, or null (empty/unknown).

## Encoding Details
Puzzle task strings use run-length encoding:
- Digits (0/1): place value, advance 1 cell
- Letters (a-z): skip cells (a=1, b=2, ..., z=26)
- Grid scanned left→right, top→bottom (row-major order)
