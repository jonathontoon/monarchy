#!/usr/bin/env python3
"""
Rank Binairo puzzle difficulty based on human-solving techniques.

This analyzer evaluates puzzles based on the cognitive complexity required
for human solvers, not computational difficulty. It considers:
- Which techniques are required
- How frequently advanced techniques are needed  
- Depth of logical reasoning required
- Interaction complexity between techniques

Provides human-meaningful difficulty scores from 1-10.
"""

import json
import sys
import argparse
import glob
import os
from typing import List, Dict, Tuple, Optional
from solve import BinairoSolver


class TechniqueAnalyzer:
    """Analyze solving techniques and assign difficulty scores."""
    
    TECHNIQUE_WEIGHTS = {
        'Avoid': 1,      # Basic avoid-three rule
        'Balance': 2,    # Count-based balance rule  
        'Prevent': 4,    # Duplicate prevention
        'Forced': 3,     # Forced moves (constraint propagation)
    }
    
    def __init__(self):
        self.reset_stats()
    
    def reset_stats(self):
        """Reset analysis statistics."""
        self.technique_counts = {}
        self.total_moves = 0
        self.solving_depth = 0
        self.technique_sequence = []
    
    def analyze_puzzle(self, puzzle_grid: List[List[Optional[int]]]) -> Dict:
        """
        Analyze a puzzle and return difficulty metrics.
        
        Returns:
            Dictionary with analysis results
        """
        self.reset_stats()
        
        solver = BinairoSolver(puzzle_grid)
        solved, moves_log = solver.solve(show_steps=False)
        
        if not solved:
            return {
                'solved': False,
                'difficulty_score': 10,  # Unsolvable by human techniques
                'analysis': 'Could not solve with human techniques'
            }
        
        # Analyze the solving process
        self.total_moves = len(moves_log)
        
        # Count technique usage
        for move in moves_log:
            technique = self._extract_technique(move)
            self.technique_counts[technique] = self.technique_counts.get(technique, 0) + 1
            self.technique_sequence.append(technique)
        
        # Calculate metrics
        complexity_score = self._calculate_complexity_score()
        technique_variety = len(self.technique_counts)
        advanced_technique_ratio = self._calculate_advanced_ratio()
        interaction_complexity = self._calculate_interaction_complexity()
        
        # Calculate final difficulty score (1-10)
        difficulty_score = self._calculate_difficulty_score(
            complexity_score, technique_variety, advanced_technique_ratio, interaction_complexity
        )
        
        return {
            'solved': True,
            'difficulty_score': difficulty_score,
            'total_moves': self.total_moves,
            'technique_counts': dict(self.technique_counts),
            'technique_variety': technique_variety,
            'complexity_score': complexity_score,
            'advanced_ratio': advanced_technique_ratio,
            'interaction_complexity': interaction_complexity,
            'technique_sequence': list(self.technique_sequence),
            'analysis': self._generate_analysis_text()
        }
    
    def _extract_technique(self, move: str) -> str:
        """Extract technique type from move description."""
        if 'Avoid' in move:
            return 'Avoid'
        elif 'Balance' in move:
            return 'Balance'
        elif 'Prevent' in move:
            return 'Prevent'
        elif 'Forced' in move:
            return 'Forced'
        else:
            return 'Unknown'
    
    def _calculate_complexity_score(self) -> float:
        """Calculate weighted complexity based on technique usage."""
        total_weight = 0
        for technique, count in self.technique_counts.items():
            weight = self.TECHNIQUE_WEIGHTS.get(technique, 1)
            total_weight += weight * count
        
        # Normalize by total moves
        return total_weight / max(self.total_moves, 1)
    
    def _calculate_advanced_ratio(self) -> float:
        """Calculate ratio of advanced technique usage."""
        advanced_techniques = ['Prevent', 'Forced']
        advanced_count = sum(
            self.technique_counts.get(tech, 0) for tech in advanced_techniques
        )
        return advanced_count / max(self.total_moves, 1)
    
    def _calculate_interaction_complexity(self) -> float:
        """
        Calculate complexity from technique interactions.
        Higher score when techniques are mixed throughout solving.
        """
        if len(self.technique_sequence) <= 1:
            return 0
        
        # Count technique transitions
        transitions = 0
        for i in range(1, len(self.technique_sequence)):
            if self.technique_sequence[i] != self.technique_sequence[i-1]:
                transitions += 1
        
        # Normalize by sequence length
        return transitions / (len(self.technique_sequence) - 1)
    
    def _calculate_difficulty_score(self, complexity_score: float, variety: int, 
                                  advanced_ratio: float, interaction: float) -> int:
        """
        Calculate final human difficulty score (1-10).
        
        Scoring philosophy:
        1-2: Basic puzzles requiring only avoid-three and balance
        3-4: Moderate puzzles with some forced moves
        5-6: Challenging puzzles requiring duplicate prevention
        7-8: Complex puzzles with high technique mixing
        9-10: Very complex or unsolvable puzzles
        """
        # Base score from complexity
        base_score = complexity_score * 2.5
        
        # Bonus for technique variety (more techniques = harder)
        variety_bonus = (variety - 1) * 0.8
        
        # Bonus for advanced technique usage
        advanced_bonus = advanced_ratio * 3
        
        # Bonus for technique interaction complexity
        interaction_bonus = interaction * 1.5
        
        # Bonus for move count (longer puzzles are generally harder)
        length_bonus = min(self.total_moves / 20, 1.5)
        
        total_score = base_score + variety_bonus + advanced_bonus + interaction_bonus + length_bonus
        
        # Clamp to 1-10 range
        return max(1, min(10, round(total_score)))
    
    def _generate_analysis_text(self) -> str:
        """Generate human-readable analysis text."""
        analysis = []
        
        # Move count analysis
        if self.total_moves <= 10:
            analysis.append("Quick solve")
        elif self.total_moves <= 20:
            analysis.append("Moderate solving time")
        else:
            analysis.append("Long solve required")
        
        # Technique analysis
        main_techniques = [t for t, c in self.technique_counts.items() if c > 1]
        if 'Prevent' in main_techniques:
            analysis.append("requires duplicate prevention")
        if 'Forced' in main_techniques:
            analysis.append("needs constraint propagation")
        if len(main_techniques) >= 3:
            analysis.append("uses multiple techniques")
        
        # Pattern analysis
        advanced_ratio = self._calculate_advanced_ratio()
        if advanced_ratio > 0.5:
            analysis.append("heavily relies on advanced techniques")
        elif advanced_ratio > 0.2:
            analysis.append("needs some advanced techniques")
        
        return "; ".join(analysis) if analysis else "straightforward solve"


