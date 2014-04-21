#!/usr/bin/env python
import os, sys
import argparse, itertools
import numpy as np

from constants import *


###############
# Parse args
###############
def check_mode(mode):
    try:
        m = int(mode)
        if (m < 0) or (m >= len(MODES)):
            raise argparse.ArgumentTypeError('Invalid mode')
        return m
    except:
        raise argparse.ArgumentTypeError('Invalid mode')

parser = argparse.ArgumentParser(description='Plots parsed experimental data values.')
parser.add_argument('mode', type=check_mode,
                    help='mode to use: 0 for time, 1 for memory, 2 for network')

# additional mode options
parser.add_argument('--master', action='store_true', default=False,
                    help='plot mem/net statistics for the master rather than the worker machines (only relevant for mode=1,2)')
parser.add_argument('--premizan', action='store_true', default=False,
                    help='plot mem/net statistics for premizan, Mizan\'s graph partitioner (only relevant for mode=1,2)')
parser.add_argument('--total-time', action='store_true', default=False,
                    help='plot total time (stacked bars) instead of separate setup and computation times (only revelant for mode=0)')
parser.add_argument('--avg-memory', action='store_true', default=False,
                    help='plot only average memory usage, instead of min, max, and average (only revelant for mode=1)')

# save related items
parser.add_argument('--save-png', action='store_true', default=False,
                    help='save plots as PNG files (200 DPI) instead of displaying them')
eps_group = parser.add_mutually_exclusive_group()
eps_group.add_argument('--save-eps', action='store_true', default=False,
                       help='save plots as EPS files instead of displaying them')
eps_group.add_argument('--save-paper', action='store_true', default=False,
                       help='save plots as EPS files for paper (uses large text labels)')

mode = parser.parse_args().mode
do_master = parser.parse_args().master
do_premizan = parser.parse_args().premizan
do_time_tot = parser.parse_args().total_time
do_avg_only = parser.parse_args().avg_memory

save_png = parser.parse_args().save_png
save_eps = parser.parse_args().save_eps
save_paper = parser.parse_args().save_paper

# save_paper is just a special case of save_eps
if save_paper:
    save_eps = True


# import data
if mode == MODE_TIME:
    from data_time import *

elif mode == MODE_MEM:
    if do_master:
        from data_mem_master import *
    else:
        from data_mem import *

elif mode == MODE_NET:
    if do_master:
        from data_net_master import *
    else:
        from data_net import *

# we have to import matplotlib.pyplot here, as its backend
# will get reset if we don't import matplotlib first
import matplotlib
matplotlib.rcParams['figure.max_open_warning'] = 41

if save_eps:
    # using tight_layout will cause this to be Agg...
    matplotlib.use('PS')

import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator
from matplotlib.ticker import MaxNLocator

###############
# Format data
###############
# Genneral conventions:
#
# For each plot, bars represent a particular system in a partciular mode.
# Bars are clustered/grouped by the number of machines used in the experiment.
# Finally, plots are separated into different figures based on algorithm + graph.
#
# Additionally, each "mode" (time, mem, or net) can have multiple different
# "plot types". These are just extra figures that display more data.
#
# E.g., using gen-data's output variable names:
#
# <giraph_0>_<16>_<pagerank_livejournal>_<run_avg>
# single bar   ^         figure            value
#          bar group


## Matrix for one alg and one graph, with rows indexed by system + system mode
## and columns indexed by number of machines
#alg_graph_run_avg = [[system + '_' + sysmode + '_' + machines + '_alg_graph_run_avg'
#                      for machines in MACHINES]
#                     for (system,sysmode) in ALL_SYS]
#
## Tuple of matrices for a particular algorithm
#alg_run_avg = [[[system + '_' sysmode + '_' + machines + '_alg_' + graph + '_run_avg'
#                 for machines in MACHINES]
#                for (system,sysmode) in ALL_SYS]
#               for graph in GRAPHS]
#
## Tuple of tuples of matrics for one particular statistic
#run_avg = = [[[[system + '_' + sysmode + '_' + machines + '_' + alg + '_' + graph + '_run_avg'
#                for (system,sysmode) in ALL_SYS]
#               for machines in MACHINES]
#              for graph in GRAPHS]
#             for alg in ALGS]

