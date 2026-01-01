# Monarchy

A Binairo puzzle scraper and solver. Monarchy downloads puzzles from puzzle-binairo.com, solves them using human-readable logical techniques, and analyzes difficulty.

## Quick Start

```bash
# Complete workflow: scrape → solve → add to file → validate
python3 scripts/main.py --size 6 --difficulty easy

# Or manually scrape a puzzle
python3 scripts/scrape.py --size 6 --difficulty easy --output puzzles/6x6.json

# Solve it with detailed steps
python3 scripts/solve.py puzzles/6x6.json --show-steps

# Validate your puzzles
python3 scripts/validate.py puzzles/*.json --batch
```

## Project Structure

- **puzzles/** - Puzzle files (JSON format)
- **scripts/** - Utility scripts:
  - `main.py` - Unified workflow for complete puzzle acquisition
  - `scrape.py` - Download puzzles from puzzle-binairo.com
  - `solve.py` - Solve puzzles using human techniques
  - `validate.py` - Validate puzzle integrity and correctness

## Solving Techniques

The solver uses only human-readable techniques:
- **Avoid Three Rule** - Prevent three consecutive identical digits
- **Balance Rule** - Ensure equal 0s and 1s in rows/columns
- **Duplicate Prevention** - Prevent identical rows or columns
- **Forced Moves** - Fill cells when only one option remains valid

No brute force or backtracking—only logical deduction.

## Documentation

See [AGENTS.md](AGENTS.md) for detailed commands and usage examples.
