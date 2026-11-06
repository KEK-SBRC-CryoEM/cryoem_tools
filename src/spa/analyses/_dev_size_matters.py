# temporary ctf/box CLI
import os
import logging
import argparse
from pathlib import Path

from spa import utils
from spa.physics import relativistic_electron_wavelength_A
from spa.physics.ctf import ctf_limit, ctf_limit_sparx, ctf_delocalization_distance_A, delocalization_max_width_A, box_delocalization

__myname__ = Path(__file__).stem 
logger     = logging.getLogger(__myname__)


if __name__ == "__main__":
    # python src/spa/analyses/size_matters.py -m sparx limit -b 480 -p 0.5585 -k 200 -d 1.7 -c 2.7   # 1.117 A (sparx) / 2.764 A (fixed)
    # python src/spa/analyses/size_matters.py -m fresnel -D 120 -r 2.8 -k 200 -d 1.7                 # 424.52 A
    # python src/spa/analyses/size_matters.py -m delocalization -r 2.7 -k 200 -d 1.7 -c 2.7          # R = 136.27 A
    # python src/spa/analyses/size_matters.py -m box -D 76 -r 2.7 -p 0.5585 -k 200 -d 1.7 -c 2.7     # 624 px
    # python src/spa/analyses/size_matters.py -m all -b 480 -p 0.5585 -D 76 -r 2.7 -k 200 -d 1.7 -c 2.7 --output-dir test_/output/
    ########## CLI setup ##########
    MODES = { # mode: extra arguments it requires (all modes use --voltage and --defocus, all but fresnel use --cs)
        "sparx"          : ["box_size", "pixel_size"],               # ctf_limit_sparx
        "limit"          : ["box_size", "pixel_size"],               # ctf_limit
        "fresnel"        : ["diameter", "resolution"],               # ctf_delocalization_distance_A
        "delocalization" : ["resolution"],                           # delocalization_max_width_A
        "box"            : ["diameter", "resolution", "pixel_size"], # box_delocalization
    }
    parser = argparse.ArgumentParser(
        description=(
            "CTF limits on the pixel and box sizes: aliasing, Fresnel fringes and delocalization. \n"
            "Select the computation(s) with --mode (several can be given, or 'all'):\n"
            "\t sparx          : resolution [Å] before CTF aliasing, original SPARX version\n"
            "\t limit          : resolution [Å] before CTF aliasing, fixed version\n"
            "\t fresnel        : width in real space [Å] with the Fresnel fringes (book): D + 2*lambda*defocus/resolution\n"
            "\t delocalization : max extent R [Å] of the delocalization for the target frequency (1/resolution)\n"
            "\t box            : box size [px] from the derivative of the phase: (D + 2R) / pixel_size\n"
            "Defocus is given in [um] and positive for underfocus; Cs in [mm].\n"
            "Usage: \n"
            "\t python ctf_limits.py -m sparx limit -b 480 -p 0.5585 -k 200 -d 1.7\n"
            "\t python ctf_limits.py -m fresnel -D 120 -r 2.8 -k 200 -d 1.7\n"
            "\t python ctf_limits.py -m box -D 76 -r 2.7 -p 0.5585 -k 200 -d 1.7 -c 2.7"
        ),
        formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("-m", "--mode",       type=str,   required=True, nargs="+", choices=list(MODES) + ["all"], metavar="MODE", help=f"Computation(s) to run: {', '.join(MODES)} or all")
    parser.add_argument("-k", "--voltage",    type=float, required=True, help="Acceleration voltage [kV]")
    parser.add_argument("-d", "--defocus",    type=float, required=True, help="Defocus [um]")
    parser.add_argument("-c", "--cs",         type=float, default=2.7,   help="Spherical aberration [mm] (default: 2.7). Not used by fresnel.")
    parser.add_argument("-b", "--box_size",   type=int,   default=None,  help="Box size [px]. Required by sparx and limit.")
    parser.add_argument("-p", "--pixel_size", type=float, default=None,  help="Pixel size [A/px]. Required by sparx, limit and box.")
    parser.add_argument("-D", "--diameter",   type=float, default=0.0,   help="Particle diameter [Å]. Required by fresnel and box.")
    parser.add_argument("-r", "--resolution", type=float, default=None,  help="Target resolution [Å], frequency_target = 1/resolution. Required by fresnel, delocalization and box.")

    args = utils.cli.init_cli(__myname__, parser) # check the docstring for complete behavior; args.output_path is the resolved run directory

    modes   = [mode for mode in MODES if mode in args.mode or "all" in args.mode] # keeps the MODES order, no duplicates
    missing = sorted({arg for mode in modes for arg in MODES[mode] if getattr(args, arg) is None})
    if missing:
        parser.error(f"--mode {' '.join(modes)} also requires: " + ", ".join("--" + arg.replace("_", "-") for arg in missing))
    ##### / #####

    # computation
    defocus_A = args.defocus * 1e4 # [um] -> [Å]
    cs_A      = args.cs * 1e7      # [mm] -> [Å]
    lambda_A  = relativistic_electron_wavelength_A(voltage_kV=args.voltage)
    logger.info(f"Electron wavelength at {args.voltage:g} kV: {lambda_A:.5f} A")

    result = {"voltage_kV": args.voltage, "lambda_A": lambda_A, "defocus_um": args.defocus, "cs_mm": args.cs}
    inputs = {"box_size_px": args.box_size, "pixel_size_A": args.pixel_size, "particle_diameter_A": args.diameter, "target_resolution_A": args.resolution}
    result.update({key: value for key, value in inputs.items() if value is not None})

    if "sparx" in modes:
        logger.info("Running ctf_limit_sparx (original SPARX version)...")
        frequency = ctf_limit_sparx(box_size=args.box_size, pixel_size_A=args.pixel_size, voltage_kV=args.voltage, defocus_um=args.defocus, cs_mm=args.cs)[1]
        result["ctf_limit_sparx_resolution_A"] = 1/frequency # resolution before aliasing

    if "limit" in modes:
        logger.info("Running ctf_limit (fixed version)...")
        frequency = ctf_limit(box_size=args.box_size, pixel_size_A=args.pixel_size, voltage_kV=args.voltage, defocus_A=defocus_A, cs_A=cs_A)[1]
        result["ctf_limit_resolution_A"] = 1/frequency # resolution before aliasing

    if "fresnel" in modes:
        logger.info("Running ctf_delocalization_distance_A (Fresnel fringes)...")
        result["fresnel_delocalization_distance_A"] = ctf_delocalization_distance_A( # width in real space
                particle_diameter_A = args.diameter,
                lambda_A            = lambda_A,
                resolution_A        = args.resolution,
                defocus_A           = defocus_A
        )

    if "delocalization" in modes:
        logger.info("Running delocalization_max_width_A...")
        result["delocalization_max_width_A"] = delocalization_max_width_A( # R
                frequency_target = 1/args.resolution,
                lambda_A         = lambda_A,
                defocus_A        = defocus_A,
                cs_A             = cs_A
        )

    if "box" in modes:
        logger.info("Running box_delocalization...")
        result["box_delocalization_px"] = box_delocalization( # (D+2R)/pixel_size
                frequency_target    = 1/args.resolution,
                particle_diameter_A = args.diameter,
                lambda_A            = lambda_A,
                defocus_A           = defocus_A,
                cs_A                = cs_A,
                pixel_size_A        = args.pixel_size
        )

    # print and save output
    output = utils.output.print_and_save(result,
                                         print_as="json" if args.json else "yaml",
                                         filepath=os.path.join(args.output_path, __myname__) if args.output_path else None)
    logger.info(f"Result:\n{output['yaml']}")
    logger.info(f"Exiting...")
    logger.info("-"*40)

