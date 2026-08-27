from fractions import Fraction
import os
import logging
import argparse
from pathlib import Path
from matplotlib.colors import ListedColormap
import pandas as pd
import numpy as np
from collections import Counter

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from spa import utils, box
from spa.utils import numbers

__myname__ = Path(__file__).stem
logger = logging.getLogger(__myname__)

# note: compute_pareto_front and plot_pareto are quite general
#       if we end up needing to reuse these functions, it is better to move them to another package

# Auxiliary methods for assessing prime-factors in the EMAN2 box-size list
def summarize_prime_factor_classes(sizes):
    counts = Counter(
        numbers.prime_factors(n)
        for n in sizes
    )
    return dict(sorted(counts.items(), key=lambda x: x[1], reverse=True))

def _summarize():
    logger.info("Assessing prime-factor groups in the EMAN2 box-size list.")
    counts = summarize_prime_factor_classes(box.FFT_FRIENDLY_SIZES)
    output = utils.output.print_and_save(counts, print_as="yaml", filepath=None)
    logger.info(f"Result:\n{output['yaml']}")
    # output: primes in the EMAN2 list are (2,3,5,7,11,13)
# /

def compute_pareto_front(objectives):
    """
    Return the indices of the Pareto-optimal points for minimization.
    Retain duplicated points.
    """
    # start with every solution on the pareto front
    is_pareto = np.ones(len(objectives), dtype=bool)

    for i, candidate in enumerate(objectives):
        if not is_pareto[i]: # skip solutions that we already found to be dominated
            continue

        # get the indices of all solutions still considered pareto
        active = np.flatnonzero(is_pareto)

        # determine solutions dominated by candidate:
        ## candidate <= solution in every objective
        ## candidate < solution in at least one objective
        dominates = (
            np.all(candidate <= objectives[active], axis=1)
            & np.any(candidate < objectives[active], axis=1)
        )

        is_pareto[active[dominates]] = False

    return np.flatnonzero(is_pareto)

def plot_pareto(solutions, all_solutions=False, feasible_solutions=False, 
        x_label="", y_label="", title_str="", subtitle_str="", legend_str="",
        all_solutions_label="", feasible_solutions_label="", pareto_labels=None,
        filepath=None):
    """
    Plot a 2D Pareto from a pandas dataframe.

    Parameters
    ----------
    solutions : pandas.DataFrame
        Dataframe containing:
            ``obj1``  : objective values to be plotted along the x-axis
            ``obj2``  : objective values to be plotted along the y-axis
            ``is_feasible`` : (booleans) feasibility indicator
            ``pareto``: (ints) Pareto level, where 0 denotes a non-Pareto solution
            and values greater than 0 identify Pareto solutions or categories (eg: soft constraints)

    all_solutions : bool, default=False
        Plot all candidate solutions as a faint background cloud.

    feasible_solutions : bool, default=False
        Plot feasible solutions.

    x_label, y_label : str, optional
        Labels for the x- and y-axes.

    title_str, subtitle_str, legend_str : str, optional
        Plot title, subtitle, and legend text.

    all_solutions_label, feasible_solutions_label : str, optional
        Legend labels for the corresponding solution sets.

    pareto_labels : optional
        Labels used for the Pareto solution categories.

    filepath : str or pathlib.Path, optional
        Path to save the figure. If None, the figure is not saved.
    """
        
    fig, ax = plt.subplots(figsize=(8, 6))

    # plot ALL solutions
    if all_solutions:
        ax.scatter(solutions["obj1"],
                   solutions["obj2"],
                   facecolors='lightgray', edgecolors='lightgray', s=50, label=all_solutions_label)
    
    # plot all FEASIBLE solutions
    if feasible_solutions:
        ax.scatter(solutions[solutions["is_feasible"]]["obj1"], 
                   solutions[solutions["is_feasible"]]["obj2"], 
                   facecolors='gray', edgecolors='gray', s=50, label=feasible_solutions_label)

    # plot PARETO solutions
    pareto_levels = solutions[solutions["pareto"]>0]["pareto"].unique() # 0: not pareto
    cmap = plt.get_cmap('tab10') #alternative coloring 'viridis'
    tab10_red = ListedColormap(np.roll(cmap.colors, -3, axis=0), name="tab10_red") # red as first color

    for i in pareto_levels:
        _pareto = solutions[solutions["pareto"]==i]
        ax.scatter(_pareto["obj1"], _pareto["obj2"], color=tab10_red(i-1), s=50, edgecolors='none', label=pareto_labels[i-1])
    
    # text and labels
    ax.text(0.5, 0.90, f"{subtitle_str}", 
            horizontalalignment='center', verticalalignment='center', multialignment='left', transform=ax.transAxes, 
            fontsize=8, color='black')
    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    ax.set_title(title_str)
    ax.legend(title=legend_str, loc="best")


    if filepath:
        plt.savefig(filepath, dpi=300)
    return ax

