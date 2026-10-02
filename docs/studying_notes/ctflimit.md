# CTFLimit
This is my personal notes when studying the `ctflimit` and `ctfperiod` functions which are implemented in [`morphology.py`](https://github.com/cryoem/eman2/blob/master/sparx/libpy/morphology.py) from the `EMAN2/SPARX` package, and published in **"CTER—Rapid estimation of CTF parameters with error assessment"** [(Penczek et al., 2014)](https://www.sciencedirect.com/science/article/pii/S0304399114000199).

**Goal:** Given the CTF and a box size; up to which frequency can be represented without aliasing? 
- The CTF has a local period, the sampling grid has a spacing, and it needs enough samples per period. 
- As such, we are trying to find the spacing $T$ in an oscillation ($f+T$ to $f$) and check if it is wide enough to be represented by 2 fourier pixels.
- Worth noting, we are interested in a complete cycle ($2\pi$), not from one zero-crossing to another (half-cycle) and not necessarily peak-to-peak.

$$
\gamma(f + T) - \gamma(f) = {- 2\pi} \qquad (0)
$$

The $−2\pi$ advance means $T$ is negative, this interval $T$ is the cycle below $f$. As such, at the end, we take $|T|$.

where 

$$
\frac{\gamma(f)}{2 \pi}   = \left( \frac{\Delta Z \lambda f^2}{2}  - \frac{C_s \lambda^3 f^4}{4} \right) \qquad (1)
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
\frac{\gamma(f+T)}{2 \pi}   = \left( \frac{\Delta Z \lambda (f+T)^2}{2}  - \frac{C_s \lambda^3 (f+T)^4}{4} \right)  \qquad (2)
$$

---
\
Expanding the squares in $(2)$:

$$
\begin{array}{rlr}
(f+T)^2 & {}= f^2 + 2 f T + T^2 \qquad (3) \\
(f+T)^4 & {}= f^4 + 4 f^3 T + 6 f^2 T^2 + 4 f T^3 + T^4 \qquad (4)
\end{array}
$$

Substituing $(3)$ and $(4)$ into $(2)$:
 
$$
\frac{\gamma(f)}{2 \pi} = \left( \frac{\Delta Z \lambda (f^2 + 2 f T + T^2)}{2}  - \frac{C_s \lambda^3 (f^4 + 4 f^3 T + 6 f^2 T^2 + 4 f T^3 + T^4)}{4} \right) \qquad (5)
$$

--- 

Applying distributive:

$$
\begin{array}{llcll}
\text{(5a)} \qquad & 0.5 \Delta Z \lambda &   & f^2 &     \\
\text{(5b)} \qquad & 0.5 \Delta Z \lambda & 2 & f   & T   \\
\text{(5c)} \qquad & 0.5 \Delta Z \lambda &   &     & T^2
\end{array}
$$

and

$$
\begin{array}{lcllr}
\text{(5d)} \qquad {-0.25} C_s \lambda^3 &   & f^4 &     \\
\text{(5e)} \qquad {-0.25} C_s \lambda^3 & 4 & f^3 & T   \\
\text{(5f)} \qquad {-0.25} C_s \lambda^3 & 6 & f^2 & T^2 \\
\text{(5g)} \qquad {-0.25} C_s \lambda^3 & 4 & f   & T^3 \\
\text{(5h)} \qquad {-0.25} C_s \lambda^3 &   &     & T^4 
\end{array}
$$

---

Applying the sign from $(0)$ into $(1)$:

$$
\left( - \frac{\Delta Z \lambda f^2}{2}  + \frac{C_s \lambda^3 f^4}{4} \right) \qquad (6)
$$

and lets call

$$
\begin{array}{lclcll}
\text{(6a)} \qquad & - & 0.5  & \Delta Z & \lambda   & f^2 \\
\text{(6b)} \qquad & + & 0.25 & C_s      & \lambda^3 & f^4
\end{array}
$$

Simplifying, $(5)$ and $(6)$ into $(0)$:
- (5a) opposes (6a) -> 0
- (5d) opposes (6b) -> 0

Resulting in:

$$
\begin{aligned}
& 0.5  \Delta Z \lambda   2 f   T + 0.5  \Delta Z \lambda T^2 \\
& \qquad - 0.25 C_s      \lambda^3 4 f^3 T - 0.25 C_s      \lambda^3 6 f^2 T^2 \\
& \qquad - 0.25 C_s      \lambda^3 4 f   T^3 - 0.25 C_s      \lambda^3               T^4 + 1 = 0 \qquad (7)
\end{aligned}
$$

--- 
\
To align with CTF Period, lets multiply by -1 and lets name the terms:

$$
\begin{array}{lclclcll}
\text{(7a)} \qquad & - & 0.5  & \Delta Z & \lambda   & 2 & f   & T   \\
\text{(7b)} \qquad & - & 0.5  & \Delta Z & \lambda   &   &     & T^2 \\
\text{(7c)} \qquad & + & 0.25 & C_s      & \lambda^3 & 4 & f^3 & T   \\
\text{(7d)} \qquad & + & 0.25 & C_s      & \lambda^3 & 6 & f^2 & T^2 \\
\text{(7e)} \qquad & + & 0.25 & C_s      & \lambda^3 & 4 & f   & T^3 \\
\text{(7f)} \qquad & + & 0.25 & C_s      & \lambda^3 &   &     & T^4 \\
& - & 1 \\
& = & 0
\end{array}
$$

Grouping by terms:

$T^{4}: \qquad \text{(7f)} \qquad {+ 0.25} C_s      \lambda^3$ 

$T^{3}: \qquad \text{(7e)} \qquad {+ 0.25} C_s      \lambda^3 4 f$

$T^{2}: \qquad \text{(7b+7d)} \qquad {- 0.5}  \Delta Z \lambda               + 0.25 C_s \lambda^3 6 f^2$

$T^{1}: \qquad \text{(7a+7c)} \qquad {- 0.5}  \Delta Z \lambda   2 f + 0.25 C_s \lambda^3 4 f^3$

$T^{0}: \qquad \text{(7g)} \qquad {- 1}$

---
\
Finally, T is found by solving $(7)$ as a 4th order polynomial. The physical root is negative (from all 4 possible ones) since we are looking from $f$ towards the lower frequency $f+T$. The code takes the smallest $|T|$ (is the smallest root always physical?) and compare it against 2 fourier pixels, where: 

$\text{Fourier pixel width} = 1/(\text{pixel size } × \text{ box size})$. 

Aliasing happens when $|T| ≤ 2 × \text{fourier pixels}$.