# Use eval to get the value of the variable name given by the string
stats_dict = {stat + suffix: megatuple
              for (stat,suffix) in itertools.product(STATS[mode],('_avg', '_ci'))
              for megatuple in
              np.array([[[[[eval(system + '_' + sysmode + '_' + machines + '_' + alg + '_' + graph + '_' + stat + suffix)
                            for machines in MACHINES]
                           for (system,sysmode) in ALL_SYS]
                          for graph in GRAPHS]
                         for alg in ALGS]])}

# Premizan is special case. Each entry is a tuple of matrices,
# whose rows are all 0s except for the Mizan row. This Mizan row
# holds premizan stats.
#
# This setup is only relevant for plotting time (which needs permizan
# as an extra I/O add-on for Mizan).
#
# "+" between matrices joins Mizan row (premizan data) with the 0s matrix.
# TODO: constants hacked in..
premizan_dict = {stat + suffix: megatuple
                 for (stat,suffix) in itertools.product(STATS[mode],('_avg', '_ci'))
                 for megatuple in
                 np.array([[[[0]*len(MACHINES)]*(len(ALL_SYS)-3)
                            + [[eval(SYS_MIZAN + '_' + SYSMODE_HASH + '_' + machines + '_' + ALG_PREMIZAN + '_' + graph + '_' + stat + suffix)
                                for machines in MACHINES]]
                            + [[0]*len(MACHINES)]*2
                            for graph in GRAPHS]])}


# Simple way to handle premizan: just plot 0s for all the other systems.
# HACK: yes, we're changing the constant ALGS...
if do_premizan:
    stats_dict = {key: np.array([val]) for key, val in premizan_dict.iteritems()}
    premizan_dict = {key: np.array([[[0]*len(MACHINES)]*len(ALL_SYS)]*len(GRAPHS)) for key in premizan_dict}
    ALGS = ('premizan',)


####################
# Plot constants
####################
PLOT_TYPES = (('time_tot' if do_time_tot else 'time_split',),  # time
              ('mem_avg' if do_avg_only else 'mem',),          # mem
              ('recv', 'sent'))                                # net

# decoration
# more chars = denser patterns; can also mix and match different ones
PATTERNS = ('..','*',             # Giraph
            '///','o','\\\\\\',   # GPS
            'xx',                 # Mizan
            '++', 'O')            # GraphLab

# old: #ff7f00 (orange), #1f78b4 (blue), #7ac36a (darker green)
COLORS = ('#faa75b','#faa75b',            # Giraph
          '#5a9bd4','#5a9bd4','#5a9bd4',  # GPS
          '#b2df8a',                      # Mizan
          '#eb65aa','#eb65aa')            # GraphLab

COLOR_PREMIZAN = '#737373'
COLOR_IO = (0.9, 0.9, 0.9)
COLOR_ERR = (0.3, 0.3, 0.3)

# labels
LEGEND_LABELS = ('Giraph (byte array)', 'Giraph (hash map)',
                 'GPS (none)', 'GPS (LALP)', 'GPS (dynamic)',
                 'Mizan (static)',
                 'Graphlab (sync)', 'GraphLab (async)')

# all possible graph labels
# must be an array, b/c we use np's list slicing
GRAPH_LABELS = np.array((('LJ (16)', 'LJ (32)', 'LJ (64)', 'LJ (128)'),
                         ('OR (16)', 'OR (32)', 'OR (64)', 'OR (128)'),
                         ('AR (16)', 'AR (32)', 'AR (64)', 'AR (128)'),
                         ('TW (16)', 'TW (32)', 'TW (64)', 'TW (128)'),
                         ('UK (16)', 'UK (32)', 'UK (64)', 'UK (128)')))

