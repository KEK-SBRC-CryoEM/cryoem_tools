import numpy as np

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

