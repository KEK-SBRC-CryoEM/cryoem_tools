# CTFLimit
This is my personal notes when studying the `ctflimit` and `ctfperiod` functions which are implemented in [`morphology.py`](https://github.com/cryoem/eman2/blob/master/sparx/libpy/morphology.py) from the `EMAN2/SPARX` package, and published in **"CTER—Rapid estimation of CTF parameters with error assessment"** [(Penczek et al., 2014)](https://www.sciencedirect.com/science/article/pii/S0304399114000199).

**Goal:** Given the CTF and a box size; up to which frequency can be represented without aliasing? 
- The CTF has a local period, the sampling grid has a spacing, and it needs enough samples per period. 
- As such, we are trying to find the spacing $T$ in an oscillation ($f+T$ to $f$) and check if it is wide enough to be represented by 2 fourier pixels.
- Worth noting, we are interested in a complete cycle ($2\pi$), not from one zero-crossing to another (half-cycle) and not necessarily peak-to-peak.

$$
\gamma(f + T) - \gamma(f) = - 2\pi \tag{0}
$$

The $−2\pi$ advance means $T$ is negative, this interval $T$ is the cycle below $f$. As such, at the end, we take $|T|$.

where 

$$
\frac{\gamma(f)}{2 \pi}   = \left( \frac{\Delta Z \lambda f^2}{2}  - \frac{C_s \lambda^3 f^4}{4} \right) \tag{1}
$$

and

| | | |
|---|---|---|
| **$T$**:        | frequency interval in one full CTF cycle | $[Å^{-1}]$
| **f**:          | frequency                                | $[Å^{-1}]$
| **$\Delta Z$**: | defocus (positive for underfocus)        | $[Å]$ = [µm] $×1e4$
| **$\lambda$**:  | relativistically corrected electron wave length | $[Å]$
| **$C_s$**:      | spherical aberration constant            | $[Å]$ = [mm] $×1e7$

equivalently

$$
\frac{\gamma(f+T)}{2 \pi}   = \left( \frac{\Delta Z \lambda (f+T)^2}{2}  - \frac{C_s \lambda^3 (f+T)^4}{4} \right)  \tag{2}
$$

---
\
Expanding the squares in $(2)$:


$(3)$ $
(f+T)^2 = f^2 + 2 f T + T^2 
$ 

$(4)$ $
(f+T)^4 = f^4 + 4 f^3 T + 6 f^2 T^2 + 4 f T^3 + T^4
$ 

Substituing $(3)$ and $(4)$ into $(2)$:
 
$$
\frac{\gamma(f)}{2 \pi} = \left( \frac{\Delta Z \lambda (f^2 + 2 f T + T^2)}{2}  - \frac{C_s \lambda^3 (f^4 + 4 f^3 T + 6 f^2 T^2 + 4 f T^3 + T^4)}{4} \right) \tag{5}
$$

--- 

Applying distributive: 
- (5a) $0.5 \Delta Z \lambda f^2$
- (5b) $0.5 \Delta Z \lambda 2 f T$
- (5c) $0.5 \Delta Z \lambda T^2$

and

- (5d) $- 0.25 C_s \lambda^3 f^4$
- (5e) $- 0.25 C_s \lambda^3 4 f^3 T$
- (5f) $- 0.25 C_s \lambda^3 6 f^2 T^2$
- (5g) $- 0.25 C_s \lambda^3 4 f T^3$
- (5h) $- 0.25 C_s \lambda^3 T^4$

---

Applying the sign from $(0)$ into $(1)$:

$(6)$ $
\left( - \frac{\Delta Z \lambda f^2}{2}  + \frac{C_s \lambda^3 f^4}{4} \right)
$

and lets call
- (6a) $- 0.5 \Delta Z \lambda f^2$
- (6b) $0.25 C_s \lambda^3 f^4$

Simplifying, $(5)$ and $(6)$ into $(0)$:
- (5a) opposes (6a) -> 0
- (5d) opposes (6b) -> 0

Resulting in:

$$

0.5  \Delta Z \lambda   2 f   T 
+ 0.5  \Delta Z \lambda                 T^2 \\
- 0.25 C_s      \lambda^3 4 f^3 T 
- 0.25 C_s      \lambda^3 6 f^2 T^2
- 0.25 C_s      \lambda^3 4 f   T^3
- 0.25 C_s      \lambda^3               T^4
+ 1
= 0
\tag{7}
$$

--- 
\
To align with CTF Period, lets multiply by -1 and lets name the terms:

| Name | | | | | | |
| :--- | :--- | :---   | :---:      | :---:       | ---:    | ---:    | 
| (7a) |  $-$ | $0.5$  | $\Delta Z$ | $\lambda$   | $2 f$   |  $T$    |
| (7b) |  $-$ | $0.5$  | $\Delta Z$ | $\lambda$   |         |  $T^2$  |
| (7c) |  $+$ | $0.25$ | $C_s$      | $\lambda^3$ | $4 f^3$ |  $T$    |
| (7d) |  $+$ | $0.25$ | $C_s$      | $\lambda^3$ | $6 f^2$ |  $T^2$  |
| (7e) |  $+$ | $0.25$ | $C_s$      | $\lambda^3$ | $4 f$   |  $T^3$  |
| (7f) |  $+$ | $0.25$ | $C_s$      | $\lambda^3$ |         |  $T^4$  |
| (7g) |  $-$ | 1 | | | | |
|      |  $=$ | 0 | | | | |

Grouping by terms:

$T^4$: (7f)
- $+ 0.25 C_s      \lambda^3$

$T^3$: (7e)
- $+ 0.25 C_s      \lambda^3 4 f$

$T^2$: $(7b+7d)$
- $- 0.5  \Delta Z \lambda               + 0.25 C_s \lambda^3 6 f^2$

$T^1$: (7a+7c)
- $- 0.5  \Delta Z \lambda   2 f + 0.25 C_s \lambda^3 4 f^3$

$T^0$: (7g)
- $- 1$

---
\
Finally, T is found by solving $(7)$ as a 4th order polynomial. The physical root is negative (from all 4 possible ones) since we are looking from $f$ towards the lower frequency $f+T$. The code takes the smallest $|T|$ (is the smallest root always physical?) and compare it against 2 fourier pixels, where: 

$ \text{Fourier pixel width} = 1/(\text{pixel size} × \text{box size})$. 

Aliasing happens when $|T| ≤ 2 × \text{fourier pixels}$.