if save_paper:
    FONTSIZE = 20
    VAL_FONTSIZE = 5   # for "F" of failed bars
elif save_eps and (not save_paper):
    FONTSIZE = 12
    VAL_FONTSIZE = 4   # for text values on top of bars
else:
    FONTSIZE = 12      # 12 is default
    VAL_FONTSIZE = 8

# left/right margins of each bar group
BAR_MARGIN = 0.05

# how much extra space to leave at the top of each plot
YMAX_FACTOR = 1.05

# location of bar groups (changes depending on # of machines)
IND = np.array([np.arange(len(g))+BAR_MARGIN for g in GRAPH_LABELS])


####################
# Plot functions
####################
# label formats indexed by mode
LABEL_FORMAT = ('%0.2f', '%0.2f', '%0.1f')

def autolabel(bar):
    """Labels a bar with text values."""
    # get_y() needed to output proper total time
    height = bar.get_height() + bar.get_y()

    # values will never be small enough to cause issues w/ this comparison
    if height == 0:
        plt.text(bar.get_x()+bar.get_width()/2.0, 0, 'F',
                 ha='center', va='bottom', fontsize=VAL_FONTSIZE+2)
    else:
        if not save_paper:
            plt.text(bar.get_x()+bar.get_width()/2.0, height*1.005, LABEL_FORMAT[mode]%float(height),
                     ha='center', va='bottom', fontsize=VAL_FONTSIZE)


def plot_time_tot(plt, fignum, ai, gi, si, mi, ind, width):
    """Plots total computation time (separated into I/O, premizan, and computation time).

    Arguments:
    plt -- matplotlib.pyplot being used
    fignum -- figure number (int)
    ai -- algorithm index (int)
    gi -- graph index (int)
    si -- system indices, for plotting all or a subset of the systems (list/range)
    mi -- machine indices, for plotting all or a subset of the machines (list/range)
    ind -- left x-location of each bar group (list/range)
    width -- width of each bar

    Returns:
    Tuple of axes.
    """

    # TODO: strings are hard coded...

    # this is generated implicitly by default, but we need to return it
    ax = plt.subplot()

    # don't show premizan bar if comuptation time is 0 (i.e., failed run)
    premizan_avg = np.array([[0.0 if stats_dict['run_avg'][ai,gi,si][i,j] == 0 else val
                              for j,val in enumerate(arr)]
                             for i,arr in enumerate(premizan_dict['io_avg'][gi,si])])

    premizan_ci = np.array([[0.0 if stats_dict['run_avg'][ai,gi,si][i,j] == 0 else val
                             for j,val in enumerate(arr)]
                            for i,arr in enumerate(premizan_dict['io_ci'][gi,si])])

    # Each (implicit) iteration plots one system+sysmode in different groups (= # of machines).
    # "+" does element-wise add as everything is an np.array.
    plt_run = [plt.bar(ind + width*i, avg[mi], width, color=col, hatch=pat,
                       ecolor=COLOR_ERR, yerr=ci[mi], align='edge', bottom=io[mi])
               for i,(avg,ci,io,col,pat) in enumerate(zip(stats_dict['run_avg'][ai,gi,si],
                                                          stats_dict['run_ci'][ai,gi],
                                                          stats_dict['io_avg'][ai,gi,si]+premizan_avg,
                                                          COLORS,
                                                          PATTERNS))]

    # Only need to slice first array in zip()---the rest will get shortened automatically.
    plt_io = [plt.bar(ind + width*i, avg[mi], width, color=COLOR_IO,
                      ecolor=COLOR_ERR, yerr=ci[mi], align='edge')
              for i,(avg,ci) in enumerate(zip(stats_dict['io_avg'][ai,gi,si],
                                              stats_dict['io_ci'][ai,gi]))]

    plt_pm = [plt.bar(ind + width*i, avg[mi], width, color=COLOR_PREMIZAN,
                      ecolor=COLOR_ERR, yerr=ci[mi], align='edge', bottom=io[mi])
              for i,(avg,ci,io) in enumerate(zip(premizan_avg,
                                                 premizan_ci,
                                                 stats_dict['io_avg'][ai,gi]))]

    # label with total time (if not for paper.. otherwise it clutters things)
    for bars in plt_run:
        for bar in bars:
            autolabel(bar)

    #plt.ylim(ymax=np.max(stats_dict['run_avg'][ai,gi,si] + stats_dict['run_ci'][ai,gi,si]
    #                     + premizan_dict['io_avg'][gi,si]
    #                     + stats_dict['io_avg'][ai,gi,si])*YMAX_FACTOR)

    if (not save_paper) or gi == 0:
        plt.ylabel('Total time (mins)')

    return (ax,)


