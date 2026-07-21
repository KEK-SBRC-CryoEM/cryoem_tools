import numpy as np
import yaml
import json

#### OUTPUT FILE ####
def print_and_save_output_file(output, print_as=None, filepath=None):
    """
    Receives a dictionary and 
    + converts it to YAML and JSON;
    + prints the requested format (skip if print_as is None); and
    + saves both formats to its respectively file.
    
    Parameters
    ----------
    output : dict
        The result data to be converted and saved.
    filepath : str, optional
        File path where the output will also be saved (without extension)

    return : dict
        {"yaml": output:dict converted to yaml,
         "json": output:dict converted to json}
    ------

    Example
    -------
    >>> result = {"accuracy": 0.92}
    >>> save_output_file(result, filepath="path/accuracy")
    """

    # conversion
    setup_representer_yaml()
    result = {"yaml": yaml.safe_dump(output, sort_keys=False),
              "json": json.dumps(output, cls=NumpyEncoder, indent=2)
    }

    # save
    if filepath:
        with open(filepath+".json", "w") as file:
            file.write(result["json"])

        with open(filepath+".yaml", "w") as file:
            file.write(result["yaml"])

    if print_as:
        print(result[print_as])

    return result

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