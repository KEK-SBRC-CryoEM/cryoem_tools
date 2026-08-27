import numpy as np

def decimal_places_for_fraction(denominator):
    """
    Returns the exact number of decimal places a fraction will have.
    Returns np.inf if it's an infinite decimal.
    """
    p2 = 0
    while denominator % 2 == 0:
        p2 += 1
        denominator //= 2
    
    p5 = 0
    while denominator % 5 == 0:
        p5 += 1
        denominator //= 5
        
    return max(p2, p5) if denominator == 1 else np.inf

def prime_factors(n):
    """
    Returns the prime factors of n as a tuple.
    """
    # it could be adjusted to return powers if necessary
    
    # guard
    if n==0: 
        return None
    
    factors = []

    for p in range(2, int(np.sqrt(n)) + 1):
        if n % p == 0:
            factors.append(p)
            while n % p == 0:
                n //= p

    if n > 1:
        factors.append(n)

    return tuple(factors)

def prime_factorization(n, allowed_primes=(2,3,5,7,11,13)):
    # guard
    if n==0: 
        return None
        
    remainder = abs(n)
    factors = {} 
    # try all allowed primes
    for prime in allowed_primes:
        # divide by prime^power
        power = 0
        while remainder % prime == 0:
            remainder //= prime
            power += 1
        factors[prime] = power

    # there is a prime factor that is not in the allowed group
    if remainder!=1:
        return None
    return factors

def prime_factors_to_str(factors: dict):
    # dict output from prime_factorization
    terms = [f"{k}^{v}" if v > 0 else str(k) for k, v in factors.items() if v != 0]
    return " x ".join(terms) if terms else "1"

def has_allowed_prime_factors(n, allowed_primes=(2,3,5,7,11,13)):
    """
    Check if the prime factors of a number n are in the allowed_primes set
    """
    for p in allowed_primes:
        while n % p == 0: n //= p
    return n == 1
