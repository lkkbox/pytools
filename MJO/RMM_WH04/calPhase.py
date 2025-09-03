import numpy as np

def calPhase(pc1, pc2):
    angleDeg = np.angle(pc1 + 1j * pc2) / np.pi * 180
    phase = np.nan * np.ones_like(pc1)

    phase[( 0<= angleDeg) & (angleDeg < 45)] = 5
    phase[( 45<= angleDeg) & (angleDeg < 90)] = 6
    phase[( 90<= angleDeg) & (angleDeg < 135)] = 7
    phase[( 135<= angleDeg) & (angleDeg <= 180)] = 8
    phase[( -180<= angleDeg) & (angleDeg < -135)] = 1
    phase[( -135<= angleDeg) & (angleDeg < -90)] = 2
    phase[( -90<= angleDeg) & (angleDeg < -45)] = 3
    phase[( -45<= angleDeg) & (angleDeg < 0)] = 4
    return phase
