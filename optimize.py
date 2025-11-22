import BMD
import CrossSection
import copy
import numpy
import plot

#test 8 ways the bridge can fail

#1-2 --> Compression and Tension
#tension tested at bottom only (bc tension at top is negligeable)
#compression tested only at top (bc compression at bottom is negligeable)


#5-6 --> Shear Stresses
#material shear stress tau = VQ / Ib
#glue tab shear stress calculated manually, since writing a program is difficult

#7-10 --> Plate Buckling
#Case 1 --> secured on two side and compressive stress applied normal to cross-section
#Case 2 --> secured on one side and compressive stress applied normal to cross-section
#Case 3 --> secured on both sides compressive stress applied normal to cross-section, stress ditributed linearly
#Case 4 --> shear buckling (all vertical members subject to this)

#diaphragm spacing, 0 and 1250 are necessary for code to run, but aren't actually placed in the bridge
#distributed densely closer to supports, and more rarely towards the middle
#total of 6 diaphragms
diaphragm_spacing = [0, 20, 30, 475, 750, 1220, 1230, 1250]#, 20, 30, 425, 825, 1220, 1230, 

#constants (MPa)
tau_max = 4
tau_glue = 2
sigma_C = 6
sigma_T = 30

E = 4000
mu = 0.2

#function returns flexural stress FOS for given moment and cross-section
#called along the length of the bridge with changing cross-section
#returns both compressive and tensile FOS
def flex_stress(M, I, y_top, y_bot):
    global sigma_C, sigma_T

    #compute FOS = allowed / current
    fos_c = sigma_C / (M * y_top / I)
    fos_t = sigma_T / (M * y_bot / I)

    #return dictionary with FOS type and value
    return {
        "Compression" : abs(fos_c),
        "Tension" : abs(fos_t),
    }

#function calculates Material Shear Stress FOS
#using given cross section and Shear Force returns Material Shear Stree FOS
def shear_stress(V, Q, I, b):

    global tau_max, tau_glue

    tau_m = abs(V * Q / I / b)
    return {
        "Material Shear Stress" : 1e3 if tau_m == 0 else tau_max / tau_m
    }


