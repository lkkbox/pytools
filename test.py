#!/usr/bin/env python

TESTSDIR = './tests'

def main():
    test_plot_coastlines()
    # test_config()


def test_plot_coastlines():
    import plottools as pt
    import matplotlib.pyplot as plt
    import matplotlib
    matplotlib.use("Agg")

    fig = plt.figure()
    ax = fig.add_subplot()
    ax.set_xlim([0, 360])
    ax.set_ylim([-90, 90])
    pt.plotcoast(ax, color='k')
    fig.savefig(f'./{TESTSDIR}/test_plot_coastlines_0.png')


def test_config():
    from pytools import config
    out = config.load_config('nothing')
    if out is None:
        print('> 1 passed')

    out = config.load_config(['nothing1', 'nothing2'])
    if out == [None, None]:
        print('> 2 passed')

    out = config.load_config('etopo_coastlines_0p1')
    if isinstance(out, str):
        print('> 3 passed')




if __name__ == '__main__':
    main()