#def plot_time_run(plt, fignum, ai, gi, si, mi, ind, width):
#    """Plots computation time only.
#
#    Arguments:
#    plt -- matplotlib.pyplot being used
#    fignum -- figure number (int)
#    ai -- algorithm index (int)
#    gi -- graph index (int)
#    si -- system indices, for plotting all or a subset of the systems (list/range)
#    mi -- machine indices, for plotting all or a subset of the machines (list/range)
#    ind -- left x-location of each bar group (list/range)
#    width -- width of each bar
#
#    Returns:
#    Tuple of axes.
#    """
#
#    ax = plt.subplot()
#
#    plt_run = [plt.bar(ind + width*i, avg[mi], width, color=col, hatch=pat,
#                       ecolor=COLOR_ERR, yerr=ci[mi], align='edge')
#               for i,(avg,ci,col,pat) in enumerate(zip(stats_dict['run_avg'][ai,gi,si],
#                                                       stats_dict['run_ci'][ai,gi],
#                                                       COLORS,
#                                                       PATTERNS))]
#
#    # label bars with computation times
#    for bars in plt_run:
#        for bar in bars:
#            autolabel(bar)
#
#    #plt.ylim(ymax=np.max(stats_dict['run_avg'][ai,gi,si] + stats_dict['run_ci'][ai,gi,si])*YMAX_FACTOR)
#
#    if (not save_paper) or gi == 0:
#        plt.ylabel('Computation time (mins)')
#    return (ax,)