def find_binning_parameters(target_resolution_A, pixel_size_A_per_pixel, sampling_factor, 
                            evaluation_boxes,
                            evaluation_feasible_primes,
                            step=1e-6, search_radius_A=1.5):
    # guarantees it is a np.array
    evaluation_boxes = np.asarray(evaluation_boxes)

    ### search grid ###
    start = target_resolution_A + search_radius_A
    end   = target_resolution_A - search_radius_A
    search_range =  int((start - end)/step) + 1

    ### candidate solutions ###
    candidate_resolutions = np.array([Fraction(str(start)) - i * Fraction(str(step)) for i in range(search_range)])
    candidate_binnings    = np.array([r/(Fraction(str(pixel_size_A_per_pixel))*sampling_factor) for r in candidate_resolutions])
    candidate_pixel_sizes = [Fraction(str(b*pixel_size_A_per_pixel)) for b in candidate_binnings]
    
    ### evaluation ###
    # objective 1: number of decimals in the pixel size
    n_decimals_pixel   = np.array([numbers.decimal_places_for_fraction(p.denominator) for p in candidate_pixel_sizes])

    # objective 2: amount of change in the target resolution
    d_resolution         = np.abs(target_resolution_A - candidate_resolutions)
    is_worse_than_target = candidate_resolutions > target_resolution_A # sign direction of objective 2

    # objective 3: box compatibility
    # evaluate only feasibile solutions (evaluated after feasibility check)

    ### constraints ###
    # constraint 1: solutions with prime factors in the group
    has_prime_factor = [numbers.has_allowed_prime_factors(b.denominator, allowed_primes=evaluation_feasible_primes) for b in candidate_binnings]

    # constraint 2: no infinite decimals in the binning factor
    n_decimals_binning = np.array([numbers.decimal_places_for_fraction(b.denominator) for b in candidate_binnings])
    finite_decimals_binning = n_decimals_binning!=np.inf
    
    # constraint 3: no infinite decimals in the pixel size
    finite_decimals_pixel   = n_decimals_pixel!=np.inf

    # merge feasibility
    mask_feasible  = has_prime_factor & finite_decimals_binning & finite_decimals_pixel

    ### evaluation objective 3  ###
    # test compatibility of each feasible binning vs each box
    _false = np.full(len(evaluation_boxes), False)
    compatible_boxes_mask  = np.array([((b*evaluation_boxes)%2)==0 if m else _false for b, m in zip(candidate_binnings, mask_feasible)])
    # minimization -> 0:compatible, 1:incompatible
    incompatibility_mask     = np.array([(~m).astype(int) for m in compatible_boxes_mask])
    count_compatible_boxes = compatible_boxes_mask.sum(axis=1)
    

    # update feasiblity for the rare case a candidate binning has no compatible box
    mask_feasible &= (count_compatible_boxes>0)
    # result
    history = pd.DataFrame({# decision variable
                            "binning_factor"          : candidate_binnings,
                            # consequences of the decision variable
                            "binned_pixel_size"       : candidate_pixel_sizes,
                            "target_resolution"       : candidate_resolutions,
                            # constraints
                            "has_prime_factor"        : has_prime_factor, 
                            "has_finite_binning"      : finite_decimals_binning, 
                            "has_finite_pixel"        : finite_decimals_pixel, 
                            "count_compatible_boxes"  : count_compatible_boxes,
                            "is_feasible"             : mask_feasible,
                            # objectives
                            "n_decimals_pixel"        : n_decimals_pixel, 
                            "d_resolution"            : d_resolution,
                            "incompatible_boxes"      : list(incompatibility_mask),
                            # additional information
                            "n_decimals_binning"      : n_decimals_binning, 
                            "is_worse_than_target"    : is_worse_than_target,
    })
    
    return history

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    # required
    parser.add_argument("-p", "--pixel_size"       , type=float, required=True, help="Current Pixel Size")
    parser.add_argument("-t", "--target_resolution", type=float, required=True, help="Target Resolution")
    # optionals
    parser.add_argument("--sampling_factor", type=float, default=3,    help="Nyquist: 2. Oversampling >2")
    parser.add_argument("--search_radius_A", type=float, default=0.2,  help="Range around the target resolution to search [Å].")
    parser.add_argument("--search_step",     type=float, default=1e-6, help="Step size between candidate resolutions [Å].")
    parser = utils.cli.add_common_arguments(parser) # adds --verbose, --json, --output-dir --debug
    args = parser.parse_args()

    # directory creation
    basedir = utils.paths.mkdir_timestamp(args.output_dir) # skip if args.output_dir is None

    # logging
    utils.log.configure_logging(verbose=args.verbose, output_directory=basedir, capture_warnings=True)

    # print log header
    if args.verbose:
        utils.cli.log_cli_header(logger=logger, script_name=__myname__, args=args)

    # computation
    logger.info("Exhaustive evaluation of binning parameters...")
    history = find_binning_parameters(target_resolution_A        = args.target_resolution, 
                                      pixel_size_A_per_pixel     = args.pixel_size, 
                                      sampling_factor            = args.sampling_factor,
                                      evaluation_boxes           = box.FFT_FRIENDLY_SIZES,
                                      evaluation_feasible_primes = (2, 3, 5, 7, 11, 13),
                                      step                       = args.search_step, 
                                      search_radius_A            = args.search_radius_A)
    logger.info(f"+ Total candidates  : {len(history)}")
    logger.info("Checking feasibility...")
    _count = (~history["has_prime_factor"]).sum()
    logger.info(f"+ Filtering in  candidates with prime factors ≤ 13     : {_count}")
    _count = (history["has_prime_factor"] & ~(history["has_finite_binning"] & history["has_finite_pixel"])).sum()
    logger.info(f"+ Filtering out candidates with infinite decimal places: {_count}")
    _count = (history["has_prime_factor"] & history["has_finite_binning"] & history["has_finite_pixel"] & (history["count_compatible_boxes"]==0)).sum()
    logger.info(f"+ Filtering out candidates with no box compatibility   : {_count}")
    logger.info(f"+ Feasible solutions: {len(history[history['is_feasible']])}")
    if basedir and args.debug: # may generate heavy file
        filepath = os.path.join(basedir, f"history_{args.pixel_size}ÅperPixel_{args.target_resolution}Å.csv")
        history.to_csv(filepath, index=False)
        logger.info(f"+ Search evaluation saved to {filepath}")

    logger.info("Computing pareto front...")
    logger.info("+ Minimizing number of decimal places in the resulting binned pixel size...")
    logger.info("+ Maximizing compatibility between binning factor and EMAN2 box...")

    # compute pareto
    mask = history["is_feasible"]
    objectives = np.column_stack([history[mask]["n_decimals_pixel"].to_numpy(), 
                                  #history["is_feasible"]["d_resolution"].to_numpy(), 
                                  history[mask]["incompatible_boxes"].to_list(),
    ])
    pareto_idx_group = compute_pareto_front(objectives)

    # update history
    history["pareto"] = 0
    history.loc[history.index[mask][pareto_idx_group], "pareto"] = 1
    logger.info(f"+ Non-dominated solutions: {len(history[history['pareto']>0])}")

    # filter pareto only for output
    _view = history[history["pareto"]>0].sort_values(by=["n_decimals_pixel", "count_compatible_boxes", "d_resolution"], ascending=[True, False, True])
    pareto_csv = pd.DataFrame({"binning_factor"             : _view["binning_factor"].astype(float),
                               "binned_pixel_size"          : _view["binned_pixel_size"].astype(float),
                               "target_resolution"          : _view["target_resolution"].astype(float),
                               "count_compatible_EMAN2boxes": _view["count_compatible_boxes"],
                               "compatibility_factors":_view["binning_factor"].apply(lambda b: numbers.prime_factors_to_str(numbers.prime_factorization(b.denominator))),
    })

    logger.info("Recommended binning factor: ")
    result = {f"rank{i+1}":entry for i, entry in enumerate(pareto_csv.head(3).to_dict(orient="records"))} # "recors"->list of dicts, where each pd row is a dict
    output = utils.output.print_and_save(result, 
                                         #pareto_csv.iloc[0].to_dict(), 
                                         print_as="json" if args.json else ("yaml" if not args.verbose else None),
                                         filepath=os.path.join(basedir, __myname__) if basedir else None)
    logger.info(f"Top #{len(pareto_csv.head(3))} Results:\n\n{output['yaml']}")

    # save remaining files: pareto csv and figure
    if basedir:
        # pareto only
        filepath = os.path.join(basedir, f"optimal_{args.pixel_size}ÅperPixel_{args.target_resolution}Å.csv")
        pareto_csv.to_csv(filepath, index=False)
        logger.info(f"+ Pareto solutions saved to {filepath}")
    
        ### figure ###
        logger.info("Generating figures...")
        # adjust dataframe
        _toplot = history.rename(columns={"d_resolution"    : "obj1", 
                                          "n_decimals_pixel": "obj2",})

        # obj1 is just the magnitude, lets plot the actual resolution
        _sign = _toplot["is_worse_than_target"].apply(lambda x: 1 if x else -1)
        _toplot["obj1"] = args.target_resolution + _sign*_toplot["obj1"]

        # 
        plot_args = {
            "y_label"     : "Number of decimals on the Binned Pixel Size",
            "x_label"     : "Actual Target Resolution",
            "title_str"   : f"Target Resolution: {args.target_resolution} Å",
            # "subtitle_str": f"",
            "legend_str"  : "Candidate Solutions",
            "all_solutions_label"     : "No prime factors ≤13", # "unfeasible"
            "feasible_solutions_label": "Dominated",
            "pareto_labels"           : ["Differ in box compatibility"],
            "filepath"    : os.path.join(basedir, f"pareto_{args.pixel_size}ÅperPixel_{args.target_resolution}Å.png") if basedir else None,
        }

        plot_pareto(_toplot, all_solutions=True, feasible_solutions=True, **plot_args)
        logger.info(f"+ Saved to {plot_args['filepath']}")
    else:
        logger.info("For additional information, consider providing '--output-dir'.")


    logger.info(f"Exiting...")
    logger.info("-"*40)
