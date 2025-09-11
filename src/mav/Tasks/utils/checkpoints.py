import os
import json
import pickle
from typing import Any, Dict, Optional


def ensure_parent_dir(file_path: str) -> None:
	"""Ensure the parent directory for file_path exists."""
	parent = os.path.dirname(file_path)
	if parent:
		os.makedirs(parent, exist_ok=True)


# -------------------- Index-based checkpoints (int) --------------------

def load_checkpoint_index(chk_file: str) -> int:
	"""Load a numeric index checkpoint from a text file. Returns 0 if missing."""
	try:
		with open(chk_file, "r") as f:
			value = f.read().strip()
			return int(value) if value else 0
	except FileNotFoundError:
		return 0
	except Exception:
		return 0


def save_checkpoint_index(index: int, chk_file: str) -> None:
	"""Save a numeric index checkpoint to a text file."""
	ensure_parent_dir(chk_file)
	with open(chk_file, "w") as f:
		f.write(str(index))


# -------------------- JSON-based checkpoints (dict) --------------------

def load_checkpoint_json(chk_file: str) -> Dict[str, Any]:
	"""Load a JSON checkpoint dict. Returns empty dict if missing or invalid."""
	try:
		with open(chk_file, "r") as f:
			return json.load(f)
	except (FileNotFoundError, ValueError, json.JSONDecodeError):
		return {}


def save_checkpoint_json(data: Dict[str, Any], chk_file: str) -> None:
	"""Save a JSON checkpoint dict to file."""
	ensure_parent_dir(chk_file)
	with open(chk_file, "w") as f:
		json.dump(data, f, indent=2)


# -------------------- Pickle-based checkpoints (any object) --------------------

def load_checkpoint_pickle(chk_file: str) -> Optional[Any]:
	"""Load a pickle checkpoint. Returns None if missing or invalid."""
	try:
		with open(chk_file, "rb") as f:
			return pickle.load(f)
	except Exception:
		return None


def save_checkpoint_pickle(obj: Any, chk_file: str) -> None:
	"""Save an object checkpoint using pickle."""
	ensure_parent_dir(chk_file)
	with open(chk_file, "wb") as f:
		pickle.dump(obj, f)


# -------------------- Composite save (checkpoint + records) --------------------

def save_checkpoint_and_records(checkpoint_data: Dict[str, Any], chk_file: str,
								  records: Any, save_file: str) -> bool:
	"""Save checkpoint (JSON) and records (JSON) together. Returns True on success."""
	try:
		ensure_parent_dir(chk_file)
		ensure_parent_dir(save_file)
		with open(chk_file, 'w') as cf:
			json.dump(checkpoint_data, cf, indent=2)
		with open(save_file, 'w') as rf:
			json.dump(records, rf, indent=2)
		return True
	except Exception:
		return False
