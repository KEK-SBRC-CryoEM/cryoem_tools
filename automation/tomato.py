## temporary script for testing; need integration ##

import os
import logging
import argparse
import subprocess
from spa import utils
import json
import pickle
import postprocessing_rules

from pathlib import Path

### usage examples ###
# 1) all settings in one config yaml file
# python main.py -c config/all_settings_prews.yaml --verbose --debug
#  
# 2) settings split into multiple yaml files
# python main.py -c config/user_input_empiar10673_gpcr.yaml config/environment_settings_prews.yaml config/analyses_settings.yaml --verbose --debug
#
# 3) user input direct from CLI + every other settings in one config yaml file
# python main.py -c config/all_settings_prews.yaml -m "/home/tmoriya/shared_for_all/data/jair/EMPIAR10673_GPCR/PostProcess/job115/postprocess.mrc" -k "/home/tmoriya/shared_for_all/data/jair/autoparam/CS-Schemes/configs/common/config_em_settings_empiar10673_gpcr.yml" -n  "/home/tmoriya/shared_for_all/data/jair/autoparam/CS-Schemes/configs/common/config_sample_settings_empiar10673_gpcr.yml" --verbose --debug
#
# 4) user input direct from CLI + other settings split into multiple yaml files
# python main.py  config/environment_settings_prews.yaml  config/analyses_settings.yaml -m "/home/tmoriya/shared_for_all/data/jair/EMPIAR10673_GPCR/PostProcess/job115/postprocess.mrc" -k "/home/tmoriya/shared_for_all/data/jair/autoparam/CS-Schemes/configs/common/config_em_settings_empiar10673_gpcr.yml" -n  "/home/tmoriya/shared_for_all/data/jair/autoparam/CS-Schemes/configs/common/config_sample_settings_empiar10673_gpcr.yml" --verbose --debug
###

from pathlib import Path
__myname__ = Path(__file__).stem
logger = logging.getLogger(__myname__)

## input YAML processing ##
def load_settings(filepath_list):
    settings = {}
    for filepath in filepath_list:
        settings = settings | utils.serialization.load_yaml(filepath)

    return settings

def process_system_settings(settings):
    # check for missing env and script files
    env_notfound  = [(name, path)         for name, path in settings["env"].items()     if not Path(path).is_file()]
    tool_notfound = [(name, path["path"]) for name, path in settings["toolbox"].items() if not Path(path["path"]).is_file()]

    # write to log
    for (name,path) in env_notfound+tool_notfound:
        logger.warning(f"File not found!\t{name.upper()}:\t{path}")
    
    # link scripts to their executable
    for tool in settings["toolbox"]:
        exec_placeholder = settings["toolbox"][tool].get("env")
        if exec_placeholder: # if there is env, replace name by its filepath
            exec_path = settings["env"][exec_placeholder]
            settings["toolbox"][tool]["env"] = exec_path

    return settings["toolbox"]

def process_workflow_settings(settings):
    # from input file: workflow.{name, command,  command arg list}
    # then we add workflow.{invocation, output_dir, output}
    settings = {entry["name"]: {"command"       : entry["command"],
                                "args"          : entry["args"],
                                "postprocessing": entry.get("postprocessing", None),
                                "invocation"    : None, # derived from command and args
                                "output_dir"    : None, # basedir + name
                                "output"        : None,
                                # "output_original": a copy of the original output if any postprocessing rule was applied
                                }
                                                for entry in settings}

    # postprocessing: convert args from a list of dicts to a single dict
    # for entry in settings.values():
    #     for rule in entry["postprocessing"] or []:
    #         args = rule.get("args", None)
    #         if args:
    #             rule["args"] = {k: v for d in args for k, v in d.items()}

    return {"workflow": settings}