def load_puzzles(pattern: str) -> List[Tuple[str, dict]]:
    """Load puzzles from file pattern."""
    puzzles = []
    
    for file_path in glob.glob(pattern):
        try:
            with open(file_path, 'r') as f:
                puzzle_data = json.load(f)
                puzzles.append((file_path, puzzle_data))
        except Exception as e:
            print(f"Error loading {file_path}: {e}", file=sys.stderr)
    
    return puzzles


def rank_single_puzzle(file_path: str, show_details: bool = False) -> Optional[dict]:
    """Rank a single puzzle file."""
    try:
        with open(file_path, 'r') as f:
            puzzle_data = json.load(f)
    except Exception as e:
        print(f"Error loading {file_path}: {e}", file=sys.stderr)
        return None
    
    puzzle_grid = puzzle_data.get('puzzle')
    if not puzzle_grid:
        print(f"No puzzle grid in {file_path}", file=sys.stderr)
        return None
    
    analyzer = TechniqueAnalyzer()
    analysis = analyzer.analyze_puzzle(puzzle_grid)
    
    # Add puzzle metadata
    analysis['file'] = file_path
    analysis['puzzle_id'] = puzzle_data.get('id', 'N/A')
    analysis['source_id'] = puzzle_data.get('puzzle_id', 'N/A')
    analysis['size'] = puzzle_data.get('size', 'Unknown')
    analysis['stated_difficulty'] = puzzle_data.get('difficulty', 'Unknown')
    
    return analysis


def print_detailed_analysis(analysis: dict):
    """Print detailed analysis of a puzzle."""
    print(f"\nPuzzle: {analysis['file']}")
    print(f"ID: {analysis['puzzle_id']} (Source: {analysis['source_id']})")
    print(f"Size: {analysis['size']}, Stated: {analysis['stated_difficulty']}")
    print(f"Human Difficulty Score: {analysis['difficulty_score']}/10")
    
    if analysis['solved']:
        print(f"Total Moves: {analysis['total_moves']}")
        print(f"Techniques Used: {analysis['technique_variety']}")
        print(f"Technique Breakdown: {analysis['technique_counts']}")
        print(f"Advanced Technique Ratio: {analysis['advanced_ratio']:.1%}")
        print(f"Interaction Complexity: {analysis['interaction_complexity']:.2f}")
        print(f"Analysis: {analysis['analysis']}")
    else:
        print(f"Analysis: {analysis['analysis']}")


