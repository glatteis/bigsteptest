import pylab
import tabulate
import csv
import argparse
from datetime import datetime
import random
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from matplotlib import cm
import matplotlib.lines as mlines
import matplotlib.markers
import string
import matplotlib


parser = argparse.ArgumentParser(description='Convert a csv file generated by process_output.py to a scatter plot input csv.')
parser.add_argument('input', type=str, help='location of input csv file')
parser.add_argument('compx', type=str, help='method on x axis')
parser.add_argument('compy', type=str, help='method(s) on y axis')
parser.add_argument('labelx', type=str, help='label on x axis')
parser.add_argument('labely', type=str, help='label on y axis')
output_file_name = "scatter-plot/scatter" + str(int(datetime.now().timestamp()))
parser.add_argument('--output-csv', type=str, default=output_file_name+".csv", help='location of output csv file')
parser.add_argument('--output-pdf', type=str, default=output_file_name+".pdf", help='location of output pdf file')
parser.add_argument('--comp-field', help='fields to compare', type=str, default='Method')
parser.add_argument('--filter', help='key/values to only include e.g. a:x;b:y', type=str, default=None)
parser.add_argument('--one-vs-all', help='creates a one-vs-all plot', type=bool, default=False)
parser.add_argument('--seperate-legend', help='saves legend in different pdf', type=bool, default=False)
parser.add_argument('--symbols', help='symbols instead of letters', type=bool, default=False)

TO_VALUE = 11000
ERR_VALUE = 20000
MIN_VALUE = 0.0001
MAX_VALUE = 10000

args = parser.parse_args()

# output_table_headers = ["Type", "Benchmark", "Model", "Color", "time_" + args.compx, "time_" + args.compy]
# output_table = [output_table_headers]
matplotlib.rcParams.update({'font.size': 16})

color_map = {}
marker_map = {}
hatch_map = {}

benchmark_map = {}
model_map = {}
with open(args.input) as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        skip = False
        if args.filter != None:
            for keyvalue in args.filter.split(";"):
                key = keyvalue.split(":")[0]
                value = keyvalue.split(":")[1]
                if row[key] != value:
                    skip = True
                    break
        if skip:
            continue
        if row["Model"].startswith("network2"):
            row["Model"] = row["Model"].replace("network2", "n2").replace("priorities", "prios").replace("packets", "ps").replace("dropped", "dr")
        join_params = ["Model", "Const", "Mem", "Prop", "Method", "Add. Settings"]
        if args.comp_field in join_params:
            join_params.remove(args.comp_field)
        benchmark_id = "-".join([row[x] for x in join_params])
        if benchmark_id not in benchmark_map:
            benchmark_map[benchmark_id] = []
        benchmark_map[benchmark_id].append(row)
        model_map[row["Model"]] = 1


benchmark_map_averaged = {}
for benchmark_id in benchmark_map:
    benchmarks = benchmark_map[benchmark_id]
    keys = benchmarks[0].keys()
    benchmark_buckets = []
    for benchmark in benchmarks:
        found_bucket = False
        for benchmark_bucket in benchmark_buckets:
            benchmark2 = benchmark_bucket[0]
            belongs_into_bucket = True
            for key in keys:
                if key != "Time" and key != "Found" and benchmark2[key] != benchmark[key]:
                    belongs_into_bucket = False
                    break
            if belongs_into_bucket:
                found_bucket = True
                benchmark_bucket.append(benchmark)
        if not found_bucket:
            benchmark_buckets.append([benchmark])
    # Average buckets
    benchmark_map_averaged[benchmark_id] = []
    for benchmark_bucket in benchmark_buckets:
        times = []
        founds = []
        avg_time = None
        avg_found = None
        for benchmark in benchmark_bucket:
            times.append(benchmark["Time"])
            founds.append(benchmark["Found"])
        if "N/A" in times:
            for t in times:
                if t != "N/A":
                    print("In this benchmark, some timed out, but some didn't:", benchmark_bucket)
                avg_time = "N/A"
                avg_found = "N/A"
        elif "ERR" in times:
            for t in times:
                if t != "ERR":
                    print("In this benchmark, some errord, but some didn't:", benchmark_bucket)
                avg_time = "ERR"
                avg_found = "ERR"
        else:
            avg_time = sum([float(x) for x in times]) / len(times)
            avg_found = sum([float(x) for x in founds]) / len(founds)
        first_benchmark = benchmark_bucket[0].copy()
        first_benchmark["Time"] = avg_time
        first_benchmark["Found"] = avg_found
        benchmark_map_averaged[benchmark_id].append(first_benchmark)
