import os
import logging 
import argparse

import numpy as np
from functools import partial
from pathlib import Path
__myname__ = Path(__file__).stem 
logger = logging.getLogger(__myname__) 

from spa import utils
from spa import physics

def ctf_delocalization_distance_A(particle_diameter_A:float, lambda_A:float, resolution_A:float, defocus_A:float) -> float:
    """
    Calculate the physical distance required to capture "Fresnel fringes"
        around a particle in real space caused by defocus induced delocalization.

    Parameters:
        particle_diameter_A (float): Particle diameter in Ångströms [Å].
        lambda_A            (float): Relativistic electron wavelength in Ångströms [Å].
        resolution_A        (float): Target resolution in Ångströms [Å].
        defocus_A           (float): Defocus value in Ångströms [Å].

    Returns:
        distance_A (float): Physical distance in Ångströms [Å].

    Formula:
        distance_A = particle_diameter_A + 2 * defocus_A * (lambda_A / resolution_A)

    Source:
        @book{glaeser2021single,
            title     = {Single-particle Cryo-EM of biological macromolecules},
            author    = {Glaeser, Robert M and Nogales, Eva and Chiu, Wah},
            year      = {2021},
            publisher = {IOP publishing}
            series    = {2053-2563},
            isbn      = {978-0-7503-3039-8},
            url       = {https://doi.org/10.1088/978-0-7503-3039-8},
            doi       = {10.1088/978-0-7503-3039-8}
            note      = {Chapter 4.3.2, Equation 4-10, Page 4-18}
        }

    """
    return particle_diameter_A + 2*defocus_A*(lambda_A/resolution_A) # [Å]

def ctf_period(frequency:float, lambda_A:float, defocus_A:float, cs_A:float) -> float:
    r"""
    Calculate the local oscillation period of the Contrast Transfer Function (CTF) at a given spatial frequency.
    
    This function solves for the CTF oscillation period T using a fourth-order polynomial obtained from the 
        phase condition: $\gamma(f + T) - \gamma(f) = - 2\pi $ where 
        $\gamma(f) = 2\pi \left(\frac{defocus \lambda frequency^2}{2} - \frac{cs \lambda^3 frequency^4}{4} \right)$.

    The result represents the frequency interval between two consecutive peaks of the CTF from
        the specified spatial frequency moving towards lower frequency, which can be used to assess aliasing in Fourier space.
        
    Parameters:
        defocus_A (float): defocus value in (positive for underfocus) [Å].
        cs_A      (float): spherical aberration constant in [Å].
        lambda_A  (float): relativistic electron wavelength in [Å].
        frequency (float): spatial frequency in [Å⁻¹] at which to compute the CTF oscillation period.

    Returns:
        float : Frequency Spacing T [Å⁻¹].

	Notes:
        This is a reimplementation of the `ctfperiod` function defined in `morphology.py` from the `EMAN2/SPARX` package.
        morphology.py: https://github.com/cryoem/eman2/blob/master/sparx/libpy/morphology.py (Original Author: Pawel A.Penczek)
    """
    A  = 0.5 * defocus_A * lambda_A
    B  = 0.25 * cs_A * lambda_A**3
    f2 = frequency**2

    # solve a 4th order polynomial to compute the local CTF period
    roots      = np.roots([B, 4*B*frequency, 6*B*f2 - A, 4*B*f2*frequency - 2*A*frequency, -1.0])
    real_roots = roots[np.isclose(roots.imag, 0)] # filter out complex roots 
    return np.min(np.abs(real_roots))

