import os
import logging
import argparse
from dataclasses import dataclass, asdict, fields
from pathlib import Path

import numpy as np

from spa import utils
from spa import box
from spa.extraction import parameters as extraction
import postprocessing_rules as rules

__myname__ = Path(__file__).stem
logger = logging.getLogger(__myname__)

INVALID = "<INVALID>" # value of a parameter that can't be computed (a warning says why)

class NotAvailable(Exception):
    """A value a parameter needs is not available."""

@dataclass
class CSSParameters:
    """
    CS-Schemes parameters, one property each.
    The fields are the values they are computed from, all wired in the workflow: from the steps and from the user inputs.
    A field that isn't given keeps its default; a parameter that needs a None field can't be computed.
    """
    # from the workflow steps
    lbin_pixel_size_A_per_px    : float | None = None # find_binning_factor, rank1
    lbin_binning_factor         : float | None = None # find_binning_factor, rank1
    lbin_compatible_boxes_px    : list  | None = None # find_binning_factor, rank1: binned boxes compatible with the binning factor
    lbin_deloc_box_px           : int   | None = None # size_matters, at the binned pixel size
    particle_diameter_px        : float | None = None # size_estimation; 0 or None when unknown
    # from the user inputs
    particle_pixel_size_A_per_px: float | None = None
    micrograph_lower_bound_x    : int   = 0
    micrograph_lower_bound_y    : int   = 0
    micrograph_upper_bound_x    : int   | None = None # micrograph size
    micrograph_upper_bound_y    : int   | None = None
    padding_pixels              : float = 0
    padding_angstrom            : float = 0
    padding_percentage          : float = 0

    def need(self, name):
        """Value of a field; raises NotAvailable when it is None."""
        value = getattr(self, name)
        if value is None:
            raise NotAvailable(f"{name} is not available")
        return value

    ### used by several parameters ###
    @property
    def lbin_boxes(self):
        """Smallest compatible box that holds the delocalization box and is an even box on the micrographs."""
        compatible = np.asarray(self.need("lbin_compatible_boxes_px"))
        boxes      = extraction.compute_boxes(self.need("lbin_deloc_box_px"), self.need("lbin_binning_factor"), compatible)
        if boxes["rescaled_box"] is None:
            raise NotAvailable(f"no compatible box holds {self.lbin_deloc_box_px} px (largest: {compatible.max()} px)")
        return boxes # extract_box: on the micrographs; rescaled_box: after binning

    @property
    def particle_pmd_A(self):
        """Particle diameter with the user's padding [Å]."""
        if not self.need("particle_diameter_px"):
            raise NotAvailable("particle_diameter_px is 0 (unknown)")
        return rules.padding(self.particle_diameter_px, self.need("particle_pixel_size_A_per_px"),
                             padding_pixels     = self.padding_pixels,
                             padding_angstrom   = self.padding_angstrom,
                             padding_percentage = self.padding_percentage)

    ##### Common #####
    @property
    def SS_comm_class2d_pmd(self):
        return self.particle_pmd_A

    @property
    def SS_comm_optimal_pmd(self):
        return self.particle_pmd_A

    @property
    def SS_comm_lbin_angpix(self):
        return self.need("lbin_pixel_size_A_per_px")

    ##### 030_GTF_Create_Stack #####
    @property
    def GTF_lbin_extract_mics_box(self):
        return self.lbin_boxes["extract_box"]

    @property
    def GTF_lbin_extract_mics_0o95box(self):
        return box.adjust_box(self.lbin_boxes["extract_box"], scaling=0.95, make_even=True)

    @property
    def GTF_lbin_extract_parts_box(self):
        return self.lbin_boxes["rescaled_box"]

    @property
    def GTF_lbin_extract_parts_x_min(self):
        return extraction.compute_coordinates_min(self.lbin_boxes["extract_box"], self.micrograph_lower_bound_x)

    @property
    def GTF_lbin_extract_parts_x_max(self):
        return extraction.compute_coordinates_max(self.lbin_boxes["extract_box"], self.need("micrograph_upper_bound_x"))

    @property
    def GTF_lbin_extract_parts_y_min(self):
        return extraction.compute_coordinates_min(self.lbin_boxes["extract_box"], self.micrograph_lower_bound_y)

    @property
    def GTF_lbin_extract_parts_y_max(self):
        return extraction.compute_coordinates_max(self.lbin_boxes["extract_box"], self.need("micrograph_upper_bound_y"))

    ##### 050_GTF_AbInitReconst3D #####
    @property
    def GTF_lbin_abinit3d_pmd(self):
        return self.particle_pmd_A

