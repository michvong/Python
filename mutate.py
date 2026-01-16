#!/usr/bin/env python3

import argparse
import ast
import csv
import difflib
import random
import re
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple


# -----------------------------
# Mutation definitions
# -----------------------------


@dataclass(frozen=True)
class Mutation:
    """
    Represents one mutation applied at a specific location in the source file.

    This object is immutable (frozen=True) to prevent accidental modification
    after creation.

    Fields:
        operator (str): The mutation operator used (e.g., ROR, LCR, CRP).

        line_no (int): The line number in the source file where the mutation occurs.

        col_start (int): The column index where the mutation begins on the line (0-based).

        col_end (int): The column index where the mutation ends on the line (0-based).

        before (str): Exact substring in the original source code to be replaced.

        after (str): Replacement substring inserted by the mutation.
    """

    operator: str
    line_no: int
    col_start: int
    col_end: int
    before: str
    after: str


def _find_all_substrings(line: str, before: str):
    """
    Yields all occurrences of a substring in a line.

    Args:
        line (str): A single line of code.
        before (str): The substring to search for.

    Yields:
        Tuple[int, int]: (start_index, end_index) of each occurrence.

    This helper allows multiple mutation candidates per line.
    """
    start = 0
    while True:
        idx = line.find(before, start)
        if idx == -1:
            return
        yield idx, idx + len(before)
        start = idx + 1


def generate_mutation_candidates(lines: List[str]) -> List[Mutation]:
    """
    Scan the source file and generate a list of possible mutations.
    This function DOES NOT apply mutations.

    Mutation operators used:
        ROR (Relational Operator Replacement): == ↔ !=, < ↔ <=, > ↔ >=
        LCR (Logical Connector Replacement): and ↔ or
        CRP (Constant Replacement): 0 ↔ 1, -1 → 0
        AOR (Arithmetic Operator Replacement): - 1 ↔ + 1
        NMC (None-Check Mutation): is None ↔ is not None

    Args:
        lines (List[str]): List of lines from the original source file.

    Returns:
        List[Mutation]: A list of mutation candidates.
    """
    muts: List[Mutation] = []

    ror_map = {
        " == ": " != ",
        " != ": " == ",
        " <= ": " < ",
        " < ": " <= ",
        " >= ": " > ",
        " > ": " >= ",
    }
    lcr_map = {" and ": " or ", " or ": " and "}
    nmc_map = {" is None": " is not None", " is not None": " is None"}
    aor_map = {" - 1": " + 1", " + 1": " - 1"}
    int_pat = re.compile(r"(?<![\w.])(-?1|0|1)(?![\w.])")

    for i, line in enumerate(lines, start=1):

        for before, after in ror_map.items():
            for s, e in _find_all_substrings(line, before):
                muts.append(Mutation("ROR", i, s, e, before, after))

        for before, after in lcr_map.items():
            for s, e in _find_all_substrings(line, before):
                muts.append(Mutation("LCR", i, s, e, before, after))

        for before, after in nmc_map.items():
            for s, e in _find_all_substrings(line, before):
                muts.append(Mutation("NMC", i, s, e, before, after))

        for before, after in aor_map.items():
            for s, e in _find_all_substrings(line, before):
                muts.append(Mutation("AOR", i, s, e, before, after))

        for m in int_pat.finditer(line):
            tok = m.group(1)

            if tok == "0":
                rep = "1"
            elif tok == "1":
                rep = "0"
            elif tok == "-1":
                rep = "0"
            else:
                continue

            muts.append(Mutation("CRP", i, m.start(1), m.end(1), tok, rep))

    # Only store unique mutations
    uniq = {}
    for mu in muts:
        key = (mu.operator, mu.line_no, mu.col_start, mu.col_end, mu.before, mu.after)
        uniq[key] = mu

    return list(uniq.values())


def apply_mutation(lines: List[str], mu: Mutation) -> List[str]:
    """
    Apply a single mutation to the source file.

    Args:
        lines (List[str]): Original source file lines.
        mu (Mutation): Mutation to apply.

    Returns:
        List[str]: New list of lines with exactly one modification applied.

    Raises:
        ValueError: If the expected 'before' text is not found at the specified location.
    """
    new_lines = lines.copy()
    idx = mu.line_no - 1
    line = new_lines[idx]

    if line[mu.col_start : mu.col_end] != mu.before:
        raise ValueError("Mutation 'before' text not found at expected location")

    # (before mutation) + (mutated text) + (after mutation)
    new_lines[idx] = line[: mu.col_start] + mu.after + line[mu.col_end :]

    return new_lines


def unified_diff_u3(original: List[str], mutated: List[str], relpath: str) -> str:
    """
    Generate a unified diff with 3 lines of context.

    Args:
        original (List[str]): Original source file lines.
        mutated (List[str]): Mutated source file lines.
        relpath (str): Relative file path used in diff headers.

    Returns:
        str: Unified diff text with 3 lines of context.
    """
    diff = difflib.unified_diff(
        original,
        mutated,
        fromfile=f"a/{relpath}",
        tofile=f"b/{relpath}",
        lineterm="",
        n=3,
    )
    return "\n".join(diff) + "\n"


def _self_test() -> None:
    # Load a target file
    target = Path("data_structures/linked_list/circular_linked_list.py")
    text = target.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)

    # Generate candidates
    cands = generate_mutation_candidates(lines)
    print(f"Candidates found: {len(cands)}")
    assert len(cands) > 0

    # Apply the first candidate, ensure only one line changed
    mu = cands[0]
    mutated = apply_mutation(lines, mu)

    # Count changed lines
    changed = [i for i, (a, b) in enumerate(zip(lines, mutated), start=1) if a != b]
    print(f"Mutation: {mu.operator} at line {mu.line_no}, changed lines: {changed}")
    assert len(changed) == 1
    assert changed[0] == mu.line_no

    # Make a diff and ensure it contains headers
    d = unified_diff_u3(lines, mutated, str(target))
    assert d.startswith("--- a/")
    assert "+++ b/" in d
    assert "@@" in d
    print(d)
    print("Passed")


if __name__ == "__main__":
    _self_test()
