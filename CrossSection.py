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

#return rectangle intersection of rectangles a and b
def intersect(a, b):
    return [ (max(a[0]-a[2]/2, b[0]-b[2]/2) + min(a[0]+a[2]/2, b[0]+b[2]/2)) / 2,
             (max(a[1]-a[3]/2, b[1]-b[3]/2) + min(a[1]+a[3]/2, b[1]+b[3]/2)) / 2,
             max(0, min(a[0]+a[2]/2, b[0]+b[2]/2) - max(a[0]-a[2]/2, b[0]-b[2]/2)),
             max(0, min(a[1]+a[3]/2, b[1]+b[3]/2) - max(a[1]-a[3]/2, b[1]-b[3]/2)) ]


# return a list of rectangles representing (a minus b)
def inv_intersect(a, b):
    inter = intersect(a, b)
    if inter is None:
        return [a]   # no cut

    ax1, ax2 = a[0] - a[2]/2, a[0] + a[2]/2
    ay1, ay2 = a[1] - a[3]/2, a[1] + a[3]/2

    ix1, ix2 = inter[0] - inter[2]/2, inter[0] + inter[2]/2
    iy1, iy2 = inter[1] - inter[3]/2, inter[1] + inter[3]/2

    pieces = []

    # Top piece
    if iy2 < ay2:
        h = ay2 - iy2
        pieces.append([a[0], (iy2 + ay2)/2, a[2], h])

    # Bottom piece
    if iy1 > ay1:
        h = iy1 - ay1
        pieces.append([a[0], (ay1 + iy1)/2, a[2], h])

    # Left piece
    if ix1 > ax1:
        w = ix1 - ax1
        cy = (max(ay1, iy1) + min(ay2, iy2)) / 2
        h = min(ay2, iy2) - max(ay1, iy1)
        if h > 0:
            pieces.append([(ax1 + ix1)/2, cy, w, h])

    # Right piece
    if ix2 < ax2:
        w = ax2 - ix2
        cy = (max(ay1, iy1) + min(ay2, iy2)) / 2
        h = min(ay2, iy2) - max(ay1, ay1)
        h = min(ay2, iy2) - max(ay1, iy1)
        if h > 0:
            pieces.append([(ix2 + ax2)/2, cy, w, h])

    return pieces


# cleave rectangle a by an array of rectangles b
def cleave(a, b_list):
    pieces = [a]
    for cutter in b_list:
        new_pieces = []
        for p in pieces:
            new_pieces.extend(inv_intersect(p, cutter))
        pieces = new_pieces
    return pieces

#gives Q (first moment of area) of the cross section (rects) at the centroidal axis (ybar) measured from bottom
def Q(rects, ybar):
    #first find rects below ybar
    below = [0, ybar - 1000, 1000, 1000 * 2]

    rects_below = []
    for i in rects:
        rects_below.append(intersect(i, below))

    print ("rects below", rects_below)
    
    out = 0
    for i in rects_below:
        if i == None: continue
        out += i[2] * i[3] * abs(i[1] - ybar)

    return out

#return width at centroid
def width_at_centroid(rects, ybar):
    centroid = [0, ybar, 1000, 0]

    out = 0
    for i in rects:
        if i == None: continue
        out += intersect(centroid, i)[2]
    
    return out




#ybar relative to very bottom of cross-section
#to find ybar relative
def ybar_bot(rects):
    YBAR = ybar(rects)

    return YBAR - min([a[1] - a[3] / 2 for a in rects])

def ybar_top(rects):
    YBAR = ybar(rects)
    return max([a[1] + a[3] / 2 for a in rects]) - YBAR

def get_rects():
    file = load_file("/Users/gregoryparamonau/Desktop/BRIDGE/BridgeSimulator/test_shape.txt")

    rects = []

    for i in file:
        rects.append(convert_to_rect(i))
    
    return rects

if __name__ == "__main__":

    rects = get_rects()

    print (ybar_bot(rects), I(rects))