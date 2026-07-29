from pathlib import Path
from spa.utils.time import get_timestamp

def mkdir_numbered(base_path):
    """
    Creates a numbered directory (e.g., '000') under base_path.
    """
    if not base_path:
        return None

    base_dir = Path(base_path)
    
    for n in range(1000):
        final_dir = base_dir / f"{n:03d}"
        
        try:
            final_dir.mkdir(parents=True, exist_ok=False)
            return str(final_dir)
        except FileExistsError:
            continue

    # if somehow we hit folder 999+1...
    raise RuntimeError(f"Limit reached: please consider creating another base directory.")

def mkdir_timestamp(base_path):
    """
    Create a timestamped output directory under base_path.
    """
    if not base_path:
        return None
    
    final_dir = Path(base_path) / get_timestamp(True)
    Path(final_dir).mkdir(parents=True, exist_ok=True)

    return str(final_dir)

