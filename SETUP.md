# Assignment #1: Mutation Adequacy Setup

This repository uses Docker to ensure the same
operating system, Python version, and dependencies when evaluating the
test suite and performing mutation analysis.

---

## System Requirements

- Docker

---

## Setup Instructions

### 1. Clone the repository

```bash
git clone https://github.com/michvong/Python.git
cd Python
```

### 2. Start the Docker container

```bash
docker run --rm -it \
  -v "$PWD":/work \
  -w /work \
  python:3.14-slim \
  bash
```

### 3. Activate virtual environment

```bash
python -m venv .venv
. .venv/bin/activate
```

### 4. Install dependencies

```bash
pip install -U pip
pip install -r requirements.lock.txt
```

### 5. Run the test suite

```bash
pytest -q
```
