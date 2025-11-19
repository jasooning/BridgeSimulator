import matplotlib.pyplot as plt
import numpy as np

def plot(data_rows):
    """
    data_rows: list of CSV-style strings.
               First row contains column labels.
               First column of each row is the x-axis.
    """

    # --- Parse CSV rows into lists ---
    parsed = [row.strip().split(",") for row in data_rows]

    # --- Extract labels from first row ---
    labels = parsed[0]                # e.g. ["Position (mm)", "Label1", "Label2"]
    x_label = labels[0]
    y_labels = labels[1:]

    parsed = parsed[50 : 1200]

    # --- Convert numeric rows ---
    x = []
    y_series = [[] for _ in y_labels]

    for row in parsed[1:]:
        if not row or len(row) < len(labels):
            continue  # skip malformed rows

        # first column → x axis
        x.append(float(row[0]))

        # remaining columns → y-series
        for i in range(len(y_labels)):
            y_series[i].append(float(row[i+1]))

    # --- Plotting ---
    plt.figure(figsize=(12, 7))

    for i, y in enumerate(y_series):
        plt.plot(x, y, label=y_labels[i])

    # Draw horizontal line at y=1
    plt.axhline(y=1, color='red', linestyle='--', linewidth=1, label='FOS = 1')

    plt.yscale("log")
    plt.xlabel(x_label)
    plt.ylabel("FOS (log scale)")
    plt.title("Bridge Failure Modes vs Position")
    plt.grid(True, which="both", ls="--", alpha=0.5)
    plt.legend(loc = "upper right")
    plt.tight_layout()
    plt.xticks(np.arange(0, max(x)+50, 50))  # ticks every 50 units
    plt.show()


if __name__ == "__main__":
    test = [
        "Position (mm),Comp,Tens,Shear",
        "0,2.3,4.1,1.2",
        "1,2.2,3.8,1.3",
        "2,2.0,3.6,1.4"
    ]
    plot(test)
