# synesthesia_eval

Evaluation framework for the SYNESTHESIA psychoacoustic visualization system.

## Setup

```bash
python3 -m venv synesthesia_eval/.venv
source synesthesia_eval/.venv/bin/activate
pip install cython numpy
pip install -r synesthesia_eval/requirements.txt
pip install --no-build-isolation madmom
pip install pytest
```

## Project Structure

```
synesthesia_eval/
├── __init__.py
├── requirements.txt
├── README.md
├── models/          # Model checkpoints and configs
├── data/            # Evaluation datasets
├── outputs/         # Evaluation results
└── tests/
    └── test_imports.py
```

## Running Tests

```bash
source synesthesia_eval/.venv/bin/activate
python -m pytest synesthesia_eval/tests/ -v
```

## Known Issues

- **madmom**: Incompatible with Python 3.10+ (`collections.MutableSequence` removed). Use Python 3.9 if madmom is required.