def process_user_inputs(settings):
    user        = {"user"           : settings.get("user",            {})}
    em_settings = {"em_settings"    : settings.get("em_settings",     {})}
    sp_settings = {"sample_settings": settings.get("sample_settings", {})}

    # load files if specified 
    # for repeated variables, the priority is for manual user inputs over the ones in the file
    if "em_settings_filepath" in user.keys():
        em_settings["em_settings"] = utils.load_yaml(settings["em_settings_filepath"])["Settings"] | em_settings["em_settings"]

    if "sample_settings_filepath" in user.keys():
        sp_settings["sample_settings"] = utils.load_yaml(settings["sample_settings_filepath"])["Settings"] | sp_settings["sample_settings"]
    
    return {"input": user|em_settings|sp_settings}

## preprocessing ##
def get_nested_value(path, data_dict):
    try:
        keys = path.split(".")
        # descend
        next_ = data_dict
        for k in keys:
            next_ = next_[k]
        return next_

    except (KeyError, TypeError):
        return None

def substitute_placeholders(text, context):
    for pattern, value in context.items():
        text = text.replace(pattern, value)
    return text

def resolve_value(value, data_dict, str_context):
    # regular input; replaces directories
    if isinstance(value, str):
        result  = substitute_placeholders(value, str_context)
    # input comes from an analysis
    elif isinstance(value, dict):
        result = get_nested_value(value["from"], data_dict)

        # result not available, use default
        if result is None:
            result = value.get("default", None)
            logger.warning(f"VALUE NOT FOUND: {value['from']}!")
            logger.warning(f"+ DEFAULTING TO {result}.")

            # the obtained default value is still None
            if result is None: 
                logger.warning(f"+ THIS MAY CAUSE SOME COMMANDS TO FAIL!")
    # other datatype (eg numbers)
    else: 
        result = value
    
    return result

def parse_callable_arglist(args, workflow_data, str_context):
    result = {}
    for arg in args:
        # each arg is always {name:value}
        key, value = next(iter(arg.items()))
        resolved = resolve_value(value, workflow_data, str_context)
        result[key] = resolved
            
    return result

def parse_subprocess_arglist(args, workflow_data, str_context):
    result = []
    for arg in args:
        # each arg is 1) flag:str or 2) {flag,value}:dict or 3) {value}:dict
        ## 1) str : return the flag as is
        ## 2) dict: return flag, resolved value
        ## 3) dict: return resolved value
        if isinstance(arg, dict):
            key, value = next(iter(arg.items()))
            # flag and value
            if key.startswith("-"):
                resolved = resolve_value(value, workflow_data, str_context)
                value    = [key, str(resolved)]
            # value only (dict)
            else:
                resolved = resolve_value(arg, workflow_data)
                value    = [str(resolved)]
        # default value
        else:
            value = [str(arg)]
        
        result.extend(value)
    return result

def make_command(env, cmd_path, args):
    cmd = [env, cmd_path] if env else [cmd_path]
    cmd.extend(args)
    return cmd

## pipeline ##
def run_subprocess(name, invocation, output_directory=None):
    try: 
        result = subprocess.run(invocation, capture_output=True, text=True, encoding="utf-8")
        # note: important attributes from subprocess: stdout, stderr, returncode
        
        if output_directory:
            with open(os.path.join(output_directory, "out.txt"), "w") as f:
                f.write(result.stdout)

            with open(os.path.join(output_directory, "run.log"), "w") as f:
                f.write(result.stderr)
                f.write(f"\nexit code: {result.returncode}\n")
    
        # ensure it run successfully
        result.check_returncode()
    except subprocess.CalledProcessError:
        logger.error(f"Pipeline Crashed while running {name.upper()} with return code {result.returncode}!!")
        logger.error("+ Current analysis failed to run. Please, check its log file and the message below.")
        # logger.error(f"{result.stderr}")
        raise

    try: # parse output and return result
        result = json.loads(result.stdout)
    except (AttributeError, TypeError, json.JSONDecodeError):
        # not json, return result as is
        result = result.stdout
    return result

