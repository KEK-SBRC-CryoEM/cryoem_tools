import numpy as np

def relativistic_electron_wavelength_A(voltage_kV):
    """
    Calculate the relativistically corrected deBroglie wavelength of an electron.
    
    Parameters:
        voltage_kV (float): accelerating voltage in kV
        
    Returns:
        lambda_A (float): the relativistically corrected electron wavelength in Ångströms [Å]

    Constants:
        1022   = 2*rest_energy (electron rest energy = 511 [keV])
        12.398 = h*c [eV Å] from Planck's constant [Js] and speed of light [m/s]

    Source: 
        @Inbook{Tanaka2024,
            author    = "Tanaka, Nobuo",
            title     = "Relativistic Effects to Diffraction and Imaging by a Transmission Electron Microscope---Basic Theories for High-Voltage Electron Microscopy",
            bookTitle = "Electron Nano-imaging: Basics of Imaging and Diffraction for TEM and STEM",
            year      = "2024",
            publisher = "Springer Japan",
            address   = "Tokyo",
            isbn      = "978-4-431-56940-4",
            doi       = "10.1007/978-4-431-56940-4_31",
            url       = "https://doi.org/10.1007/978-4-431-56940-4_31"
            note      = {Chapter 1.4, Equation 1.3, Page 11}
        }
    """
    return 12.398 / np.sqrt(voltage_kV * (1022.0 + voltage_kV)) # [Å]

def ctf_delocalization_distance_A(particle_diameter_A, lambda_A, resolution_A, defocus_A):
    """
    Calculate the physical distance required to capture "Fresnel fringes"
        around a particle in real space caused by CTF-induced delocalization.

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