def plot_time_split(plt, fignum, ai, gi, si, mi, ind, width):
    """Plots I/O + premizan time and computation times in vertically separated subplots.

    This is basically a variant of plot_time_tot, where we don't stack the computation
    time on top of the I/O bars.

    Arguments:
    plt -- matplotlib.pyplot being used
    fignum -- figure number (int)
    ai -- algorithm index (int)
    gi -- graph index (int)
    si -- system indices, for plotting all or a subset of the systems (list/range)
    mi -- machine indices, for plotting all or a subset of the machines (list/range)
    ind -- left x-location of each bar group (list/range)
    width -- width of each bar

    Returns:
    Tuple of axes.
    """

    ax_run = plt.subplot(211)
    plt_run = [plt.bar(ind + width*i, avg[mi], width, color=col, hatch=pat,
                       ecolor=COLOR_ERR, yerr=ci[mi], align='edge')
               for i,(avg,ci,col,pat) in enumerate(zip(stats_dict['run_avg'][ai,gi,si],
                                                       stats_dict['run_ci'][ai,gi],
                                                       COLORS,
                                                       PATTERNS))]

    # label bars with their values
    for bars in plt_run:
        for bar in bars:
            autolabel(bar)

    # using sharey ensures both y-axis are of same scale... but it can waste a lot of space
    #ax_io = plt.subplot(2, 1, 2, sharey=ax_run)
    ax_io = plt.subplot(212)

    plt_io = [plt.bar(ind + width*i, avg[mi], width, color=COLOR_IO, hatch=pat,
                      ecolor=COLOR_ERR, yerr=ci[mi], align='edge')
              for i,(avg,ci,pat) in enumerate(zip(stats_dict['io_avg'][ai,gi,si],
                                                  stats_dict['io_ci'][ai,gi],
                                                  PATTERNS))]

    # don't show premizan bar if comuptation time is 0 (i.e., failed run)
    premizan_avg = np.array([[0.0 if stats_dict['run_avg'][ai,gi,si][i,j] == 0 else val
                              for j,val in enumerate(arr)]
                             for i,arr in enumerate(premizan_dict['io_avg'][gi,si])])

    premizan_ci = np.array([[0.0 if stats_dict['run_avg'][ai,gi,si][i,j] == 0 else val
                             for j,val in enumerate(arr)]
                            for i,arr in enumerate(premizan_dict['io_ci'][gi,si])])


    plt_pm = [plt.bar(ind + width*i, avg[mi], width, color=COLOR_PREMIZAN, hatch=pat,
                      ecolor=COLOR_ERR, yerr=ci[mi], align='edge', bottom=io[mi])
              for i,(avg,ci,io,pat) in enumerate(zip(premizan_avg,
                                                     premizan_ci,
                                                     stats_dict['io_avg'][ai,gi],
                                                     PATTERNS))]

    # label bars with their values
    for bars in plt_pm:
        for bar in bars:
            autolabel(bar)


    # set proper ymax
    #ax_run.set_ylim(ymax=np.max(stats_dict['run_avg'][ai,gi,si] + stats_dict['run_ci'][ai,gi,si])*YMAX_FACTOR)
    #ax_io.set_ylim(ymax=np.max(premizan_dict['io_avg'][gi,si] + premizan_dict['io_ci'][gi,si]
    #                           + stats_dict['io_avg'][ai,gi,si])*YMAX_FACTOR)

    if (not save_paper) or gi == 0:
        ax_run.set_ylabel('Computation (mins)')
        ax_io.set_ylabel('Setup (mins)')

    # remove upper y-label to avoid overlap
    nbins = len(ax_run.get_yticklabels())
    ax_io.yaxis.set_major_locator(MaxNLocator(nbins=nbins, prune='upper'))

    return (ax_run, ax_io)


