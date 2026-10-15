"""
utils/data_loader.py
Memuat test data dari file JSON agar test terpisah dari data.
"""
import json
import os

DEFAULT_DATA_FILE = os.path.join(os.path.dirname(__file__), "..", "tests", "test_data.json")


def load_test_data(path: str = None) -> dict:
    file_path = os.path.abspath(path or DEFAULT_DATA_FILE)
    with open(file_path, encoding="utf-8") as f:
        return json.load(f)