def ctf_limit(box_size:int, pixel_size_A:float, voltage_kV:float, defocus_A:float, cs_A:float, min_bins_per_cycle:float=2):
    """
    Find the Fourier pixel index and up to which spatial frequency that can be represented by the given box_size and microscope settings.

    Parameters:
      boxsize      (int)  : image length in [pixel].
      pixel_size_A (float): real space length [Å].
      defocus_A    (float): defocus value in [Å].
      cs_A         (float): spherical aberration constant in [Å].
      voltage_kV   (float): microscope accelerating voltage in [kV].
      min_bins_per_cycle (float): Minimum necessary bins required to represent one cycle (Default is Nyquist Limit: 2)
    
    Returns:
      (tuple): (Fourier pixel index, spatial frequency in [Å⁻¹]),
        Highest alias-free Fourier pixel index and spatial frequency.
                
    
	Notes:
        This is a reimplementation of the `ctflimit` function defined in `morphology.py` from the `EMAN2/SPARX` package.
        morphology.py: https://github.com/cryoem/eman2/blob/master/sparx/libpy/morphology.py (Original Author: Pawel A.Penczek)
    
    Important changes:
        - Fix off-by-one error 
        - Scan upwards due to non-monotonicity on the ctf_period(frequency)
    """
    logger.info("")
    logger.info(f"CTF Limit calculation using boxsize={box_size}, pixel_size={pixel_size_A}, defocus={defocus_A}, cs={cs_A}, voltage={voltage_kV}")

    # 1. Number of unique frequency bins (from 0 to Nyquist)
    n_frequency_bins = box_size // 2 + 1  # half of the image +1 in fourier space (DC and nyquist; excludes negatives)
    logger.info(f"Number of unique frequency bins: {n_frequency_bins} (from 0 to Nyquist)")
  
    # 2. Width of a frequency bin in fourier space [Å⁻¹]
    nyquist_frequency   = 1.0/(2*pixel_size_A)        # [Å⁻¹] maximum representable frequency for this pixel size
    frequency_bin_width = nyquist_frequency / (n_frequency_bins-1) # [Å⁻¹] # 1.0/(box_size*pixel_size) 
    logger.info(f"Nyquist Frequency: {nyquist_frequency} [Å⁻¹]")
    logger.info(f"Width of frequency bins in fourier space: {frequency_bin_width} [Å⁻¹]")
 
    # 3. Minimum CTF period representable by the bin width
    min_ctf_period = min_bins_per_cycle*frequency_bin_width # [Å⁻¹]
    logger.info(f"Minimum representable CTF period: {min_ctf_period} [Å⁻¹]")

    # 4. Electron wavelength from accelerating voltage
    lambda_A  = physics.relativistic_electron_wavelength_A(voltage_kV=voltage_kV) # [Å]

    # 5. If no alias-free bin is found, return Nyquist
    bin_result       = n_frequency_bins-1 # index of last bin
    frequency_result = nyquist_frequency  # maximum frequency
    found = False

    # 6. Find the frequency where the CTF oscillation period exceeds the threshold frequency
    logger.info("Finding CTF oscillation period that exceed the threshold frequency...")
    for bin_i in range(1, n_frequency_bins):  # from low frequencies to Nyquist
        # 6a. Map Fourier‐bin index to spatial frequency (bin_i frequency)
        spatial_frequency = (bin_i /(n_frequency_bins-1)) * nyquist_frequency # [Å⁻¹]

        # 6b. Compute CTF period in fourier space  
        current_ctf_period = ctf_period(frequency = spatial_frequency,
                                        defocus_A = defocus_A,
                                        cs_A      = cs_A,
                                        lambda_A  = lambda_A) # [Å⁻¹]
        logger.info(f"\tCTF period: {current_ctf_period}[Å⁻¹] >= {min_ctf_period}[Å⁻¹]? {current_ctf_period >= min_ctf_period}")

        # 6c. When the CTF period exceeds the allowed sampling window, return the previous bin
        if current_ctf_period < min_ctf_period:
            bin_result       = bin_i - 1 
            frequency_result = (bin_result / (n_frequency_bins - 1)) * nyquist_frequency
            found = True
            break # return (bin index, spatial frequency) at aliasing limit

    if found:
        logger.info(f"Aliasing begins at bin #{bin_i}; highest alias-free frequency {frequency_result} [Å⁻¹] ({1/frequency_result:.2f} Å)")
    else:
        logger.info(f"No aliasing up to Nyquist: {frequency_result} [Å⁻¹] ({1/frequency_result:.2f} Å)")
    logger.info("")

    return bin_result, frequency_result

