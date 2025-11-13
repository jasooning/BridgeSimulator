import ast
#shapes defined by a list of vertices

def load_file(filename):
    """
    Reads a text file containing lists of tuples on each line,
    and returns a list of lists of tuples.
    
    Example line in file: [(0, 4), (4, 4), (4, 3.5), (0, 3.5)]
    """
    all_polygons = []

    with open(filename, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue  # skip empty lines
            polygon = ast.literal_eval(line)  # safely convert string to list of tuples
            all_polygons.append(polygon)
    
    return all_polygons

#converts 4 tuples to a list of 4 numbers [x, y, w, h]   
def convert_to_rect(verts):

    xs = [a[0] for a in verts]
    ys = [a[1] for a in verts]

    print(xs)
    print(ys)

    x = (max(xs) + min(xs)) / 2
    y = (max(ys) + min(ys)) / 2

    w = max(xs) - min(xs)
    h = max(ys) - min(ys)

    return [x, y, w, h]



def ybar(rects):

    ybar = 0
    area = 0

    for i in rects:
        area += i[2] * i[3]
        ybar += i[1] * i[2] * i[3]

    return ybar / area

def I(rects):
    YBAR = ybar(rects)

    Iout = 0

    for i in rects:
        Iout += i[2] * (i[3] ** 3) / 12
        Iout += i[2] * i[3] * (i[1] - YBAR) ** 2

    return Iout


#ybar relative to very bottom of cross-section
#to find ybar relative
def ybar_bot(rects):
    YBAR = ybar(rects)

    return YBAR - min([a[1] - a[3] / 2 for a in rects])

def ybar_top(rects):
    yb = ybar_bot(rects)
    h = max([a[1] + a[3] / 2 for a in rects]) - min([a[1] - a[3] / 2 for a in rects])
    return h - yb

def get_rects():
    file = load_file("/Users/gregoryparamonau/Desktop/BRIDGE/BridgeSimulator/test_shape.txt")

    rects = []

    for i in file:
        rects.append(convert_to_rect(i))
    
    return rects

if __name__ == "__main__":

    rects = get_rects()

    print (ybar_bot(rects), I(rects))