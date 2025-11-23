import matplotlib.pyplot as plt
import numpy as np

def plot(data_rows, plotting_fos, title):
    #parse string into list of strings
    parsed = [row.strip().split(",") for row in data_rows]

    # first string in list data_rows contains labels, so extracts those
    labels = parsed[0]
    x_label = labels[0]
    y_labels = labels[1:]

    parsed = parsed[1:] # skips label row

    #converts all strings to numbers and values
    #to be plotted
    x = []
    y_series = [[] for _ in y_labels]

    for row in parsed:
        #skip rows with missing values (sometimes happens)
        if not row or len(row) < len(labels):
            continue

        #very first column is x-axis --> mm
        x.append(float(row[0]))

       #the rest become data to be plotted
        for i in range(len(y_labels)):
            y_series[i].append(float(row[i+1]))

    #creates figure
    plt.figure(figsize=(12, 7))

    #since two separate graphs are being made, Envelopes and factors of safety
    #we need to differentiate

    #when plotting Factor of safety, plot on log scale to be discerned easier
    #also limit y-height to 100 since factors of safety above that are irrelevant
    if plotting_fos:
        for i, y in enumerate(y_series):
            plt.plot(x, y, label=y_labels[i])
        plt.yscale("log")
        plt.ylim((0.9, 10**2))
        plt.ylabel("FOS (log scale)")
        plt.axhline(y=1, color='red', linestyle='--', linewidth=1, label='FOS = 1')

        #highlight regions by what mode of failure is governing
        y_array = np.array(y_series)
        min_series_idx = np.argmin(y_array, axis=0)

        for xi, idx in zip(x, min_series_idx):
            #creates highlight of graph
            plt.fill_betweenx(plt.ylim(), xi-0.5, xi+0.5, color=plt.gca().lines[idx].get_color(), alpha=0.1)
    
    #now if plotting envelopes, different logic
    #use two separate y-axes
    #SFEs use left axis
    #BMEs use right axis (also inverted so positive is down)
    else:
        fig, ax1 = plt.subplots(figsize=(12, 7))

        # Left axis
        ax1.plot(x, y_series[0], color='tab:purple', label=y_labels[0])
        ax1.plot(x, y_series[1], color='tab:green', label = y_labels[1])
        ax1.plot(x, y_series[2], color='tab:blue', label = y_labels[2])
        ax1.set_ylabel(y_labels[2], color='tab:blue')
        ax1.tick_params(axis='y', labelcolor='tab:blue')

        # Right axis
        ax2 = ax1.twinx()
        ax2.invert_yaxis()
        ax2.plot(x, y_series[3], color='tab:olive', label=y_labels[3])
        ax2.plot(x, y_series[4], color='tab:red', label=y_labels[4])
        ax2.plot(x, y_series[5], color='tab:orange', label=y_labels[5])
        ax2.set_ylabel(y_labels[5], color='tab:orange')
        ax2.tick_params(axis='y', labelcolor='tab:orange')

        # Draw horizontal line at y=1 on both axes
        ax1.axhline(y=1, color='red', linestyle='--', linewidth=1)
        ax2.axhline(y=1, color='red', linestyle='--', linewidth=1)

        plt.title("Load Case 1 SFE and BME")
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

    plt.xlabel(x_label)
    plt.title(title)
    plt.grid(True, which="both", ls="--", alpha=0.5)
    plt.legend(loc="upper right")
    plt.tight_layout()
    plt.xticks(np.arange(0, max(x)+50, 50))
    plt.show()
