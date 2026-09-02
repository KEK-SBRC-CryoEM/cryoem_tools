from fractions import Fraction
import os
import logging
import argparse
from pathlib import Path
from matplotlib.colors import ListedColormap
import pandas as pd
import numpy as np
from collections import Counter
import math

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
        pareto_annotations=None, filepath=None):
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

    # plot ALL solutions not in the pareto (unfeasible + dominated)
    if all_solutions:
        ax.scatter(solutions[solutions["pareto"]==0]["obj1"],
                   solutions[solutions["pareto"]==0]["obj2"],
                   facecolors='lightgray', edgecolors='lightgray', s=50, label=all_solutions_label)
    
    # plot all FEASIBLE solutions not in the pareto (dominated)
    if feasible_solutions:
        ax.scatter(solutions[solutions["pareto"]>=0][solutions["is_feasible"]]["obj1"], 
                   solutions[solutions["pareto"]>=0][solutions["is_feasible"]]["obj2"], 
                   facecolors='gray', edgecolors='gray', s=50, label=feasible_solutions_label)

    # plot PARETO solutions
    pareto_levels = solutions[solutions["pareto"]>0]["pareto"].unique() # 0: not pareto
    cmap = plt.get_cmap('tab10') #alternative coloring 'viridis'
    tab10_red = ListedColormap(np.roll(cmap.colors, -3, axis=0), name="tab10_red") # red as first color

    for i in pareto_levels:
        _pareto = solutions[solutions["pareto"]==i]
        ax.scatter(_pareto["obj1"], _pareto["obj2"], color=tab10_red(i-1), s=50, edgecolors='none', label=pareto_labels[i-1])

    # add annotation to solutions in the pareto
    if pareto_annotations:
        for i, label in pareto_annotations.items():
            row = solutions.loc[i]
            ax.annotate(label, (row["obj1"], row["obj2"]), textcoords="offset points", xytext=(0, 7), ha='center', fontsize=8)

    # extend y-axis a little to fit the legends
    ymin, ymax = ax.get_ylim()
    yrange = ymax - ymin
    ax.set_ylim(ymin, ymax + 0.25 * yrange)

    # text and labels
    ax.text(0.5, 0.90, f"{subtitle_str}", 
            horizontalalignment='center', verticalalignment='center', multialignment='left', transform=ax.transAxes, 
            fontsize=8, color='black')
    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    ax.set_title(title_str)
    ax.legend(title=legend_str, loc="upper right")
    fig.tight_layout()    

    if filepath:
        plt.savefig(filepath, dpi=300)
    return ax

