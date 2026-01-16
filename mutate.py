#!/usr/bin/env python3
from __future__ import annotations

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
        operator (str):
            The mutation operator used (e.g., ROR, LCR, CRP).

        line_no (int):
            The line number in the source file where the mutation occurs.

        col_start (int):
            The column index where the mutation begins on the line (0-based).

        col_end (int):
            The column index where the mutation ends on the line (0-based).

        before (str):
            Exact substring in the original source code to be replaced.

        after (str):
            Replacement substring inserted by the mutation.
    """

    operator: str
    line_no: int
    col_start: int
    col_end: int
    before: str
    after: str
