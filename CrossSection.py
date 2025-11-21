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
    if not intersects(a, b):
        return [0, 0, 0, 0]

    # edges of a
    x1, x2 = a[0] - a[2]/2, a[0] + a[2]/2
    y1, y2 = a[1] - a[3]/2, a[1] + a[3]/2

    # edges of b
    x3, x4 = b[0] - b[2]/2, b[0] + b[2]/2
    y3, y4 = b[1] - b[3]/2, b[1] + b[3]/2

    # intersection edges
    ix1 = max(x1, x3)
    ix2 = min(x2, x4)
    iy1 = max(y1, y3)
    iy2 = min(y2, y4)

    # width and height
    w = ix2 - ix1
    h = iy2 - iy1

    # center of intersection
    cx = (ix1 + ix2) / 2
    cy = (iy1 + iy2) / 2

    return [cx, cy, w, h]



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
        h = min(ay2, iy2) - max(ay1, iy1)
        if h > 0:
            pieces.append([(ix2 + ax2)/2, cy, w, h])

    return pieces

def intersects(a, b): 
    return abs(a[0]-b[0]) < (a[2]+b[2])/2 and abs(a[1]-b[1]) < (a[3]+b[3])/2

def int_list(a, b_list):
    for i in b_list:
        if intersects(a, i): return True
    return False

def make_taller(b_list):
    out = []
    for i in b_list: out.append([i[0], i[1], i[2], i[3] + 500])

    return out

def make_wider(b_list):
    out = []
    for i in b_list: out.append([i[0], i[1], i[2] + 500, i[3]])
    return out



# cleave rectangle a by an array of rectangles b
def cleave(a, b_list):
    pieces = [a]
    count = 0
    reset = False
    while (count < len(pieces)):
        reset = False
        for cutter in b_list:
            if (not intersects(pieces[count], cutter)): continue
            else:
                cut = inv_intersect(pieces[count], cutter)

                if cut == [pieces[count]]: 
                    reset = False
                else:
                    pieces[count : count + 1] = cut

                    reset = True
                    break
        if reset : count = 0
        else : count += 1

    return pieces

#gives Q (first moment of area) of the cross section (rects) at the centroidal axis (ybar) measured from bottom
def Q(rects, height, ybar):

    block = [0, height - 1000, 1000, 1000 * 2]
    if (height > ybar): block = [0, height + 1000, 1000, 1000 * 2]

    rects_below = []
    for i in rects:
        print(i)
        rects_below.append(intersect(i, block))

    print ("rects below", rects_below)
    
    out = 0
    for i in rects_below:
        if i == None: continue
        out += i[2] * i[3] * abs(i[1] - ybar)

    return out

#return width at centroid
def width_at_location(rects, ybar):
    out = 0
    for i in rects:
        if i[1] - i[3] / 2 < ybar <= i[1] + i[3] / 2:
            out += i[2]

    return out

def cross_section_at_pos(pos):
    # support, edge, middle
    spac = [125, 500, 800, 1125]
    if (spac[1] <= pos <= spac[2]):
        return "middle"
    if spac[0] <= pos < spac[1] or spac[2] < pos <= spac[3]:
        return "edge"
    return "support"




#ybar relative to very bottom of cross-section
#to find ybar relative
def ybar_bot(rects):
    YBAR = ybar(rects)

    return YBAR - min([a[1] - a[3] / 2 for a in rects])

def ybar_top(rects):
    YBAR = ybar(rects)
    return max([a[1] + a[3] / 2 for a in rects]) - YBAR

def get_rects(file_name):
    file = load_file(file_name)

    rects = []

    for i in file:
        rects.append(convert_to_rect(i))
    
    return rects

if __name__ == "__main__":

    rects = get_rects("./section_v4_supports.txt")
    ybarr = ybar(rects)

    print (ybarr, I(rects), Q(rects, 100, ybarr), width_at_location(rects, 100))