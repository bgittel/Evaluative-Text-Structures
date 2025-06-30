

#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Compare directed graph weights using portrait divergence
import os
import subprocess
import pandas as pd
from itertools import product
from concurrent.futures import ThreadPoolExecutor, as_completed
import matplotlib.pyplot as plt

# === Config ===
# Define the folders containing .graphml files
# In case we use positive and negative evaluations in one file.
folder_paths = [r'D:\_workspace\_vscode\Hiwi\network-portrait-divergence\data\split_network_graphml_Relationen_17Jun2025',
                r'D:\_workspace\_vscode\Hiwi\network-portrait-divergence\data\split_network_graphml_Wertungen_17Jun2025']

# In case we use positive and abs negative evaluations seperately.
folder_paths = [r"D:\_workspace\_vscode\Hiwi\network-portrait-divergence\data\seperate_evaluations\split_network_graphml_Wertungen_abs_negative_18Jun2025",
                r"D:\_workspace\_vscode\Hiwi\network-portrait-divergence\data\seperate_evaluations\split_network_graphml_Wertungen_positive_18Jun2025",
                r"D:\_workspace\_vscode\Hiwi\network-portrait-divergence\data\seperate_evaluations\split_network_graphml_Relationen_18Jun2025"]

# Ensure matplotlib uses a non-interactive backend
for folder_path in folder_paths:
    if not os.path.isdir(folder_path):
        print(f"?? Skipping '{folder_path}': Not a valid directory.")
        continue
    print(f"?? Processing folder: {folder_path}")
    
    # === Setup ===
    portrait_script = 'portrait_divergence.py'
    max_workers = 8

    # Dynamically generate output filename
    folder_name = os.path.basename(os.path.normpath(folder_path))
    output_dir = os.path.join('.', 'data')
    os.makedirs(output_dir, exist_ok=True)

    output_excel = os.path.join(output_dir, f'portrait_divergence_matrix_{folder_name}.xlsx')
    output_plot = os.path.join(output_dir, f'portrait_divergence_histogram_{folder_name}.png')

    # === Get .graphml files ===
    graphml_files = sorted([f for f in os.listdir(folder_path) if f.endswith('.graphml')])
    graphml_paths = {f: os.path.join(folder_path, f) for f in graphml_files}
    file_pairs = list(product(graphml_files, repeat=2))  # all pairs (including self)

    # === Function to run comparison ===
    def compare_graphmls(pair):
        file1, file2 = pair
        try:
            result = subprocess.run(
                [
                    'python', portrait_script,
                    '-d',
                    '-w', 'WEIGHTS',
                    '--graphml',
                    graphml_paths[file1],
                    graphml_paths[file2]
                ],
                capture_output=True, text=True, check=True
            )
            value = float(result.stdout.strip())
            return file1, file2, value
        except subprocess.CalledProcessError as e:
            print(f"[ERROR] Comparing {file1} vs {file2}: {e.stderr.strip()}")
            return file1, file2, None
        except ValueError:
            print(f"[PARSE ERROR] Could not parse output for {file1} vs {file2}: {result.stdout.strip()}")
            return file1, file2, None

    # === Parallel execution ===
    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(compare_graphmls, pair) for pair in file_pairs]
        for future in as_completed(futures):
            results.append(future.result())

    # === Build matrix ===
    matrix = pd.DataFrame(index=graphml_files, columns=graphml_files, dtype=object)
    for file1, file2, value in results:
        matrix.loc[file1, file2] = value

    # === Save to Excel ===
    matrix.to_excel(output_excel)
    print(f"? Full comparison matrix saved to '{output_excel}'")

    # === Plot histogram ===
    values = pd.to_numeric(matrix.values.flatten(), errors='coerce')
    values = [v for v in values if pd.notna(v)]

    if values:
        plt.hist(values, bins='auto', density=True, histtype='stepfilled', alpha=0.7)
        plt.xlabel(r"Portrait divergence $D_\mathrm{JS}$")
        plt.ylabel("Probability Density")
        plt.title("Histogram of All Graph Pair Divergences")
        plt.tight_layout()
        plt.savefig(output_plot)  # Save
        plt.close()
        print(f"?? Histogram saved to '{output_plot}'")
    else:
        print("?? No valid values to plot.")