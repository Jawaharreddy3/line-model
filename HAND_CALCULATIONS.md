# Hand calculations (for theory slide and for checking the code)

Common data: Z0 = 50 ohm, f = 100 MHz, vf = 1.0 (air). All numbers match `line_model.py`.

lambda = c/f = 3×10^8 / 10^8 ≈ 3.00 m (exact c = 2.99792458 m)
beta = 2*pi/lambda = 2.0958 rad/m

**1. Matched, ZL = 50:** Gamma_L = 0, Zin = Z0 = 50 ohm for any length.

**2. Short, l = lambda/8 (beta*l = 45 deg):** Zin = j*50*tan(45) = +j50 ohm (inductive).

**3. Open, l = lambda/8:** Zin = -j*50*cot(45) = -j50 ohm (capacitive).

**4. Quarter-wave, ZL = 100:** Zin = 50^2/100 = 25 ohm. Gamma_L = 1/3, VSWR = (1+1/3)/(1-1/3) = 2.

**5. Half-wave, ZL = 30 + j40:** Zin = ZL (repeats every lambda/2).

**6. Transformer example, 50 -> 200 ohm:** Zt = sqrt(50*200) = 100 ohm, length = lambda/4 (0.75 m at 100 MHz, vf=1).

**7. Short at lambda/4:** Zin -> infinity (looks open); open at lambda/4 -> 0 (looks short).