benchmark_map = benchmark_map_averaged



# Make a scatter plot!
x = []
y = []
colors = []
markers = []
hatches = []

cm = plt.get_cmap('nipy_spectral')
if args.one_vs_all:
    NUM_COLORS = len(args.compy.split(","))
else:
    NUM_COLORS = len(model_map.keys()) * len(args.compy.split(","))
# color_cycle = [cm(0)] * 1000
color_cycle = [cm(1.*i/NUM_COLORS) for i in range(NUM_COLORS)]
marker_cycle = []
# if args.one_vs_all:
#     marker_cycle = ["o"] * 1000
hatch_cycle = [None] * len(color_cycle)
if args.symbols:
    cmap = plt.get_cmap('tab10').colors
    # hack: this works for the constraint method plot, and only the constraint method plot
    # marker_cycle = ["o", "o", "^", "^", "^", "s", "s", "s"]
    # logarithmic barrier: s
    # project: ^
    # logistic sigmod: o
    marker_cycle = ["s", "o"] + ["s", "^", "o"] * 2
    color_cycle = [cmap[0], cmap[2]] + [cmap[0], cmap[1], cmap[2]] * 2
    # color_cycle = [cmap[0]] * 2 + [cmap[1]] * 3 + [cmap[2]] * 3
    hatch_dashed = "/" * 10
    hatch_dotted = "." * 8
    hatch_cycle = [None] * 2 + [hatch_dotted] * 3 + [hatch_dashed] * 3
else:
    for letter in (list(string.ascii_lowercase) + list(string.ascii_uppercase)) * 10:
        marker_cycle.append("$" + letter + "$")
# "o",
# "v" ,
# "^" ,
# "<",
# ">",
# "s",
# "p",
# "P",
# "*",
# "h",
# "+",
# "x",
# "X",
# "D" ,
# "d"] * 10
i = 0

def marker_discriminator(compy_benchmark):
    if args.one_vs_all:
        return compy_benchmark[args.comp_field]
    return compy_benchmark["Model"]

for benchmark_id in benchmark_map:
    benchmarks = benchmark_map[benchmark_id]
    compx_benchmark = None
    compy_benchmarks = []
    model = None
    for benchmark in benchmarks:
        if benchmark[args.comp_field] == args.compx:
            compx_benchmark = benchmark
        if benchmark[args.comp_field] in args.compy.split(","):
            compy_benchmarks.append(benchmark)
        model = benchmark["Model"]
    if compx_benchmark == None or compy_benchmarks == [] or model == None:
        print("Warning: Not both methods exist in benchmark " + benchmark_id)
        continue
    for compy_benchmark in compy_benchmarks:
        if marker_discriminator(compy_benchmark) not in color_map:
            color_map[marker_discriminator(compy_benchmark)] = color_cycle[i]
            marker_map[marker_discriminator(compy_benchmark)] = marker_cycle[i]
            hatch_map[marker_discriminator(compy_benchmark)] = hatch_cycle[i]
            i += 1
    # output_table.append(["pdtmc", benchmark_id, model, color_map[model], compx_benchmark["Time"], compy_benchmark["Time"]])

    def time_to_int(time):
        if time == "N/A":
            return TO_VALUE
        if time == "ERR":
            return ERR_VALUE
        return float(time)

    for compy_benchmark in compy_benchmarks:
        x.append(time_to_int(compx_benchmark["Time"]))
        y.append(time_to_int(compy_benchmark["Time"]))
        colors.append(color_map[marker_discriminator(compy_benchmark)])
        markers.append(marker_map[marker_discriminator(compy_benchmark)])
        hatches.append(hatch_map[marker_discriminator(compy_benchmark)])

# with open(args.output_csv, 'w') as csvfile:
#     writer = csv.writer(csvfile)
#     writer.writerows(output_table)

