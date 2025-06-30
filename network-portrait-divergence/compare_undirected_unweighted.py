#!/usr/bin/env python
# -*- coding: utf-8 -*-

# graphml_portrait_matrix_debug.py
# Debugged version to trace why output is empty

import os
import sys
import itertools
import networkx as nx
import pandas as pd
from portrait_divergence import portrait_divergence

# === Config ===
folder_path = r'D:\_workspace\_vscode\Hiwi\network-portrait-divergence\data\split_network_graphml_Wertungen_17Jun2025'

# === Check folder path ===
if not os.path.isdir(folder_path):
    print(f"? Folder path '{folder_path}' does not exist or is not a directory.")
    sys.exit(1)

# === Prepare output path ===    
folder_name = os.path.basename(os.path.normpath(folder_path))
output_excel = os.path.join('.', 'data', f'portrait_divergence_matrix_{folder_name}.xlsx')
output_plot = os.path.join('.', 'data', f'portrait_divergence_histogram_{folder_name}.png')

# === Load .graphml files ===
graphml_files = sorted([f for f in os.listdir(folder_path) if f.endswith('.graphml')])
print(f"Found {len(graphml_files)} .graphml files.")

if not graphml_files:
    sys.exit("? No .graphml files found. Check your folder path.")

graphml_paths = {f: os.path.join(folder_path, f) for f in graphml_files}

# === Load graphs into memory ===
graphs = {}
for fname, fpath in graphml_paths.items():
    try:
        G = nx.read_graphml(fpath)
        G = nx.convert_node_labels_to_integers(G)
        if len(G) == 0:
            print(f"[WARNING] Graph {fname} is empty.")
        graphs[fname] = G
    except Exception as e:
        print(f"? Failed to load {fname}: {e}")

if not graphs:
    sys.exit("? No graphs successfully loaded.")

# === Compute portrait divergences for all pairs ===
matrix = pd.DataFrame(index=graphml_files, columns=graphml_files, dtype=object)

for file1, file2 in itertools.product(graphml_files, repeat=2):
    try:
        G1 = graphs.get(file1)
        G2 = graphs.get(file2)
        if G1 is None or G2 is None:
            matrix.loc[file1, file2] = "LoadError"
            continue

        Djs = portrait_divergence(G1, G2)
        matrix.loc[file1, file2] = Djs

        print(f"Divergence({file1}, {file2}) = {Djs}")
    except Exception as e:
        print(f"? Error comparing {file1} and {file2}: {e}")
        matrix.loc[file1, file2] = "Error"

# === Save to Excel ===
matrix.to_excel(output_excel)
print(f"Full comparison matrix saved to '{output_excel}'")

# === Optional Plotting ===
try:
    import matplotlib.pyplot as plt
    values = matrix.values.flatten()
    values = [v for v in values if isinstance(v, (int, float))]
    if values:
        plt.hist(values, bins='auto', density=True, histtype='stepfilled', alpha=0.7)
        plt.xlabel("Portrait divergence $D_\mathrm{JS}$")
        plt.ylabel("Probability Density")
        plt.title("Histogram of All Graph Pair Divergences")
        plt.tight_layout()
        plt.savefig(output_plot)
        plt.show()
    else:
        print("?? No valid numeric values to plot.")
except ImportError:
    print("?? matplotlib not installed. Skipping plot.")