# the parameters each workflow writes, in the order of the CS-Schemes template
WORKFLOWS = {
    "size_matters": ("SS_comm_class2d_pmd",
                     "SS_comm_optimal_pmd",
                     "SS_comm_lbin_angpix",
                     "GTF_lbin_extract_mics_box",
                     "GTF_lbin_extract_mics_0o95box",
                     "GTF_lbin_extract_parts_box",
                     "GTF_lbin_extract_parts_x_min",
                     "GTF_lbin_extract_parts_x_max",
                     "GTF_lbin_extract_parts_y_min",
                     "GTF_lbin_extract_parts_y_max",
                     "GTF_lbin_abinit3d_pmd"),
}

def run(parameters, names):
    # compute each parameter; if it cannot be computed, write "INVALID" and warning in the logs
    values = {}
    for name in names:
        try:
            values[name] = getattr(parameters, name)
        except NotAvailable as reason:
            logger.warning(f"{name}: not computed, {reason}")
            values[name] = INVALID

    data = {}
    return values, data

if __name__ == "__main__":
    ### 1. CLI setup ###
    parser = argparse.ArgumentParser(
        description=("CS-Schemes parameters of a workflow execution."),
        formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--workflow",                 type=str, required=True, choices=list(WORKFLOWS), help="Workflow whose parameters to write")
    # from the workflow steps
    parser.add_argument("--lbin_pixel_size",          type=float,          help="Binned pixel size [Å/px] (find_binning_factor, rank1)")
    parser.add_argument("--lbin_binning_factor",      type=float,          help="Binning factor (find_binning_factor, rank1)")
    parser.add_argument("--lbin_compatible_boxes",    type=int, nargs="+", help="Binned boxes compatible with the binning factor [px] (find_binning_factor, rank1)")
    parser.add_argument("--lbin_deloc_box",           type=int,            help="Box for the particle and its delocalized signal, at the binned pixel size [px] (size_matters)")
    parser.add_argument("--particle_diameter",        type=float,          help="Particle diameter [px], 0 if unknown (size_estimation)")
    parser.add_argument("--particle_pixel_size",      type=float,          help="Pixel size of the map the diameter was measured on [Å/px] (size_estimation)")
    # from the user inputs
    parser.add_argument("--micrograph_lower_bound_x", type=int,            help="Lowest x coordinate on the micrographs [px] (default: 0)")
    parser.add_argument("--micrograph_lower_bound_y", type=int,            help="Lowest y coordinate on the micrographs [px] (default: 0)")
    parser.add_argument("--micrograph_upper_bound_x", type=int,            help="Highest x coordinate on the micrographs [px]")
    parser.add_argument("--micrograph_upper_bound_y", type=int,            help="Highest y coordinate on the micrographs [px]")
    parser.add_argument("--padding_pixels",           type=float,          help="Padding of the particle diameter [px] (default: 0)")
    parser.add_argument("--padding_angstrom",         type=float,          help="Padding of the particle diameter [Å] (default: 0)")
    parser.add_argument("--padding_percentage",       type=float,          help="Padding of the particle diameter, as a fraction (default: 0)")

    args = utils.cli.init_cli(__myname__, parser) # check the docstring for complete behavior; args.output_path is the resolved run directory

    ### 2. I/O DEFINITION ###
    inputs  = {"workflow": args.workflow,
               **{field.name: ... for field in fields(CSSParameters)}, # given, or the field's default
    }
    outputs = {name: ... for name in WORKFLOWS[args.workflow]} # a value, or INVALID

    ### 3. PREPROCESSING ###
    given = {"lbin_pixel_size_A_per_px"    : args.lbin_pixel_size,
             "lbin_binning_factor"         : args.lbin_binning_factor,
             "lbin_compatible_boxes_px"    : args.lbin_compatible_boxes,
             "lbin_deloc_box_px"           : args.lbin_deloc_box,
             "particle_diameter_px"        : args.particle_diameter,
             "particle_pixel_size_A_per_px": args.particle_pixel_size,
             "micrograph_lower_bound_x"    : args.micrograph_lower_bound_x,
             "micrograph_lower_bound_y"    : args.micrograph_lower_bound_y,
             "micrograph_upper_bound_x"    : args.micrograph_upper_bound_x,
             "micrograph_upper_bound_y"    : args.micrograph_upper_bound_y,
             "padding_pixels"              : args.padding_pixels,
             "padding_angstrom"            : args.padding_angstrom,
             "padding_percentage"          : args.padding_percentage}
    parameters = CSSParameters(**{name: value for name, value in given.items() if value is not None}) # keep the default if not provided
    inputs.update(asdict(parameters))

    ### 4. MAIN ###
    logger.info(f"Computing the CS-Schemes parameters of {inputs['workflow']}...")
    values, data = run(parameters, WORKFLOWS[inputs["workflow"]])
    outputs.update(values)

    ### 5. POSTPROCESSING ###
    # save I/O
    utils.output.print_and_save({"input":inputs, "output":outputs},
                                print_as="json" if args.json else "yaml",
                                filepath=os.path.join(args.output_path, __myname__) if args.output_path else None)
    logger.info("Exiting...")
    logger.info("-"*40)