def plot_mem(plt, fignum, ai, gi, si, mi, ind, width):
    """Plots memory usage (GB per machine).

    Arguments:
    plt -- matplotlib.pyplot being used
    fignum -- figure number (int)
    ai -- algorithm index (int)
    gi -- graph index (int)
    si -- system indices, for plotting all or a subset of the systems (list/range)
    mi -- machine indices, for plotting all or a subset of the machines (list/range)
    ind -- left x-location of each bar group (list/range)
    width -- width of each bar

    Returns:
    Tuple of axes.
    """

    ax = plt.subplot()

    if do_master:
        plt_avg = [plt.bar(ind + width*i, avg[mi], width, color=col, hatch=pat,
                           ecolor=COLOR_ERR, yerr=ci[mi], align='edge')
                   for i,(avg,ci,col,pat) in enumerate(zip(stats_dict['mem_avg_avg'][ai,gi,si]*MB_PER_GB,
                                                           stats_dict['mem_avg_ci'][ai,gi]*MB_PER_GB,
                                                           COLORS,
                                                           PATTERNS))]

        plt_min = plt_max = plt_avg   # master is a single machine, so min/max = avg

    else:
        # NOTE: alpha not supported in ps/eps
        if not do_avg_only:
            plt_max = [plt.bar(ind + width*i, avg[mi], width, color='#e74c3c', alpha=0.6,
                               ecolor=COLOR_ERR, yerr=ci[mi], align='edge')
                       for i,(avg,ci,pat) in enumerate(zip(stats_dict['mem_max_avg'][ai,gi,si],
                                                           stats_dict['mem_max_ci'][ai,gi],
                                                           PATTERNS))]

        plt_avg = [plt.bar(ind + width*i, avg[mi], width, color=col, hatch=pat,
                           ecolor=COLOR_ERR, yerr=ci[mi], align='edge')
                   for i,(avg,ci,col,pat) in enumerate(zip(stats_dict['mem_avg_avg'][ai,gi,si],
                                                           stats_dict['mem_avg_ci'][ai,gi],
                                                           COLORS,
                                                           PATTERNS))]

        if not do_avg_only:
            plt_min = [plt.bar(ind + width*i, avg[mi], width, color='#27ae60', alpha=0.6,
                               ecolor=COLOR_ERR, yerr=ci[mi], align='edge')
                       for i,(avg,ci,pat) in enumerate(zip(stats_dict['mem_min_avg'][ai,gi,si],
                                                           stats_dict['mem_min_ci'][ai,gi],
                                                           PATTERNS))]

        if do_avg_only:
            plt_min = plt_max = plt_avg

    # label all bars
    for plt_mem in (plt_max, plt_avg, plt_min):
        for bars in plt_mem:
            for bar in bars:
                autolabel(bar)

    #plt.ylim(ymax=np.max(stats_dict['mem_max_avg'][ai,gi,si] + stats_dict['mem_max_ci'][ai,gi,si])*YMAX_FACTOR)

    if (not save_paper) or gi == 0:
        if do_master:
            plt.ylabel('Memory usage at master (MB)')
        else:
            if do_avg_only:
                plt.ylabel('Average memory usage (GB per machine)')
            else:
                plt.ylabel('Min/avg/max memory usage (GB per machine)')

    return (ax,)


def plot_net_recv(plt, fignum, ai, gi, si, mi, ind, width):
    """Plots total incoming network usage, summed over all machines.

    Arguments:
    plt -- matplotlib.pyplot being used
    fignum -- figure number (int)
    ai -- algorithm index (int)
    gi -- graph index (int)
    si -- system indices, for plotting all or a subset of the systems (list/range)
    mi -- machine indices, for plotting all or a subset of the machines (list/range)
    ind -- left x-location of each bar group (list/range)
    width -- width of each bar

    Returns:
    Tuple of axes.
    """

    ax = plt.subplot()

    if do_master:
        plt_recv = [plt.bar(ind + width*i, avg[mi], width, color=col, hatch=pat,
                            ecolor=COLOR_ERR, yerr=ci[mi], align='edge')
                    for i,(avg,ci,col,pat) in enumerate(zip(stats_dict['eth_recv_avg'][ai,gi,si]*MB_PER_GB,
                                                            stats_dict['eth_recv_ci'][ai,gi]*MB_PER_GB,
                                                            COLORS,
                                                            PATTERNS))]
    else:
        plt_recv = [plt.bar(ind + width*i, avg[mi], width, color=col, hatch=pat,
                            ecolor=COLOR_ERR, yerr=ci[mi], align='edge')
                    for i,(avg,ci,col,pat) in enumerate(zip(stats_dict['eth_recv_avg'][ai,gi,si],
                                                            stats_dict['eth_recv_ci'][ai,gi],
                                                            COLORS,
                                                            PATTERNS))]

    for bars in plt_recv:
        for bar in bars:
            autolabel(bar)

    #plt.ylim(ymax=np.max(stats_dict['eth_recv_avg'][ai,gi,si] + stats_dict['eth_recv_ci'][ai,gi,si])*YMAX_FACTOR)

    if (not save_paper) or gi == 0:
        if do_master:
            plt.ylabel('Total incoming network I/O (MB)')
        else:
            plt.ylabel('Total incoming network I/O (GB)')

    return (ax,)


