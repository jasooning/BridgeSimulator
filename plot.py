import matplotlib.pyplot as plt
import numpy as np

def plot(data_rows, plotting_fos):
    """
    data_rows: list of CSV-style strings.
               First row contains column labels.
               First column of each row is the x-axis.
    plotting_fos: boolean flag; if True, plot FOS (log scale).
                  if False, assume only two columns and plot on left/right axes.
    """

    # --- Parse CSV rows into lists ---
    parsed = [row.strip().split(",") for row in data_rows]

    # --- Extract labels from first row ---
    labels = parsed[0]                # e.g. ["Position (mm)", "Label1", "Label2"]
    x_label = labels[0]
    y_labels = labels[1:]

    parsed = parsed[1:]  # skip header

    # --- Convert numeric rows ---
    x = []
    y_series = [[] for _ in y_labels]

    for row in parsed:
        if not row or len(row) < len(labels):
            continue  # skip malformed rows

        # first column → x axis
        x.append(float(row[0]))

        # remaining columns → y-series
        for i in range(len(y_labels)):
            y_series[i].append(float(row[i+1]))

    # --- Plotting ---
    plt.figure(figsize=(12, 7))

    if plotting_fos:
        # All series on same (log) axis
        for i, y in enumerate(y_series):
            plt.plot(x, y, label=y_labels[i])
        plt.yscale("log")
        plt.ylabel("FOS (log scale)")
        plt.axhline(y=1, color='red', linestyle='--', linewidth=1, label='FOS = 1')
    else:
        # Two-column special case: left/right axes
        if len(y_series) != 2:
            raise ValueError("For plotting_fos=False, there must be exactly 2 columns")

        fig, ax1 = plt.subplots(figsize=(12, 7))

        # Left axis
        ax1.plot(x, y_series[0], color='tab:blue', label=y_labels[0])
        ax1.set_ylabel(y_labels[0], color='tab:blue')
        ax1.tick_params(axis='y', labelcolor='tab:blue')

        # Right axis
        ax2 = ax1.twinx()
        ax2.plot(x, y_series[1], color='tab:orange', label=y_labels[1])
        ax2.set_ylabel(y_labels[1], color='tab:orange')
        ax2.tick_params(axis='y', labelcolor='tab:orange')

        # Draw horizontal line at y=1 on both axes
        ax1.axhline(y=1, color='red', linestyle='--', linewidth=1)
        ax2.axhline(y=1, color='red', linestyle='--', linewidth=1)

        plt.title("BME and SFE with Position")
        ax1.set_xlabel(x_label)
        ax1.grid(True, which="both", ls="--", alpha=0.5)

        # Legends combined
        lines_1, labels_1 = ax1.get_legend_handles_labels()
        lines_2, labels_2 = ax2.get_legend_handles_labels()
        ax1.legend(lines_1 + lines_2, labels_1 + labels_2, loc="upper right")

        plt.xticks(np.arange(0, max(x)+50, 100))
        plt.tight_layout()
        plt.show()
        return  # exit early since already plotted

    # --- Common plotting for FOS case ---
    plt.xlabel(x_label)
    plt.title("Bridge Failure Modes vs Position")
    plt.grid(True, which="both", ls="--", alpha=0.5)
    plt.legend(loc="upper right")
    plt.tight_layout()
    plt.xticks(np.arange(0, max(x)+50, 50))
    plt.show()
