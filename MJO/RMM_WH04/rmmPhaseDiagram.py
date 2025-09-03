import numpy as np
import matplotlib.pyplot as plt


def phase_diagram():
    fig, ax = plt.subplots(figsize=(7, 7))
    ##
    angles = np.linspace(0, 2*np.pi, 200)
    ax.plot(np.cos(angles), np.sin(angles), color='k', linewidth=0.5)

    thisStyle = {'color': 'k', 'linewidth': 0.5, 'linestyle': '--'}
    ax.plot([0,  0], [1, 4], **thisStyle)
    ax.plot([0,  0], [-1, -4], **thisStyle)
    ax.plot([1,  4], [0, 0], **thisStyle)
    ax.plot([-1, -4], [0, 0], **thisStyle)
    s2 = np.sqrt(2)/2
    ax.plot([-s2,  -4], [-s2, -4], **thisStyle)
    ax.plot([s2,   4], [-s2, -4], **thisStyle)
    ax.plot([-s2,  -4], [s2,  4], **thisStyle)
    ax.plot([s2,   4], [s2,  4], **thisStyle)

    thisStyle = {'color': 'k', 'fontsize': 14}
    d1, d2 = 1.5, 3.5
    ax.text(-d2, -d1, str(1), **thisStyle)
    ax.text(-d1, -d2, str(2), **thisStyle)
    ax.text(d1, -d2, str(3), **thisStyle)
    ax.text(d2, -d1, str(4), **thisStyle)
    ax.text(d2,  d1, str(5), **thisStyle)
    ax.text(d1,  d2, str(6), **thisStyle)
    ax.text(-d1,  d2, str(7), **thisStyle)
    ax.text(-d2,  d1, str(8), **thisStyle)

    thisStyle = {
        'verticalalignment': 'center',
        'horizontalalignment': 'center',
        'fontsize': 14
    }
    ax.text(
        0, -3.5, 'Indian\nOcean', rotation=0, **thisStyle
    )
    ax.text(
        3.5, 0, 'Maritime\nContinent', rotation=-90, **thisStyle
    )
    ax.text(
        0, 3.5, 'Western\nPacific', rotation=0, **thisStyle
    )
    ax.text(
        -3.5, 0, 'West. Hemi.\nand Africa', rotation=90,  **thisStyle
    )

    ax.axis('equal')
    ax.set_xticks(np.r_[-4:4.5:1])
    ax.set_yticks(np.r_[-4:4.5:1])
    ax.set_xticks(np.r_[-4:4.5:0.5], minor=True)
    ax.set_yticks(np.r_[-4:4.5:0.5], minor=True)
    ax.set_xlim((-4.0, 4.0))
    ax.set_ylim((-4.0, 4.0))

    ax.set_xlabel('PC1')
    ax.set_ylabel('PC2')

    ax.tick_params(axis='both', which='major', length=8)
    ax.tick_params(axis='both', which='minor', length=4)
    return fig, ax
