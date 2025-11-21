import json
import tkinter as tk
from tkinter import filedialog

path = "section_v4_midmid.json"
try:
    with open(path, 'r') as file:
        data = json.load(file)
    shapes = []
    pos = [0, 0]
    for i in range(len(data)):
        rect = [(0, 0), (0, 0), (0, 0), (0, 0)]
        pos[0] = round(data[i]['pos'][0], 2)
        pos[1] = round(data[i]['pos'][1], 2)
        width = round(pos[0] + data[i]['w'], 2)
        height = round(pos[1] + data[i]['h'], 2)
        rect[0] = (pos[0], pos[1])
        rect[1] = (width, pos[1])
        rect[2] = (width, height)
        rect[3] = (pos[0], height)
        shapes.append(rect)
        
    for i in range(len(data)):
        print(shapes[i])

    root = tk.Tk()
    root.withdraw()

    file_path = filedialog.asksaveasfilename(
        title="Save numbers as",
        defaultextension=".txt",
        filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
    )

    if file_path:
        with open(file_path, 'a') as f:
            for i in range(len(shapes)):
                f.write(f"{shapes[i]}\n")
                print(shapes[i])

        print(f"Numbers saved to {file_path}")
    else:
        print("Save cancelled.")

except FileNotFoundError:
    print("Error: The file 'test2.json' was not found.")
except json.JSONDecodeError:
    print("Error: Failed to decode JSON from the file.")