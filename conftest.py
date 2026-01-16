# conftest.py
# Ignore modules that require heavyweight or non-core optional dependencies.
# These modules are not part of the core algorithm test suite and are excluded
# to ensure a reproducible evaluation platform.

collect_ignore = ["scripts"]

collect_ignore_glob = [
    "*qiskit*",
    "*quantum*",
    "*xgboost*",
    "*tensorflow*",
    "*keras*",
    "*rich*",
    "*bs4*",
]