#function calculates all plate buckling FOS + returns as dictionary
def plate_buckling(rects, ybar, M, V, I, Q, pos):
    global E, mu, sigma_C, diaphragm_spacing

    #begins by splitting cross-section (defined as an array of rectangles [x, y, w, h]) into vertical and horizontal rectangles
    #Case 1-2: Horizontal
    #Case 3-4: Vertical

    h_rects = []
    v_rects = []

    for i in rects:
        if (i[2] > i[3]): h_rects.append(i)
        else: v_rects.append(i)

    h_split = []

    #extends vertical rectangles to make them 'cut planes' by which to split horizontal rectangles
    #create an array of 'taller' vertical rectangles, which are used to 'cleave' the horizontal rects s.t.
    #they can be classified according to the plate buckling cases
    taller = CrossSection.make_taller(v_rects)

    #loops through all horizontal rectangles, and cleaves each rectangle using 'taller' array (separates it)
    for h in h_rects:
        h_split.extend(CrossSection.cleave(h, taller))

    #dictionary containing a rectangles (converted to tuple) as key
    #and type of buckling that occurs as the value
    type_dict = {}

    #sorts horizontal rectangle 'h_split' into Case 1-2 Plate Buckling
    for h in h_split:

        #create two rects, one shifted slightly left, one shifted slightly right
        #if both of these intersect a 'cut plane', then the rectangle is case-1 plate buckling
        #if only one of these intersects, then rectangle is case-2 plate buckling

        wider_left = [h[0] - 0.6, h[1], h[2] + 1, h[3]]
        wider_right = [h[0] + 0.6, h[1], h[2] + 1, h[3]]

        int_left = CrossSection.int_list(wider_left, taller)
        int_right = CrossSection.int_list(wider_right, taller)

        #if rectangle below centroid axis its in tension, hence needs to be filtered out not to mess with results
        if (h[1] - h[3] / 2 > ybar): 
            #input rectangle as tuple as key in dictionary, with value of plate buckling case (1 or 2)
            type_dict[tuple(h)] = (1 if (int_left and int_right) else 2)

    #similar with verticals: separate verticals using horizontal rectangles as 'cut planes'
    v_split = []
    #create 'cut planes'
    wider = CrossSection.make_wider(h_rects)

    #cut verts with cut planes
    for v in v_rects:
        v_split.extend(CrossSection.cleave(v, wider))


    #removes the section of each rectangle below the centroid axis (hence in tension)
    #creating rectangle that undergoes Case-3 Plate Buckling (linear variation in applied stress)
    v_split_bottom = []
    for i in v_split:
        #copy parameters from rectangle into separate variables
        x, y, w, h = i
        #if completely below centroid, ignore
        if y + h / 2 < ybar: continue
        #if halfway across centroid, cut along and keep portion above centroid
        if y - h / 2 < ybar < y + h / 2:
            temp = y + h / 2
            h = temp - ybar
            y = temp - h / 2
        #save to array
        v_split_bottom.append([x, y, w, h])

    #create case-3 rects
    for v in v_split_bottom:
        type_dict[tuple(v)] = 3
    
    #all vertical rects are subject to case-4 shear buckling, hence those are lumped together
    for v in v_split:
        #if a rectangle is completely above the centroid, then it can undergo
        #both case-3 and case-4 buckling, hence needs to be handled separately
        #assigned value 7 because 3 + 4 = 7
        if (tuple(v) in type_dict.keys()):
            type_dict[tuple(v)] = 7
        #else just assign value 4
        else:
            type_dict[tuple(v)] = 4

    
    #now do math for every type
    #originally begin with 'infinity' FOS, and go down to minimum check
    min1 = min2 = min3 = min4 = float("inf")

    #print_dict(type_dict)

    #find all FOS
    #loop through created dictionary, and use value of dictionary to calculate according FOS
    #Case 1-3 all use My / I to find FOS
    #Case 4 uses VQ / Ib
    for i in type_dict.items():
        #case 1
        if (i[1] == 1):
            sigma_crit = 4 * numpy.pi ** 2 * E / 12 / (1 - mu ** 2) * (i[0][3] / i[0][2]) ** 2
            M_min = sigma_crit * I / (i[0][1] + i[0][3] / 2 - ybar)
            min1 = min(min1, float("inf") if M == 0 else M_min / M)
        
        #case 2
        elif (i[1] == 2):
            sigma_crit = 0.425 * numpy.pi ** 2 * E / 12 / (1 - mu ** 2) * (i[0][3] / i[0][2]) ** 2
            M_min = sigma_crit * I / (i[0][1] + i[0][3] / 2 - ybar)

            min2 = min(min2, float("inf") if M == 0 else M_min / M)
        
        #case 3 + case 7
        if (i[1] == 3 or i[1] == 7):
            sigma_crit = 6 * numpy.pi ** 2 * E / 12 / (1 - mu ** 2) * (i[0][2] / i[0][3]) ** 2
            M_min = sigma_crit * I / (i[0][1] + i[0][3] / 2 - ybar)
            min3 = min(min3, float("inf") if M == 0 else M_min / M)

        #case 4 + case 7
        if (i[1] == 4 or i[1] == 7):
            #go through all diaphragms, and find between which two the current position, 'pos' falls within
            for j in range(1, len(diaphragm_spacing)):
                #if not betwen these two, skip
                if not (diaphragm_spacing[j - 1] <= pos <= diaphragm_spacing[j]): continue

                #FOS calculated using tau = VQ / Ib

                #find a, diaphragm spacing
                a = diaphragm_spacing[j] - diaphragm_spacing[j - 1]
                #find b for VQ / Ib
                b = CrossSection.width_at_location(rects, i[1])

                tau_allowable = 5 * numpy.pi ** 2 * E / 12 / (1 - mu ** 2) * ((i[0][2] / a) ** 2 + (i[0][2] / i[0][3]) ** 2)
                tau_current = V * Q / I / b

                min4 = min(min4, float("inf") if tau_current == 0 else tau_allowable / tau_current)
                break
    #return 4 cases as a dictionary
    return {
        "CASE 1 PLATE BUCKLING" : (1e3 if min1 == float("inf") else abs(min1)), 
        "CASE 2 PLATE BUCKLING" : (1e3 if min2 == float("inf") else abs(min2)), 
        "CASE 3 PLATE BUCKLING" : (1e3 if min3 == float("inf") else abs(min3)), 
        "CASE 4 PLATE BUCKLING" : (1e3 if min4 == float("inf") else abs(min4)), 
    }

