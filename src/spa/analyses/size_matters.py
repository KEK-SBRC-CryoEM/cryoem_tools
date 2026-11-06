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

if __name__ == "__main__":
    # python src/spa/analyses/size_matters.py -m ctf -b 480 -p 0.5585 -k 200 -d 1.7 -c 2.7           # 2.764 A
    # python src/spa/analyses/size_matters.py -m deloc -D 76 -r 2.7 -p 0.5585 -k 200 -d 1.7 -c 2.7     # 624 px
    # python src/spa/analyses/size_matters.py -m all -b 480 -p 0.5585 -D 76 -r 2.7 -k 200 -d 1.7 -c 2.7 --output-dir test_/output/
    ########## CLI setup ##########
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
    parser.add_argument("-c", "--cs",         type=float, required=True,   help="Spherical aberration [mm] (default: 2.7)")
    parser.add_argument("-b", "--box_size",   type=int,   default=None,  help="Box size [px]. Required by limit.")
    parser.add_argument("-p", "--pixel_size", type=float, required=True, help="Pixel size [Å/px]")
    parser.add_argument("-D", "--diameter",   type=float, default=0.0,   help="Particle diameter [Å] (default: 0). Used by box; with 0, the box covers only the delocalization (2R).")
    parser.add_argument("-r", "--resolution", type=float, default=None,  help="Target resolution [Å], frequency_target = 1/resolution. Required by delocalization and box.")

    args = utils.cli.init_cli(__myname__, parser) # check the docstring for complete behavior; args.output_path is the resolved run directory

    modes   = list(MODES) if args.mode == "all" else [args.mode]
    missing = sorted({arg for mode in modes for arg in MODES[mode] if getattr(args, arg) is None})
    if missing:
        parser.error(f"--mode {' '.join(modes)} also requires: " + ", ".join("--" + arg for arg in missing))
    ##### / #####

    # input / output organization
    defocus_A = args.defocus * 1e4 # [um] -> [Å]
    cs_A      = args.cs * 1e7      # [mm] -> [Å]
    lambda_A  = relativistic_electron_wavelength_A(voltage_kV=args.voltage)
    logger.info(f"Electron wavelength at {args.voltage:g} kV: {lambda_A:.5f} A")

    result = {"input" : {}, # inputs and derived values
              "output": {}} # computed values
    
    inputs = {"voltage_kV": args.voltage,
              "lambda_A"  : lambda_A,
              "defocus_um": args.defocus,
              "cs_mm"     : args.cs,
              "box_size_px": args.box_size, 
              "pixel_size_A": args.pixel_size, 
              "particle_diameter_A": args.diameter, 
              "target_resolution_A": args.resolution,
    }
    result["input"].update({key: value for key, value in inputs.items() if value is not None}) # filter out Nones

    if "ctf" in modes:
        logger.info("Running ctf_limit (fixed version)...")
        result_ctf = ctf_limit(box_size=args.box_size, pixel_size_A=args.pixel_size, voltage_kV=args.voltage, defocus_A=defocus_A, cs_A=cs_A)
        result["output"]["ctf_limit_resolution_A"]    = 1/result_ctf[1] # resolution before aliasing
        result["output"]["ctf_limit_frequency_per_A"] = result_ctf[1] 
        result["output"]["ctf_limit_fourier_bin"]     = result_ctf[0]

    if "deloc" in modes:
        logger.info("Running box_delocalization...")
        logger.info("Delocalization R(f) = |λ f (ΔZ - Cs λ² f²)|")

        result_deloc = delocalization_max_width_A(frequency_target=1/args.resolution, lambda_A=lambda_A, defocus_A=defocus_A, cs_A=cs_A)
        logger.info(f"R(f) for f up to 1/{args.resolution:g} Å = {1/args.resolution:.4f} Å⁻¹: R = {result_deloc[0]:.2f} Å at {1/result_deloc[1]:.2f} Å")
        result["output"]["delocalization_max_width_A"]         = result_deloc[0]
        result["output"]["delocalization_max_frequency_per_A"] = result_deloc[1]
        result["output"]["delocalization_box_px"]              = box_delocalization( # (D+2R)/pixel_size
                frequency_target    = 1/args.resolution,
                particle_diameter_A = args.diameter,
                lambda_A            = lambda_A,
                defocus_A           = defocus_A,
                cs_A                = cs_A,
                pixel_size_A        = args.pixel_size
        )

        logger.info(f"Box = (D + 2R) / pixel size = {result['output']['delocalization_box_px']}")

    if args.mode == "all": # both results: does the given box suit the target?
        if result["output"]["ctf_limit_resolution_A"] > args.resolution:
            logger.info(f"The {args.box_size} px box aliases at {result['output']['ctf_limit_resolution_A']:.2f} Å, before the {args.resolution:g} Å target")
        if result["output"]["delocalization_box_px"] > args.box_size:
            logger.info(f"The {args.box_size} px box is smaller than the {result['output']['delocalization_box_px']} px needed for the delocalization at {args.resolution:g} Å")

    # print and save output
    output = utils.output.print_and_save(result,
                                         print_as="json" if args.json else "yaml",
                                         filepath=os.path.join(args.output_path, __myname__) if args.output_path else None)
    logger.info(f"Result:\n{output['yaml']}")
    logger.info("Exiting...")
    logger.info("-"*40)