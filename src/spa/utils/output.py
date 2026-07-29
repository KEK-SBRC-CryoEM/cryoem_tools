import yaml
import json

from spa.utils import serialization

#### OUTPUT FILE ####
def print_and_save(output, print_as=None, filepath=None):
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
    serialization.setup_representer_yaml()
    result = {"yaml": yaml.safe_dump(output, sort_keys=False),
              "json": json.dumps(output, cls=serialization.NumpyEncoder, indent=2)
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