#code used to calculated FOS of all the different modes of failure
#across the length of the bridge
#also accounts for changing cross-section
#takes in SFE, BME, and the three cross-section:
#supports = cross-section at supports
#edge = cross-section between supports and middle 
#middle = cross-section at middle (~) of span
def FOS_whole_bridge(SFD_ENV, BMD_ENV, supports, edge, middle):
    #need to pre-calculate all the values for the sake of efficiency

    #supports
    ybar_s = CrossSection.ybar(supports)
    y_top_s = CrossSection.ybar_top(supports)
    y_bot_s = CrossSection.ybar_bot(supports)

    I_s = CrossSection.I(supports)
    Q_s = CrossSection.Q(supports, ybar_s, ybar_s)
    b_s = CrossSection.width_at_location(supports, ybar_s)

    #middle cross-section
    ybar_m = CrossSection.ybar(middle)
    y_top_m = CrossSection.ybar_top(middle)
    y_bot_m = CrossSection.ybar_bot(middle)

    I_m = CrossSection.I(middle)
    Q_m = CrossSection.Q(middle, ybar_m, ybar_m)
    b_m = CrossSection.width_at_location(middle, ybar_m)

    #edge (between support and middle)
    ybar_e = CrossSection.ybar(edge)
    y_top_e = CrossSection.ybar_top(edge)
    y_bot_e = CrossSection.ybar_bot(edge)

    I_e = CrossSection.I(edge)
    Q_e = CrossSection.Q(edge, ybar_e, ybar_e)
    b_e = CrossSection.width_at_location(edge, ybar_e)

    #returns both a list of strings (?) that were initially
    #printed on a text file, but later got used in plot.py to graph
    out = []

    #also prints minimum factors of safety with corresponding failure modes (minout)
    minout = {}

    #loop through length of whole bridge, and determine factors of safety for the entire length
    for i in range(1250):
        #returns 'mode' or type of cross-section used
        mode = CrossSection.cross_section_at_pos(i)

        #compute dictionary according to mode (and combine into one)
        if (mode == "support"):
            FOS = flex_stress(BMD_ENV[i], I_s, y_top_s, y_bot_s)
            FOS = FOS | shear_stress(SFD_ENV[i], Q_s, I_s, b_s)
            FOS = FOS | plate_buckling(supports, ybar_s, BMD_ENV[i], abs(SFD_ENV[i]), I_s, Q_s, i)
        elif (mode == "edge"):
            FOS = flex_stress(BMD_ENV[i], I_e, y_top_e, y_bot_e)
            FOS = FOS | shear_stress(SFD_ENV[i], Q_e, I_e, b_e)
            FOS = FOS | plate_buckling(edge, ybar_e, BMD_ENV[i], abs(SFD_ENV[i]), I_e, Q_e, i)
        elif (mode == "middle"):
            FOS = flex_stress(BMD_ENV[i], I_m, y_top_m, y_bot_m)
            FOS = FOS | shear_stress(SFD_ENV[i], Q_m, I_m, b_m)
            FOS = FOS | plate_buckling(middle, ybar_m, BMD_ENV[i], abs(SFD_ENV[i]), I_m, Q_m, i)
        
        #create minout & min it with FOS every loop
        if (i == 0): pass
        elif (i == 1): minout = copy.deepcopy(FOS)
        else:
            minout = {key: min(minout[key], FOS[key]) for key in minout}
        
        
        if (i == 0):
            out.append(to_string(FOS.keys(), -1))

        out.append(to_string(FOS.values(), i))
    
    #print factors of safety (minima)
    print_FOS(dict(sorted(minout.items(), key=lambda item: item[1], reverse=False)))

    #return array of strings
    return out


#print dictionary in readable format
def to_string(list, pos):
    out = str(pos) + ","
    if pos == -1:
        out = "Position (mm),"
    for i in list:
        out = out + str(i) + ","
    return out[:-1]

#print FOS in readable format
def print_FOS(fos_dict):

    # Determine the longest key
    max_key_len = max(len(str(k)) for k in fos_dict)
    
    for k, v in fos_dict.items():
        # Left-align key, left-align value (with 6 decimal places)
        print(f"{k.ljust(max_key_len)} : {v:<12.6f}")

#print dictionary neatly
def print_dict(dict):
    for i in dict.items():
        print (i[0], i[1])

#main
if __name__ == "__main__":
    #pre-compute SFE and BME
    BMD_ENV = BMD.BME()
    SFD_ENV = BMD.SFE()

    #get arrays of rectangles of different cross-sections
    supports = CrossSection.get_rects("./section_final_supports.txt")
    edge = CrossSection.get_rects("./section_final_middle.txt")
    middle = CrossSection.get_rects("./section_final_midmid.txt")

    #get FOS across bridge (array of strings...)
    list = FOS_whole_bridge(SFD_ENV, BMD_ENV, supports, edge, middle)

    #remove these so they don't messs w stuff
    del list[1], list[-1]

    #use plot.py to plot list
    plot.plot(list, True)

    print ("DONE")