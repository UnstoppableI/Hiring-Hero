#!/usr/bin/env python3
"""
Redrob Hackathon - Intelligent Candidate Discovery & Ranking
Main Entry Point

Usage:
    python hackathon_rank.py --candidates ./candidates.json --out ./submission.csv

Constraints:
    - CPU only (no GPU)
    - < 5 minutes runtime
    - < 16 GB RAM
    - No network access during ranking
    - Ranks 100 top candidates from input pool
"""

import json
import argparse
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

from hackathon_scoring_engine import ScoringEngine
from hackathon_ranker_utils import load_candidates_from_json, validate_candidate_schema


def parse_arguments():
    """Parse command-line arguments"""
    parser = argparse.ArgumentParser(
        description="Rank candidates for Senior AI Engineer role"
    )
    parser.add_argument(
        "--candidates",
        type=str,
        required=True,
        help="Path to candidates JSON file (or .jsonl)"
    )
    parser.add_argument(
        "--out",
        type=str,
        default="submission.csv",
        help="Output CSV file path (default: submission.csv)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output"
    )
    return parser.parse_args()


def load_candidates(filepath: str) -> List[Dict[str, Any]]:
    """
    Load candidates from JSON or JSONL file.
    Supports both single JSON array and JSONL (one JSON per line).
    """
    filepath = Path(filepath)
    
    if not filepath.exists():
        raise FileNotFoundError(f"Candidates file not found: {filepath}")
    
    candidates = []
    
    if filepath.suffix == ".jsonl":
        # Load JSONL format (one JSON object per line)
        with open(filepath, 'r') as f:
            for line_num, line in enumerate(f, 1):
                if line.strip():
                    try:
                        candidate = json.loads(line)
                        if validate_candidate_schema(candidate):
                            candidates.append(candidate)
                    except json.JSONDecodeError as e:
                        print(f"Warning: Could not parse line {line_num}: {e}")
    else:
        # Load JSON array format
        candidates = load_candidates_from_json(filepath)
    
    return candidates


def validate_submission(csv_content: str, num_candidates: int) -> bool:
    """
    Validate submission CSV format.
    Must have exactly 100 rows (plus header), with proper format.
    """
    lines = csv_content.strip().split('\n')
    
    # Check header
    if lines[0] != "candidate_id,rank,score,reasoning":
        print(f"Error: Invalid CSV header. Got: {lines[0]}")
        return False
    
    # Check number of candidates (should be exactly 100 or less than input)
    data_lines = len(lines) - 1
    if data_lines > min(100, num_candidates):
        print(f"Error: Too many candidates in output ({data_lines}), max is 100")
        return False
    
    # Validate each line
    ranks_seen = set()
    for i, line in enumerate(lines[1:], 1):
        parts = line.split(',', 3)  # Split on first 3 commas only (reasoning may have commas)
        if len(parts) < 4:
            print(f"Error: Line {i+1} has invalid format: {line}")
            return False
        
        candidate_id, rank, score, reasoning = parts
        
        # Validate rank
        try:
            rank_int = int(rank)
            if rank_int < 1 or rank_int > 100:
                print(f"Error: Invalid rank {rank} on line {i+1}")
                return False
            if rank_int in ranks_seen:
                print(f"Error: Duplicate rank {rank} on line {i+1}")
                return False
            ranks_seen.add(rank_int)
        except ValueError:
            print(f"Error: Invalid rank '{rank}' on line {i+1}")
            return False
        
        # Validate score
        try:
            score_float = float(score)
            if score_float < 0 or score_float > 1:
                print(f"Error: Score {score} out of range [0, 1] on line {i+1}")
                return False
        except ValueError:
            print(f"Error: Invalid score '{score}' on line {i+1}")
            return False
        
        # Validate candidate_id format
        if not candidate_id.startswith("CAND_"):
            print(f"Error: Invalid candidate_id '{candidate_id}' on line {i+1}")
            return False
    
    return True


def main():
    """Main entry point"""
    args = parse_arguments()
    
    start_time = datetime.now()
    
    try:
        # Load candidates
        if args.verbose:
            print(f"Loading candidates from {args.candidates}...")
        
        candidates = load_candidates(args.candidates)
        
        if not candidates:
            print("Error: No valid candidates loaded")
            return 1
        
        if args.verbose:
            print(f"Loaded {len(candidates)} candidates")
        
        # Initialize scoring engine
        engine = ScoringEngine()
        
        # Rank candidates
        if args.verbose:
            print("Ranking candidates...")
        
        ranked = engine.rank_candidates(candidates)
        
        if args.verbose:
            print(f"Ranked {len(ranked)} candidates")
            top_5 = ranked[:5]
            print("\nTop 5 candidates:")
            for i, cand in enumerate(top_5, 1):
                print(f"  {i}. {cand['candidate_id']}: {cand['score']:.4f}")
        
        # Generate submission CSV
        csv_output = engine.generate_submission_csv(ranked)
        
        # Validate submission format
        if not validate_submission(csv_output, len(candidates)):
            print("Error: Generated submission failed validation")
            return 1
        
        # Write to output file
        output_path = Path(args.out)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            f.write(csv_output)
        
        elapsed = (datetime.now() - start_time).total_seconds()
        
        if args.verbose:
            print(f"\nSuccess! Submission written to {args.out}")
            print(f"Total time: {elapsed:.2f} seconds")
        else:
            print(f"Success: Ranked {len(ranked)} candidates in {elapsed:.2f}s")
            print(f"Output: {args.out}")
        
        return 0
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
