import tabulate
import csv
import argparse
from datetime import datetime
import random
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib import cm
import matplotlib.lines as mlines
import string
import matplotlib

parser = argparse.ArgumentParser(
    description="Convert a csv file generated by process_output.py to a scatter plot input csv."
)
parser.add_argument("input", type=str, help="location of input csv file")
parser.add_argument(
    "--methods", type=str, help="methods to compare (seperated by commas)"
)

args = parser.parse_args()

methods = args.methods.split(",")
output_table_headers = ["Model", "Const", "Prop", "|S| (pMC)", "|V| (pMC)"]
for method in methods:
    output_table_headers.append(method[0].upper() + "Time")
    output_table_headers.append(method[0].upper() + "Found")

output_table = []

benchmark_map = {}
model_map = {}
with open(args.input) as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        # if row["Model"].startswith("network2"):
        #     row["Model"] = "network2"
        benchmark_id = "-".join([row["Model"], row["Const"], row["Mem"], row["Prop"]])
        if benchmark_id not in benchmark_map:
            benchmark_map[benchmark_id] = []
        benchmark_map[benchmark_id].append(row)
        model_map[row["Model"]] = 1

for key in benchmark_map:
    benchmarks = benchmark_map[key]
    for benchmark in benchmarks:
        if benchmark["#States (min)"] != "?":
            first_benchmark = benchmark
            break
    propsplit = first_benchmark["Prop"].split("_")
    prop = ""
    if propsplit[1] == "probability":
        prop += "P"
    elif propsplit[1] == "reward":
        prop += "R"
    if propsplit[3] == "max":
        prop += ">="
    elif propsplit[3] == "min":
        prop += "<="
    prop += propsplit[0]

    print(first_benchmark)

    line = [
        first_benchmark["Model"],
        first_benchmark["Const"] + " m=" + first_benchmark["Mem"],
        prop,
        first_benchmark["#States (min)"],
        first_benchmark["#Params (min)"],
    ]
    for benchmark in benchmarks:
        for method in methods:
            if method == benchmark["Method"]:
                if benchmark["Time"] == "N/A":
                    line.append("TO")
                elif benchmark["Time"] == "ERR":
                    line.append("ERR")
                else:
                    line.append(int(float(benchmark["Time"])))
                if benchmark["Found"] in ["ERR", "N/A"]:
                    line.append(benchmark["Found"])
                else:
                    line.append(float(benchmark["Found"]))
                break
    output_table.append(line)


print(tabulate.tabulate(output_table, headers=output_table_headers, tablefmt="latex"))
