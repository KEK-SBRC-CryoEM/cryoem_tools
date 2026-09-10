from pathlib import Path
from spa.utils.time import get_timestamp
from functools import partial

def get_numbered_suffix(path:str) -> str|None:
    """
    Return a numbered suffix for directory creation (e.g., '000').
    Returns None if the limit (999) is reached.
    """
    for n in range(1000):
        suffix = f"{n:03d}"

        if not Path(path+suffix).exists():
            return suffix

    # if somehow we hit folder 999+1...
    return None

def mkdir_output(path:str, mode:str="timestamp", sep:str="_") -> str|None:
    """
    Create the output directory and return f"{path}{sep}{suffix}":str.
    If 'path' already exists, it appends a string determined by 'mode'.
    Available modes:
        - number : from 000 to 999 
        - timestamp: %Y-%m-%d_%H-%M-%S
    """
    get_suffix = {
        "number" : get_numbered_suffix,
        "timestamp": lambda _: get_timestamp(file_format=True),
    }

    if not path:
        return None
    
    final_path = Path(path)
    if final_path.exists():
        if mode not in get_suffix:
            raise ValueError(f"Invalid mode '{mode}'. Available modes: {list(get_suffix.keys())}")
        
        final_path = Path(str(final_path)+sep)
        suffix = get_suffix[mode](str(final_path))
        
        if suffix:
            final_path = final_path.parent / f"{final_path.name}{suffix}"
        else:
            raise RuntimeError(f"Failed to generate a valid '{mode}' suffix for {final_path}")
        
    final_path.mkdir(parents=True, exist_ok=False)
    return str(final_path)