def print_summary_table(analyses: List[dict]):
    """Print summary table of multiple puzzle analyses."""
    print(f"\n{'File':<20} {'ID':<8} {'Size':<6} {'Stated':<8} {'Score':<6} {'Moves':<6} {'Analysis'}")
    print("-" * 80)
    
    for analysis in sorted(analyses, key=lambda x: x['difficulty_score']):
        file_name = os.path.basename(analysis['file'])[:18]
        puzzle_id = str(analysis['puzzle_id'])[:6]
        size = analysis['size'][:4]
        stated = analysis['stated_difficulty'][:6]
        score = f"{analysis['difficulty_score']}/10"
        moves = str(analysis.get('total_moves', 'N/A'))[:4] if analysis['solved'] else 'N/A'
        analysis_text = analysis['analysis'][:30]
        
        print(f"{file_name:<20} {puzzle_id:<8} {size:<6} {stated:<8} {score:<6} {moves:<6} {analysis_text}")


def export_to_csv(analyses: List[dict], output_file: str):
    """Export analysis results to CSV."""
    import csv
    
    fieldnames = [
        'file', 'puzzle_id', 'source_id', 'size', 'stated_difficulty',
        'difficulty_score', 'solved', 'total_moves', 'technique_variety',
        'complexity_score', 'advanced_ratio', 'interaction_complexity', 'analysis'
    ]
    
    try:
        with open(output_file, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for analysis in analyses:
                # Create row with only the fields we want
                row = {field: analysis.get(field, '') for field in fieldnames}
                writer.writerow(row)
        
        print(f"Exported results to {output_file}")
    except Exception as e:
        print(f"Error exporting to CSV: {e}", file=sys.stderr)


def main():
    """Parse arguments and rank puzzles."""
    parser = argparse.ArgumentParser(
        description='Rank Binairo puzzle difficulty using human-technique analysis'
    )
    parser.add_argument(
        'puzzle_files',
        nargs='+',
        help='Puzzle JSON files to analyze (supports glob patterns)'
    )
    parser.add_argument(
        '--detailed',
        action='store_true',
        help='Show detailed analysis for each puzzle'
    )
    parser.add_argument(
        '--human-metrics',
        action='store_true',
        help='Focus on human-cognitive difficulty metrics'
    )
    parser.add_argument(
        '--technique-breakdown',
        action='store_true',
        help='Show technique usage breakdown'
    )
    parser.add_argument(
        '--export-csv',
        type=str,
        help='Export results to CSV file'
    )
    parser.add_argument(
        '--sort-by',
        choices=['difficulty', 'moves', 'file'],
        default='difficulty',
        help='Sort results by specified criterion'
    )
    
    args = parser.parse_args()
    
    # Collect all puzzle files
    all_files = []
    for pattern in args.puzzle_files:
        if os.path.isfile(pattern):
            all_files.append(pattern)
        else:
            all_files.extend(glob.glob(pattern))
    
    if not all_files:
        print("No puzzle files found matching the specified patterns", file=sys.stderr)
        return 1
    
    print(f"Analyzing {len(all_files)} puzzle(s)...")
    
    # Analyze each puzzle
    analyses = []
    for file_path in all_files:
        analysis = rank_single_puzzle(file_path, args.detailed)
        if analysis:
            analyses.append(analysis)
            
            if args.detailed:
                print_detailed_analysis(analysis)
    
    if not analyses:
        print("No puzzles could be analyzed", file=sys.stderr)
        return 1
    
    # Print summary
    if len(analyses) > 1 and not args.detailed:
        print_summary_table(analyses)
    
    # Show aggregate stats if analyzing multiple puzzles
    if len(analyses) > 1:
        scores = [a['difficulty_score'] for a in analyses]
        avg_score = sum(scores) / len(scores)
        
        print(f"\nAggregate Statistics:")
        print(f"Puzzles analyzed: {len(analyses)}")
        print(f"Average difficulty: {avg_score:.1f}/10")
        print(f"Difficulty range: {min(scores)}-{max(scores)}")
        
        # Show technique frequency if requested
        if args.technique_breakdown:
            all_techniques = {}
            for analysis in analyses:
                if 'technique_counts' in analysis:
                    for tech, count in analysis['technique_counts'].items():
                        all_techniques[tech] = all_techniques.get(tech, 0) + count
            
            print(f"\nTechnique Usage Across All Puzzles:")
            for tech, count in sorted(all_techniques.items(), key=lambda x: x[1], reverse=True):
                print(f"  {tech}: {count} uses")
    
    # Export to CSV if requested
    if args.export_csv:
        export_to_csv(analyses, args.export_csv)
    
    return 0


if __name__ == '__main__':
    sys.exit(main())