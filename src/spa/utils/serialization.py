
import numpy as np
import json
import yaml

#### YAMl ####
def load_yaml(filepath):
    """
    Receives a filepath of a .yaml file and loads it as a dictionary
    """
    if filepath:
        with open(filepath, 'r') as yaml_file:
            return yaml.safe_load(yaml_file)
    return None

class YAMLDumper(yaml.SafeDumper):
    @classmethod
    def setup(cls):
        cls.add_representer(
            np.integer,
            lambda dumper, x: dumper.represent_int(x.item()))
        cls.add_representer(
            np.floating,
            lambda dumper, x: dumper.represent_float(x.item()))
        cls.add_representer(
            np.ndarray,
            lambda dumper, x: dumper.represent_sequence(
            "tag:yaml.org,2002:seq",
            x.tolist(),
            flow_style=True))

#### JSON ####
class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):  # np.int64 to int
            return int(obj)            
        if isinstance(obj, np.floating): # np.float64 to float
            return float(obj)    
        if isinstance(obj, np.ndarray):  # array to list
            return obj.tolist()  
        return super().default(obj)
    

YAMLDumper.setup()
