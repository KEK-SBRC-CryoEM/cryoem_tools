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