def run(workflow_data, toolbox_settings, basedir, debug=False):
    # For each entry in the workflow
    for name, entry in workflow_data["workflow"].items():
        # 1. Prepare environment
        logger.info(f"{name.upper()}")

        ## 1.1 output directory path
        entry["output_dir"] = os.path.join(basedir, name)
        Path(entry["output_dir"]).mkdir(parents=True, exist_ok=True)
        logger.info("+ Output Directory  : " + entry["output_dir"])

        ## 1.2 prepare context
        ctx = {"$OUTDIR": entry["output_dir"], "$BASEDIR":basedir}

        # 2. Subprocess
        ## 2.1 resolve args
        resolved_args = parse_subprocess_arglist(args=entry["args"], 
                                                 workflow_data=workflow_data, 
                                                 str_context=ctx)                                      

        ## 2.2 get script name
        cmd_name = entry["command"]
        
        ## 2.3 prepare invocation
        entry["invocation"] = make_command(env      = toolbox_settings[cmd_name].get("env"), 
                                           cmd_path = toolbox_settings[cmd_name]["path"], 
                                           args     = resolved_args)
        logger.info("+ Invocation Command: " + " ".join(entry["invocation"]))

        ## 2.4 run
        logger.info(f"Running...")
        entry["output"] = run_subprocess(name, entry["invocation"], entry["output_dir"])
        logger.info(f"+ Output: {entry['output']}")

        # 3. Postprocessing rules
        if entry["postprocessing"]:
            logger.info(f"Postprocessing...")
            entry["output_original"] = entry["output"]
            logger.info(f"+ Moving original  output to: 'workflow.{name}.output_original'")
            logger.info(f"+ Saving processed output to: 'workflow.{name}.output'")
            
            for rule in entry["postprocessing"]:
                logger.info(f"+ Applying '{rule['method']}' to '{rule['target']}'")
                ## 3.1 get callable
                method = getattr(postprocessing_rules, rule["method"])

                ## 3.2 solve syntax sugar for self.target
                target_temp = {"self": {"target":entry['output'][rule['target']]}}

                ## 3.3 parse arguments
                resolved_args = parse_callable_arglist(args=rule["args"], 
                                                    workflow_data=workflow_data|target_temp, 
                                                    str_context=ctx) 
            
                ## 3.4 call
                entry["output"][rule['target']] = method(**resolved_args)
                logger.info(f"+ := {entry['output'][rule['target']]}")

        logger.info("Done!")
        logger.info("-"*40)        

        # save state data for debugging
        if debug:
            with open(os.path.join(basedir, "pipeline_data.pkl"), "wb") as file:
                pickle.dump(workflow_data, file)

        # save state data (future: this will be used to stop/continue the workflow)
        utils.handle_output(workflow_data, 
                            to_json=True, 
                            filename=os.path.join(basedir, "pipeline_data.json"),
                            show=False)

    return workflow_data

