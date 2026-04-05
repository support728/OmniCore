import json
from pathlib import Path
from typing import Any, Dict


MEMORY_FILE = Path("memory.json")


def load_all() -> Dict[str, Any]:
	"""Load and return all saved memory entries as a dictionary."""
	if not MEMORY_FILE.exists():
		return {}

	try:
		with MEMORY_FILE.open("r", encoding="utf-8") as file:
			data = json.load(file)
		return data if isinstance(data, dict) else {}
	except (json.JSONDecodeError, OSError):
		return {}


def save_memory(key: str, value: Any) -> None:
	"""Save a single key/value pair into memory.json."""
	data = load_all()
	data[str(key)] = value
	with MEMORY_FILE.open("w", encoding="utf-8") as file:
		json.dump(data, file, indent=2, ensure_ascii=True)


def get_memory(key: str) -> Any:
	"""Get a saved value by key. Returns None when missing."""
	data = load_all()
	return data.get(str(key))