def ctf_limit_sparx(box_size:int, pixel_size_A:float, voltage_kV:float, defocus_um:float, cs_mm:float):
    """
    Find the Fourier pixel index and up to which spatial frequency that can be represented by the given box_size and microscope settings.

    Parameters:
      boxsize      (int)  : image length in [pixel].
      pixel_size_A (float): real space length [Å].
      defocus_um   (float): defocus value in [µm].
      cs_mm        (float): spherical aberration constant in [mm].
      voltage_kV   (float): microscope accelerating voltage in [kV].
    
    Returns:
      (tuple): (Fourier pixel index, spatial frequency in [Å⁻¹]),
        Highest alias-free Fourier pixel index and spatial frequency.
    
	Notes:
        This is a reimplementation of the `ctflimit` function defined in `morphology.py` from the `EMAN2/SPARX` package.
        morphology.py: https://github.com/cryoem/eman2/blob/master/sparx/libpy/morphology.py (Original Author: Pawel A.Penczek)
    """
    logger.info("SPARX Version.")
    logger.info(f"CTF Limit calculation using boxsize={box_size}, pixel_size={pixel_size_A}, defocus={defocus_um}, cs={cs_mm}, voltage={voltage_kV}")

    # 1. Number of unique frequency bins (from 0 to Nyquist)
    n_frequency_bins = box_size // 2 + 1  # half of the image +1 in fourier space (DC and nyquist; excludes negatives)
    logger.info(f"Number of unique frequency bins: {n_frequency_bins} (from 0 to Nyquist)")
  
    # 2. Width of a frequency bin in fourier space [Å⁻¹]
    nyquist_frequency   = 1.0/(2*pixel_size_A)        # [Å⁻¹] maximum representable frequency for this pixel size
    frequency_bin_width = nyquist_frequency / n_frequency_bins # [Å⁻¹] # note: divides by n,  not n-1 (off-by-one)
    logger.info(f"Nyquist Frequency: {nyquist_frequency} [Å⁻¹]")
    logger.info(f"Width of frequency bins in fourier space: {frequency_bin_width} [Å⁻¹]")
 
    # 3. Minimum CTF period representable by the bin width
    min_ctf_period = 2*frequency_bin_width # [Å⁻¹]
    logger.info(f"Minimum representable CTF period: {min_ctf_period} [Å⁻¹]")

    # 4. Wrapper for ctfperiod, binding fixed parameters that needed conversion
    partial_ctf_period = partial(ctf_period,
                                defocus_A = defocus_um*1e4,  # Convert µm to Å
                                cs_A      = cs_mm*1e7,       # Convert mm to Å
                                lambda_A  = physics.relativistic_electron_wavelength_A(voltage_kV=voltage_kV) # [Å]
    )

    # 5. If no alias-free bin is found, return Nyquist
    bin_result       = n_frequency_bins-1 # index of last bin
    frequency_result = nyquist_frequency  # maximum frequency
    found = False

    # 6. Find the frequency where the CTF oscillation period exceeds the threshold frequency
    logger.info("Finding CTF oscillation period that exceed the threshold frequency...")
    for bin_i in range(n_frequency_bins-1, 1, -1): # from nyquist bin to lower frequencies        
        # 6a. Map Fourier‐bin index to spatial frequency (bin_i frequency)
        spatial_frequency = (bin_i /(n_frequency_bins-1)) * nyquist_frequency # [Å⁻¹]

        # 6b. Compute CTF period in fourier space  
        current_ctf_period = partial_ctf_period(frequency=spatial_frequency) # [Å⁻¹]
        logger.info(f"\tCTF period: {current_ctf_period}[Å⁻¹] > {min_ctf_period}[Å⁻¹]? {current_ctf_period > min_ctf_period}")

        # 6c. If the CTF period exceeds the allowed sampling window
        if current_ctf_period > min_ctf_period:
            bin_result       = bin_i
            frequency_result = spatial_frequency
            found = True
            break # return (bin index, spatial frequency) at aliasing limit

    if found:
        logger.info(f"Highest alias-free frequency: {frequency_result} [Å⁻¹] at bin #{bin_result}, resolution {1/frequency_result:.2f} [Å]")
    else:
        logger.warning(f"No alias-free; returning Nyquist {frequency_result} [Å⁻¹] ({1/frequency_result:.2f} Å) ")
    logger.info("")

    return bin_result, frequency_result