def plot_net_sent(plt, fignum, ai, gi, si, mi, ind, width):
    """Plots total outgoing network usage, summed over all machines.

    Arguments:
    plt -- matplotlib.pyplot being used
    fignum -- figure number (int)
    ai -- algorithm index (int)
    gi -- graph index (int)
    si -- system indices, for plotting all or a subset of the systems (list/range)
    mi -- machine indices, for plotting all or a subset of the machines (list/range)
    ind -- left x-location of each bar group (list/range)
    width -- width of each bar

    Returns:
    Tuple of axes.
    """

    ax = plt.subplot()

    if do_master:
        plt_sent = [plt.bar(ind + width*i, avg[mi], width, color=col, hatch=pat,
                            ecolor=COLOR_ERR, yerr=ci[mi], align='edge')
                    for i,(avg,ci,col,pat) in enumerate(zip(stats_dict['eth_sent_avg'][ai,gi,si]*MB_PER_GB,
                                                            stats_dict['eth_sent_ci'][ai,gi]*MB_PER_GB,
                                                            COLORS,
                                                            PATTERNS))]
    else:
        plt_sent = [plt.bar(ind + width*i, avg[mi], width, color=col, hatch=pat,
                            ecolor=COLOR_ERR, yerr=ci[mi], align='edge')
                    for i,(avg,ci,col,pat) in enumerate(zip(stats_dict['eth_sent_avg'][ai,gi,si],
                                                            stats_dict['eth_sent_ci'][ai,gi],
                                                            COLORS,
                                                            PATTERNS))]

    for bars in plt_sent:
        for bar in bars:
            autolabel(bar)

    #plt.ylim(ymax=np.max(stats_dict['eth_sent_avg'][ai,gi,si] + stats_dict['eth_sent_ci'][ai,gi,si])*YMAX_FACTOR)

    if (not save_paper) or gi == 0:
        if do_master:
            plt.ylabel('Total outgoing network I/O (MB)')
        else:
            plt.ylabel('Total outgoing network I/O (GB)')

    return (ax,)


####################
# Generate plots
####################
PLOT_FUNCS = ((plot_time_tot if do_time_tot else plot_time_split,),  # time
              (plot_mem,),                                           # memory
              (plot_net_recv, plot_net_sent))                        # net

fignum = 0