def find_binning_parameters(target_resolution_A, pixel_size_A_per_pixel, sampling_factor, 
                            evaluation_boxes,
                            evaluation_feasible_primes,
                            grid_step=Fraction(1, 10**6), resolution_tolerance=0.2):
    # guarantees it is a np.array
    evaluation_boxes = np.asarray(evaluation_boxes)

    ### search grid ###
    start_res = Fraction(str(target_resolution_A - resolution_tolerance)) / sampling_factor
    end_res   = Fraction(str(target_resolution_A + resolution_tolerance)) / sampling_factor
    start_idx = math.ceil(start_res / grid_step)
    end_idx   = math.floor(end_res /  grid_step)

    ### candidate solutions ###
    candidate_pixel_sizes = np.array([Fraction(str(i * grid_step)) for i in range(start_idx, end_idx + 1)])
    candidate_resolutions = np.array([Fraction(str(p*Fraction(sampling_factor))) for p in candidate_pixel_sizes])
    candidate_binnings    = np.array([Fraction(str(p/pixel_size_A_per_pixel)) for p in candidate_pixel_sizes])
    
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
    # !!: we already evaluate all pixel sizes with decimal places <= grid_step
    # finite_decimals_pixel   = n_decimals_pixel!=np.inf

    # merge feasibility
    mask_feasible  = has_prime_factor & finite_decimals_binning # & finite_decimals_pixel

    ### evaluation objective 3  ###
    # test compatibility of each feasible binning vs each box
    _false = np.full(len(evaluation_boxes), False)
    compatible_boxes_mask  = np.array([((b*evaluation_boxes)%2)==0 if m else _false for b, m in zip(candidate_binnings, mask_feasible)])
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
                            # "has_finite_pixel"        : finite_decimals_pixel, 
                            "count_compatible_boxes"  : count_compatible_boxes,
                            "is_feasible"             : mask_feasible,
                            # objectives
                            "n_decimals_pixel"        : n_decimals_pixel, 
                            "d_resolution"            : d_resolution,
                            "mask_compatible_boxes"   : list(compatible_boxes_mask),
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
    parser.add_argument("--sampling_factor",                type=float,default=3,    help="Relate pixel size and resolution. Nyquist sampling: 2; Oversampling: >2")
    parser.add_argument("--resolution_tolerance",           type=float,default=0.2,  help="Acceptable tolerance from the target resolution in Å.")
    parser.add_argument("--pixel_max_decimals",             type=int,  default=6,    help="Maximum number of decimal places allowed for the binned pixel size.")
    parser.add_argument("-lb", "--compatible-box-min-size", type=int,  default=64,   help="Minimum FFT-friendly box size considered for compatibility (default: 64).")
    parser.add_argument("-ub", "--compatible-box-max-size", type=int,  default=1024, help="Maximum FFT-friendly box size considered for compatibility (default: 1024).")
    parser.add_argument("-db", "--compatible-box-divisible-by", type=int, nargs="+", default=(2,), help="Only consider FFT-friendly box sizes divisible by the input values (default: 2).")

    parser = utils.cli.add_common_arguments(parser) # adds --verbose, --json, --output-dir --debug
    args = parser.parse_args()

    # directory creation
    basedir = utils.paths.mkdir_timestamp(args.output_dir) # skip if args.output_dir is None

    # logging
    utils.log.configure_logging(verbose=args.verbose, output_directory=basedir, capture_warnings=True)

    # print log header
    if args.verbose:
        utils.cli.log_cli_header(logger=logger, script_name=__myname__, args=args)

    #### step 0: filter fft sizes ####
    fft_sizes_filtered = box.get_fft_friendly_sizes(min_size=args.compatible_box_min_size, 
                                                    max_size=args.compatible_box_max_size,
                                                    divisible_by=args.compatible_box_divisible_by)
    logger.info("FFT-friendly box sizes considered for binning factor compatibility:")
    logger.info(f"+ Filtering by size range: [{args.compatible_box_min_size}, {args.compatible_box_max_size}]")
    logger.info(f"+ Filtering by divisibility: {", ".join(map(str, args.compatible_box_divisible_by))}")
    logger.info(f"+ Available sizes: {len(fft_sizes_filtered)}")

    #### step 1: search process ####
    logger.info("Exhaustive evaluation of binning parameters...")
    # convert everything to fractions to minimize float related problems
    history = find_binning_parameters(target_resolution_A        = Fraction(str(args.target_resolution)), 
                                      pixel_size_A_per_pixel     = Fraction(str(args.pixel_size)), 
                                      sampling_factor            = Fraction(str(args.sampling_factor)),
                                      evaluation_boxes           = fft_sizes_filtered,
                                      evaluation_feasible_primes = (2, 3, 5, 7, 11, 13),
                                      grid_step                  = Fraction(1, 10**args.pixel_max_decimals),
                                      resolution_tolerance       = Fraction(str(args.resolution_tolerance)))
    logger.info(f"+ Total candidates  : {len(history)}")
    logger.info("Checking feasibility...")
    _count = (~history["has_prime_factor"]).sum()
    logger.info(f"+ Filtering out binning factors with prime factors > 13     : {_count}")
    _count = (history["has_prime_factor"] & ~(history["has_finite_binning"])).sum()
    logger.info(f"+ Filtering out binning factors with infinite decimal places: {_count}")
    _count = (history["has_prime_factor"] & history["has_finite_binning"] & (history["count_compatible_boxes"]==0)).sum()
    logger.info(f"+ Filtering out binning factors with no box compatibility   : {_count}")
    logger.info(f"+ Feasible solutions: {history['is_feasible'].sum()}")
    
    # (debug only) save history
    if basedir and args.debug:
        filepath = os.path.join(basedir, f"history_{args.pixel_size}ÅperPixel_{args.target_resolution}Å.csv")
        history.to_csv(filepath, index=False)
        logger.info(f"+ Search evaluation saved to {filepath}")

    #### step 2: pareto front ####
    logger.info("Computing pareto front...")
    logger.info("+ Minimizing number of decimal places in the resulting binned pixel size...")
    logger.info("+ Maximizing compatibility between binning factor and EMAN2 box...")

    # prepare objectives and compute pareto
    _mask = history["is_feasible"]
    _incompatibility_mask = history[_mask]["mask_compatible_boxes"].apply(lambda m: (~m).astype(int)) # minimization -> 0:compatible, 1:incompatible
    objectives = np.column_stack([history[_mask]["n_decimals_pixel"].to_numpy(),
                                  _incompatibility_mask.to_list()])
    _pareto_idx_group = compute_pareto_front(objectives)

    # update history
    history["pareto"] = 0
    history.loc[history.index[_mask][_pareto_idx_group], "pareto"] = 1
    logger.info(f"+ Non-dominated solutions: {sum(history['pareto']>0)}")
    
    if basedir and args.debug: 
    # (debug only) save updated history with pareto information
        filepath = os.path.join(basedir, f"history_{args.pixel_size}ÅperPixel_{args.target_resolution}Å.csv")
        history.to_csv(filepath, index=False)
        logger.info(f"+ Search evaluation updated at {filepath}")

    # save csv with all solutions in the pareto
    _view = history[history["pareto"]>0].sort_values(by=["n_decimals_pixel", "count_compatible_boxes", "d_resolution"], ascending=[True, False, True])
    pareto_csv = pd.DataFrame({"binning_factor"             :_view["binning_factor"].astype(float),
                               "binned_pixel_size"          :_view["binned_pixel_size"].astype(float),
                               "target_resolution"          :_view["target_resolution"].astype(float),
                               "compatibility_factors"      :_view["binning_factor"].apply(lambda b: numbers.prime_factors_to_str(numbers.prime_factorization(b.denominator))),
                               "count_compatible_EMAN2boxes":_view["count_compatible_boxes"],
                               "compatible_boxes"           :_view["mask_compatible_boxes"].apply(lambda m: fft_sizes_filtered[m]).to_list()
    })
    logger.info("Recommended binning factor: ")
    result = {f"rank{i+1}":entry for i, entry in enumerate(pareto_csv.head(3).to_dict(orient="records"))} # "recors"->list of dicts, where each pd row is a dict
    output = utils.output.print_and_save(result,
                                         print_as="json" if args.json else ("yaml" if not args.verbose else None),
                                         filepath=os.path.join(basedir, __myname__) if basedir else None)
    logger.info(f"Top #{len(pareto_csv.head(3))} Results:\n\n{output['yaml']}")

    #### step 3: save pareto.csv and pareto.png ####
    if basedir:
        #### csv ####
        filepath = os.path.join(basedir, f"optimal_{args.pixel_size}ÅperPixel_{args.target_resolution}Å.csv")
        pareto_csv.to_csv(filepath, index=False)
        logger.info(f"+ Pareto solutions saved to {filepath}")

        #### figure ####
        logger.info("Generating figures...")

        # adjust dataframe
        _toplot = history.rename(columns={"d_resolution": "obj1", "n_decimals_pixel": "obj2"})
        _sign = np.where(_toplot["is_worse_than_target"], 1, -1)         # obj1 is just the magnitude, 
        _toplot["obj1"] = args.target_resolution + _sign*_toplot["obj1"] # lets plot the actual resolution
        
        # plot
        filepath = os.path.join(basedir, f"pareto_{args.pixel_size}ÅperPixel_{args.target_resolution}Å.png") if basedir else None
        plot_pareto(_toplot, all_solutions=True, feasible_solutions=True, 
                y_label                  = "Number of decimals in the Binned Pixel Size",
                x_label                  = "Actual Target Resolution",
                title_str                = f"Target Resolution: {args.target_resolution} Å",
                legend_str               = "Candidate Solutions",
                all_solutions_label      = "Not Feasible", # "unfeasible"
                feasible_solutions_label = "Dominated",
                pareto_labels            = ["Differ in box compatibility"],
                pareto_annotations       = history[history["pareto"]>0]["binning_factor"].to_dict(),
                filepath                 = filepath
        )

        logger.info(f"+ Saved to {filepath}")
    else:
        logger.info("For additional information, consider providing '--output-dir'.")

    logger.info(f"Exiting...")
    logger.info("-"*40)
