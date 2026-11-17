# temporary ctf/box CLI
import os
import logging
import argparse
from pathlib import Path

from spa import utils
from spa.physics import relativistic_electron_wavelength_A
from spa.physics.ctf import ctf_limit, delocalization_max_width_A, box_delocalization

__myname__ = Path(__file__).stem 
logger     = logging.getLogger(__myname__)

def run(modes, voltage_kV, lambda_A, defocus_um, cs_mm, pixel_size_A_per_px, box_size_px, diameter_A, resolution_A):
    defocus_A = defocus_um * 1e4 # [um] -> [Å]
    cs_A      = cs_mm * 1e7      # [mm] -> [Å]
    values    = {}

    # 1. ctf: resolution before the CTF aliases in the box
    if "ctf" in modes:
        logger.info("Running ctf_limit (fixed version)...")
        fourier_bin, frequency = ctf_limit(box_size=box_size_px, pixel_size_A=pixel_size_A_per_px, voltage_kV=voltage_kV, defocus_A=defocus_A, cs_A=cs_A)
        values.update({"ctf_limit_resolution_A"   : 1/frequency, # resolution before aliasing
                       "ctf_limit_frequency_per_A": frequency,
                       "ctf_limit_fourier_bin"    : fourier_bin})

    # 2. deloc: box that holds the particle plus its delocalized signal
    if "deloc" in modes:
        logger.info("Running box_delocalization...")
        logger.info("Delocalization R(f) = |λ f (ΔZ - Cs λ² f²)|")
        R, frequency_R = delocalization_max_width_A(frequency_target=1/resolution_A, lambda_A=lambda_A, defocus_A=defocus_A, cs_A=cs_A)
        logger.info(f"R(f) for f up to 1/{resolution_A:g} Å = {1/resolution_A:.4f} Å⁻¹: R = {R:.2f} Å at {1/frequency_R:.2f} Å")
        box_px = box_delocalization( # (D+2R)/pixel_size
                frequency_target    = 1/resolution_A,
                particle_diameter_A = diameter_A,
                lambda_A            = lambda_A,
                defocus_A           = defocus_A,
                cs_A                = cs_A,
                pixel_size_A        = pixel_size_A_per_px
        )
        logger.info(f"Box = (D + 2R) / pixel size = {box_px}")
        values.update({"delocalization_max_width_A"        : R,
                       "delocalization_max_frequency_per_A": frequency_R,
                       "delocalization_box_px"             : box_px})

    data = {}

    return values, data