for plt_type,save_suffix in enumerate(PLOT_TYPES[mode]):
    # iterate over all algs (ai = algorithm index)
    for ai,alg in enumerate(ALGS):
        # Not all systems do WCC or DMST, so we have to handle it separately.
        # This removes bars from each group of bars, so change bar width
        # to compensate for # of systems as well.
        # (si = system indices, which slices rows of the matrix)
        si = np.arange(len(ALL_SYS))         # all systems by default
        if (alg == ALG_MST):
            si = np.arange(3)                # only Giraph (hashmap, byte array) and GPS (none)
        elif (alg == ALG_WCC):
            si = np.arange(len(ALL_SYS)-1)   # all except GraphLab async

        width = (1.0 - 2.0*BAR_MARGIN)/len(si)

        # iterate over all graphs (gi = graph index)
        for gi,graph in enumerate(GRAPHS):
            # Not all machine setups can run uk0705, so we remove 16/32's empty bars.
            # This will make the plot thinner (removes 2 groups of bars).
            # (mi = machine indices, which silces columns of the matrix)
            mi = np.arange(len(MACHINES))       # all machines by default
            if (alg == ALG_MST):
                if (graph == GRAPH_UK):
                    # NOTE: using 3,4 causes divide by zero warning in ticker.py
                    # along with poor figure width control..
                    mi = np.arange(2,4)         # only 128 machines, but also show 64
                elif (graph == GRAPH_TW):
                    mi = np.arange(2,4)         # only 64 and 128 machines
            else:
                if (graph == GRAPH_UK):
                    mi = np.arange(2,4)         # only 64 and 128 machines

            # each alg & graph is a separate figure---easier to handle than subplots
            fignum += 1

            # shrink width down if there are bars or groups of bars missing
            width_ratio = (7.0-len(GRAPH_LABELS[gi]))/(7.0-len(mi))
            if save_paper:
                plt.figure(fignum, figsize=(5.0*width_ratio,7), facecolor='w')
            else:
                plt.figure(fignum, figsize=(6.0*width_ratio,6), facecolor='w')

            # mode specific plot function
            axes = PLOT_FUNCS[mode][plt_type](plt, fignum, ai, gi, si, mi, IND[gi,mi], width)

            # title only for the first (upper-most) axis
            if not save_eps:
                axes[0].set_title(alg + ' ' + graph)

            # If there's only one axis, we can just use plt.stuff()...
            # But with mutliple axes we need to go through each one using axis.set_stuff()
            for ax in axes:
                ax.set_ylim(ymin=0)                 # zero y-axis
                ax.minorticks_on()                  # enable all minor ticks

                for item in ([ax.title, ax.xaxis.label, ax.yaxis.label] +
                             ax.get_xticklabels() + ax.get_yticklabels()):
                    item.set_fontsize(FONTSIZE)

                # turn off major and minor x-axis ticks (leaves minor y-ticks on)
                ax.tick_params(axis='x', which='both', bottom='off', top='off')

                ax.grid(True, which='major', axis='y')

                # draw vertical lines to separate bar groups
                vlines_mi = np.array(mi)[np.arange(1,len(mi))]
                ax.vlines(IND[gi,vlines_mi]-BAR_MARGIN, 0, ax.get_ylim()[1], colors='k', linestyles='dotted')

            # only label x-axis of last (bottom-most) axis
            for ax in axes[:-1]:
                ax.tick_params(labelbottom='off')

            # ha controls where labels are aligned to (left, center, or right)
            plt.xticks(IND[gi,mi]+width*len(si)/2, GRAPH_LABELS[gi,mi], rotation=35, ha='right')

                
            #ml = MultipleLocator(5)
            #plt.axes().yaxis.set_minor_locator(ml)

            plt.tight_layout()
            plt.subplots_adjust(hspace = 0.001)

            save_name = alg + '_' + graph + '_' + save_suffix
            if do_master:
                save_name = save_name + '_master'

            if save_eps:
                plt.savefig('./figs/' + save_name + '.eps', format='eps',
                            bbox_inches='tight', pad_inches=0.05)

            # TODO: save_png causes error on exit (purely cosmetic: trying to close a non-existent canvas)
            if save_png:
                plt.savefig('./figs/' + save_name + '.png', format='png',
                            dpi=200, bbox_inches='tight', pad_inches=0.05)


## Separate plot with the legend
# values are tuned to give perfect size output for fontsize of 20
fignum += 1
plt.figure(fignum, figsize=(4,3.6), facecolor='w')
ax = plt.subplot()
width = (1.0-2.0*BAR_MARGIN)/3
plt_legend = [plt.bar(0 + width*i, avg[0], width, color=col, hatch=pat)
              for i,(avg,col,pat) in enumerate(zip(stats_dict[STATS[mode][0] + '_avg'][0,0],
                                                   COLORS,
                                                   PATTERNS))]

ax.legend(plt_legend[0:len(plt_legend)], LEGEND_LABELS, fontsize=20,
          loc=3, bbox_to_anchor=[-0.1,-0.1], borderaxespad=0.0).draw_frame(False)

for bars in plt_legend:
    for bar in bars:
        bar.set_visible(False)

plt.axis('off')
plt.tight_layout()

if save_eps:
    plt.savefig('./figs/legend.eps', format='eps', bbox_inches='tight', pad_inches=0)

if save_png:
    plt.savefig('./figs/legend.png', format='png', dpi=200, bbox_inches='tight', pad_inches=0)


# show all plots
if (not save_eps) and (not save_png):
    plt.show()