fig = plt.figure(figsize=(7, 7))
ax = plt.gca()
ax.set_aspect("equal")
custom_legend_plots = []
custom_legend_labels = []
for model in color_map:
    marker = plt.scatter([0], [0], s=[160], marker=marker_map[model], color=color_map[model], hatch=hatch_map[model])
    custom_legend_plots.append(marker)
    custom_legend_labels.append(model)

line = mlines.Line2D([MIN_VALUE, MAX_VALUE], [MIN_VALUE, MAX_VALUE], color='black', ls="-")
ax.add_line(line)
line2 = mlines.Line2D([MIN_VALUE, MAX_VALUE/10], [MIN_VALUE*10, MAX_VALUE], color='black', ls="--")
ax.add_line(line2)
line3 = mlines.Line2D([MIN_VALUE, MAX_VALUE/100], [MIN_VALUE*100, MAX_VALUE], color='black', ls="--")
ax.add_line(line3)

to_line1 = mlines.Line2D([0, TO_VALUE], [TO_VALUE, TO_VALUE], color='gray', ls="-")
ax.add_line(to_line1)
to_line2 = mlines.Line2D([TO_VALUE, TO_VALUE], [TO_VALUE, 0], color='gray', ls="-")
ax.add_line(to_line2)

err_line1 = mlines.Line2D([0, ERR_VALUE], [ERR_VALUE, ERR_VALUE], color='gray', ls="-")
ax.add_line(err_line1)
err_line2 = mlines.Line2D([ERR_VALUE, ERR_VALUE], [ERR_VALUE, 0], color='gray', ls="-")
ax.add_line(err_line2)

plt.draw()

for i in range(len(x)):
    ax.scatter([x[i]], [y[i]], c=[colors[i]], marker=markers[i], s=[160], zorder=1000, alpha=0.65, hatch=hatches[i])
    # if args.one_vs_all:
    # else:
    #     ax.scatter([x[i]], [y[i]], c=[colors[i]], marker=markers[i], s=[160], zorder=1000, alpha=1)
ax.set_yscale('log')
ax.set_xscale('log')
ax.set_xlim([MIN_VALUE - MIN_VALUE*0.1,ERR_VALUE + ERR_VALUE * 0.25])
ax.set_ylim([MIN_VALUE - MIN_VALUE*0.1,ERR_VALUE + ERR_VALUE * 0.25])

if args.symbols:
    empty_marker = plt.scatter([0], [0], s=[0], marker=None)
    for i in range(len(custom_legend_plots)):
        custom_legend_labels[i] = " ".join(custom_legend_labels[i].split(" ")[1:])
    custom_legend_plots.insert(0, empty_marker)
    custom_legend_plots.insert(3, empty_marker)
    custom_legend_plots.insert(7, empty_marker)
    custom_legend_labels.insert(0, "η=0.1")
    custom_legend_labels.insert(3, "η=0.01")
    custom_legend_labels.insert(7, "η=0.001")


if not args.seperate_legend:
    leg = ax.legend(custom_legend_plots, custom_legend_labels, loc="lower right")


ax.spines['right'].set_visible(False)
ax.spines['top'].set_visible(False)

locs, labels = plt.xticks()
locs = [0.001, 0.01, 0.1, 1, 10, 100, 1000, TO_VALUE, ERR_VALUE]
labels = ["0.001", "0.01", "0.1", "1", "10", "100", "1000", "TO/MO", "ERR"]
plt.xticks(locs, labels, rotation=45, ha="right")
plt.yticks(locs, labels)
ax.set_xlabel(args.labelx, labelpad=0)
ax.set_ylabel(args.labely, labelpad=0)

plt.tight_layout()
plt.savefig(args.output_pdf)

if args.seperate_legend:
    figlegend = pylab.figure(figsize=(5,5))
    leg = figlegend.legend(custom_legend_plots, custom_legend_labels)
    if args.symbols:
        for vpack in leg._legend_handle_box.get_children()[:1]:
            for i in [0, 3, 7]:
                hpack = vpack.get_children()[i]
                hpack.get_children()[0].set_width(0)
    figlegend.tight_layout()
    figlegend.savefig(args.output_pdf.replace(".pdf", "-legend.pdf"))