if __name__ == "__main__":
    ### 1. CLI setup ###
    MODES = { # mode: extra arguments it requires (all modes use --voltage, --defocus, --cs and --pixel_size)
        "ctf"    : ["box_size"],    # ctf_limit
        "deloc"  : ["resolution"],  # box_delocalization (--diameter optional, default 0)
    }
    parser = argparse.ArgumentParser(
        description=(
            "CTF limit and Delocalization extent.\n"
            "Select the --mode:\n"
            "\t ctf    : resolution [Å] before CTF aliasing\n"
            "\t deloc  : box size [px] from the derivative of the phase: (D + 2R) / pixel_size\n"
            "\t          R: delocalization extent at the target resolution; D: particle diameter (0 if unknown)\n"
            "\t all    : run all above\n"
            "Defocus is given in [um] and positive for underfocus; Cs in [mm].\n"
            "Usage: \n"
            "\t python size_matters.py -m ctf -b 480 -p 0.5585 -k 200 -d 1.7\n"
            "\t python size_matters.py -m deloc -r 2.7 -p 0.5585 -k 200 -d 1.7\n"
            "\t python size_matters.py -m deloc -D 76 -r 2.7 -p 0.5585 -k 200 -d 1.7 -c 2.7"
            "\t python size_matters.py -m all -b 480 -D 76 -r 2.7 -p 0.5585 -k 200 -d 1.7 -c 2.7"
        ),
        formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("-m", "--mode",       required=True, choices=list(MODES) + ["all"], help="Computation to run (see above)")
    parser.add_argument("-k", "--voltage",    type=float, required=True, help="Acceleration voltage [kV]")
    parser.add_argument("-d", "--defocus",    type=float, required=True, help="Defocus [um]")
    parser.add_argument("-c", "--cs",         type=float, required=True, help="Spherical aberration [mm]")
    parser.add_argument("-b", "--box_size",   type=int,   default=None,  help="Box size [px]")
    parser.add_argument("-p", "--pixel_size", type=float, required=True, help="Pixel size [Å/px]")
    parser.add_argument("-D", "--diameter",   type=float, default=0.0,   help="Particle diameter [Å] (default: 0)")
    parser.add_argument("-r", "--resolution", type=float, default=None,  help="Target resolution [Å], frequency_target = 1/resolution")

    args = utils.cli.init_cli(__myname__, parser) # check the docstring for complete behavior; args.output_path is the resolved run directory

    modes   = list(MODES) if args.mode == "all" else [args.mode]
    missing = sorted({arg for mode in modes for arg in MODES[mode] if getattr(args, arg) is None})
    if missing:
        parser.error(f"--mode {' '.join(modes)} also requires: " + ", ".join("--" + arg for arg in missing))

    ### 2. I/O DEFINITION ###
    inputs  = {"mode"               : args.mode,
               "voltage_kV"         : args.voltage,
               "lambda_A"           : ..., # from the voltage
               "defocus_um"         : args.defocus,
               "cs_mm"              : args.cs,
               "pixel_size_A_per_px": args.pixel_size,
               "box_size_px"        : args.box_size   if "ctf"   in modes else None, # used only by ctf
               "diameter_A"         : args.diameter   if "deloc" in modes else None, # used only by deloc
               "resolution_A"       : args.resolution if "deloc" in modes else None, # used only by deloc
    }
    outputs = {"ctf_limit_resolution_A"            : ... if "ctf"   in modes else None, # resolution before the CTF aliases in the box
               "ctf_limit_frequency_per_A"         : ... if "ctf"   in modes else None,
               "ctf_limit_fourier_bin"             : ... if "ctf"   in modes else None,
               "delocalization_max_width_A"        : ... if "deloc" in modes else None, # R, up to the target resolution
               "delocalization_max_frequency_per_A": ... if "deloc" in modes else None, # where R occurs
               "delocalization_box_px"             : ... if "deloc" in modes else None, # (D + 2R) / pixel size, rounded up to even
    }

    ### 3. PREPROCESSING ###
    inputs["lambda_A"] = relativistic_electron_wavelength_A(voltage_kV=inputs["voltage_kV"])
    logger.info(f"Electron wavelength at {inputs['voltage_kV']:g} kV: {inputs['lambda_A']:.5f} Å")

    ### 4. MAIN ###
    values, data = run(modes               = modes,
                       voltage_kV          = inputs["voltage_kV"],
                       lambda_A            = inputs["lambda_A"],
                       defocus_um          = inputs["defocus_um"],
                       cs_mm               = inputs["cs_mm"],
                       pixel_size_A_per_px = inputs["pixel_size_A_per_px"],
                       box_size_px         = inputs["box_size_px"],
                       diameter_A          = inputs["diameter_A"],
                       resolution_A        = inputs["resolution_A"])
    outputs.update(values)

    ### 5. POSTPROCESSING ###
    # when running both modes: does the given box suit the target?
    if inputs["mode"] == "all":
        if outputs["ctf_limit_resolution_A"] > inputs["resolution_A"]:
            logger.info(f"The {inputs['box_size_px']} px box aliases at {outputs['ctf_limit_resolution_A']:.2f} Å, before the {inputs['resolution_A']:g} Å target")
        if outputs["delocalization_box_px"] > inputs["box_size_px"]:
            logger.info(f"The {inputs['box_size_px']} px box is smaller than the {outputs['delocalization_box_px']} px needed for the delocalization at {inputs['resolution_A']:g} Å")

    # save I/O
    utils.output.print_and_save({"input":inputs, "output":outputs},
                                print_as="json" if args.json else "yaml",
                                filepath=os.path.join(args.output_path, __myname__) if args.output_path else None)
    logger.info("Exiting...")
    logger.info("-"*40)