def phaseshift_ctf(box_size, pixel_size_A_per_pix, lambda_A, defocus_A, cs_A):
    r'''
    from: Principles of Phase Contrast (Electron) Microscopy - Marin van Heel
        - PhCTF(f) = sin(\frac{2\pi}{\lambda}[\frac{-C_s \lambda ^4 f^4}{4} + \frac{\Delta F \lambda ^2 f^2}{2}])

    arguments:
        - lambda_A: relativistic electron wavelength in Å
        - pixel_size_A_per_pix
        - defocus_A: positive for underfocus
        - cs_A
        - boxsize
        
    '''
    freq = np.fft.rfftfreq(box_size, d=pixel_size_A_per_pix)

    # complete
    # a = 2*np.pi/lambda_A
    # b = -(cs* lambda_A**4 * f**4)/4
    # c = (defocus_A * lambda_A**2 * f**2)/2
    # gamma = a*(b+c) # =: phase_shift
    # phaseshift_ctf = np.sin(gamma)

    # simplified
    f2 = freq**2
    a = (cs_A * (lambda_A**3) * f2)/2
    b = defocus_A * lambda_A
    gamma = np.pi*f2*(a-b)
    phaseshift_ctf = -np.sin(gamma)

    return {"frequency"     : freq,
            "phaseshift_ctf": phaseshift_ctf}

def phaseshift_ctf2d(lambda_, pixel_size, defocus, cs, boxsize):
    nyquist = 1/(2*pixel_size)
    # f  = nyquist/(boxsize//2) * np.arange(1+boxsize//2, dtype=np.float64)
    f = np.fft.fftshift(np.fft.fftfreq(boxsize, d=pixel_size))
    
    fx, fy = np.meshgrid(f, f)
    s = np.sqrt(fx**2 + fy**2)
    
    s2 = s**2
    a = (cs * lambda_**3 * s2)/2
    b = defocus * lambda_
    gamma = np.pi*s2*(a+b)
    phaseshift_ctf = -np.sin(gamma)    

    return s, phaseshift_ctf

if __name__ == "__main__": #*
	# python ctf.py -b 400 -p 1.2 -v 300 -d -0.8 -c 2.7 --verbose
    ########## CLI setup ##########
    parser = argparse.ArgumentParser(description="Estimate the CTF aliasing limit based on microscope parameters.")	
    parser.add_argument("-b", "--boxsize",    type=int,   required=True, help="Boxsize in pixels (size of the extracted image square).")
    parser.add_argument("-p", "--pixel_size", type=float, required=True, help="Pixel size in [Å].")
    parser.add_argument("-v", "--voltage",    type=float, required=True, help="Microscope accelerating voltage in [kV].")
    parser.add_argument("-d", "--defocus",    type=float, required=True, help="Defocus value in micrometers [µm].")
    parser.add_argument("-c", "--cs",         type=float, required=True, help="Spherical aberration constant (Cs) in millimeters [mm].")
    parser.add_argument("--sparx", action="store_true", help="Follow EMAN2/SPARX behavior (off-by-one and downward scan).")

    args = utils.cli.init_cli(__myname__, parser) # check the docstring for complete behavior; args.output_path is the resolved run directory
    ##### / #####

    # computation
    if not args.sparx:
        result = ctf_limit(box_size  = args.boxsize, 
                        pixel_size_A = args.pixel_size,
                        voltage_kV   = args.voltage,
                        defocus_A    = args.defocus*1e4,# Convert µm to Å
                        cs_A         = args.cs*1e7,     # Convert mm to Å,
                        min_bins_per_cycle = 2)
    else:
        result = ctf_limit_sparx(box_size     = args.boxsize, 
                                 pixel_size_A = args.pixel_size,
                                 voltage_kV   = args.voltage,
                                 defocus_um   = args.defocus,
                                 cs_mm        = args.cs)

    # output interface
    result_dict = {"bin":int(result[0]),
                   "frequency":float(result[1]),
                   "resolution":float(1/result[1])}
    
    # print and save output
    output = utils.output.print_and_save(result_dict, 
                                         print_as="json" if args.json else "yaml",
                                         filepath=os.path.join(args.output_path, __myname__) if args.output_path else None)
    logger.info(f"Result:\n{output['yaml']}")
    logger.info(f"Exiting...")
    logger.info("-"*40)