def css_run(css_settings, workflow_data, basedir, debug=False):
    logger.info("CS-Schemes:".upper())
    logger.info("+ Preparing to extrat parameters")
    css_result = {}
    ctx = {"$BASEDIR": basedir}
    for name, content in css_settings.items():
        logger.info(f"{name.upper()}")

        # run a callable to get the result
        if isinstance(content, dict) and content.get("methods", None):
            for entry in content["methods"]:
                logger.info(f"+ Calling '{entry['name']}...'")

                ## 3.1 get callable
                method = getattr(postprocessing_rules, entry['name'])

                ## 3.3 parse arguments
                css_ctx = css_result|{"self":css_result.get(name, None)}

                resolved_args = parse_callable_arglist(args=entry["args"], 
                                                        workflow_data=workflow_data|css_ctx, 
                                                        str_context=ctx)

                ## 3.4 call
                css_result[name] = method(**resolved_args)
        # lookup
        elif isinstance(content, dict) or isinstance(content, str):
            css_result[name] = resolve_value(content, workflow_data|css_result, ctx)
        # value itself
        else:
            css_result[name] = content

        # show output
        logger.info(f"\t\t := {css_result[name]}")

        # save state data for debugging
        if debug:
            with open(os.path.join(basedir, "css_data.pkl"), "wb") as file:
                pickle.dump(css_result, file)

        # final output
        utils.handle_output(css_result, 
                            to_json=False, 
                            filename=os.path.join(basedir, "csschemes_sample.yaml"),
                            show=False)

    return css_result

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--config_filepath_list", nargs='+', required=True, help="Path to one or more configuration files (yaml).")
    # alternatively receive user inputs from CLI
    parser.add_argument("-m",  "--reference_map",   type=str, help="Path to the reference map (mrc).")
    parser.add_argument("-k",  "--em_settings",     type=str, help="Path to the CS-Schemes EM Settings files (yaml).")
    parser.add_argument("-n",  "--sample_settings", type=str, help="Path to the CS-Schemes Sample Settings files (yaml).")
    parser = utils.cli.add_common_arguments(parser) # adds --verbose, --json, --output-dir --debug
    args = parser.parse_args()

    # Directory creation
    basedir = utils.paths.mkdir_timestamp(args.output_dir or ".") # skip if args.output_dir is None

    # Logging
    utils.log.configure_logging(verbose=args.verbose, output_directory=basedir, capture_warnings=True)

    # Input files handling
    settings = load_settings(args.config_filepath_list)

    # CLI handling
    if "input" not in settings.keys():
        settings["input"] = {"user": {}}
    if args.reference_map:
        settings["input"]["user"]["reference_map_filepath"]   = args.reference_map
    if args.em_settings:
        settings["input"]["user"]["em_settings_filepath"]     = args.em_settings
    if args.sample_settings:
        settings["input"]["user"]["sample_settings_filepath"] = args.sample_settings
    
    missing_settings = [ft for ft in ["input", "workflow", "system"] if ft not in settings.keys()] # todo: possibly could check subsections
    if missing_settings:
        logger.error("Check your inputs. The following settings are missing: "+" ".join(missing_settings))
        raise Exception("Missing input settings. Expected 'input', 'workflow', and 'system' sections") 

    if args.debug:
        logger.info("DEBUG MODE ON: ")
        logger.info("+ saves and updates pipeline_data.pkl during execution.")
        logger.info("+ shows error stack in case of an exception.")
        logger.info("-"*40)
    logger.info(f"Output directory: {basedir}")
    logger.info(f"Verbose: {args.verbose}")
    logger.info("-"*40)
    for i, f in enumerate(args.config_filepath_list):
        logger.info(f"Config file #{i+1}: {f}")
    logger.info("-"*40)
    logger.info("Reference MAP:              " + settings["input"]["user"].get("reference_map_filepath",   "None"))
    logger.info("CS-Schemes EM Settings:     " + settings["input"]["user"].get("em_settings_filepath",     "None"))
    logger.info("CS-Schemes Sample Settings: " + settings["input"]["user"].get("sample_settings_filepath", "None"))
    logger.info("-"*40)

    try:
        # prepare and run all analyses
        workflow_result = run(workflow_data    = process_user_inputs(settings["input"]) | process_workflow_settings(settings["workflow"]),
                              toolbox_settings = process_system_settings(settings["system"]),
                              basedir          = basedir,
                              debug            = args.debug)

        # evaluate the cs-schemes parameters
        workflow_result = css_run(settings.get("css", {}), 
                                  workflow_data = workflow_result, 
                                  basedir       = basedir,
                                  debug         = args.debug)
    except Exception:
        # if DEBUG: capture the error stack
        logger.error("Pipeline Crashed!!".upper(), exc_info=args.debug)
        


    