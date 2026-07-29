
import numpy as np
import json
import yaml

#### JSON ####
class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)      # np.int64   to int
        if isinstance(obj, np.floating):
            return float(obj)    # np.float64 to float
        if isinstance(obj, np.ndarray):
            return obj.tolist()  # array      to list
        return super().default(obj)

#### YAMl ####
def load_yaml(filepath):
    """
    Receives a filepath of a .yaml file and loads it as a dictionary
    """
    if filepath:
        with open(filepath, 'r') as yaml_file:
            return yaml.safe_load(yaml_file)
    return None

def setup_representer_yaml():
    yaml.SafeDumper.add_representer(np.int64, 
        lambda dumper, x: dumper.represent_int(x.item()))
    yaml.SafeDumper.add_representer(np.float64, 
        lambda dumper, x: dumper.represent_float(x.item()))    
    yaml.SafeDumper.add_representer(np.ndarray, 
        lambda dumper, x: dumper.represent_list(x.tolist()))
    