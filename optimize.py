import BMD
import CrossSection
import copy
import numpy


#test 10 ways the bridge can fail

#1 - 4
#tension & compression at two maximum values for bending moment (envelope only has 1...) CHECK

#5-6
#shear stress failure [CHECK] + glue shear stress failure [TODO]
#tau = VQ / Ib

#7-10
#case 1, 2, 3 of plate buckling + shear buckling

#constants: #MPa
# define here, I'm placing them at increments of 100 to start with
diaphragm_spacing = [25, 125, 225, 325, 425, 525, 625, 725, 825, 925, 1025, 1125, 1225]

tau_max = 4
tau_glue = 2
sigma_C = 6
sigma_T = 30

E = 4000
mu = 0.2

#function returns FOS's of all possible flexural stresses along the bridge [assumes constant crosssection] [TODO]
def flex_stress(BMD, I, y_top, y_bot):
    global sigma_C, sigma_T

    Mmax = max(BMD)
    Mmin = abs(min(BMD))

    #tension & compression at Mmax (compression top, tension bottom)

    fos_c_top = sigma_C / (Mmax * y_top / I)
    fos_t_bot = sigma_T / (Mmax * y_bot / I)

    #tension & compressiont at Min

    fos_c_bot = sigma_C / (Mmin * y_bot / I)
    fos_t_top = sigma_T / (Mmin * y_top / I)

    #FOS: c_top, t_bot, c_bot, t_top
    #return dictionary
    return {
        "Max Tension at Top" : fos_t_top, 
        "Max Compression at Top" : fos_c_top,
        "Max Tension at Bottom" : fos_t_bot,
        "Max Compression at Bottom" : fos_c_bot
    }

#function that calculates maximum shear stress applied to material [assumes constant cross-section so far] TODO
#returns FOS's for both shear-stress failure and shear-glue failure [TODO]
def shear_stress(SFE, Q, I, b):

    global tau_max, tau_glue

    V = max(max(SFE), abs(min(SFE)))

    #print (V, Q, I, b)

    #don't forget to implement glue tabs

    tau = V * Q / I / b
    return {
        "Material Shear Stress" : tau_max / tau,
        "Glue Shear Stress" : 0 # TODO
    }

#function that splits crosssection into different plate-buckling cases
#then calculates all minimum FOS's for each plate buckling case

def plate_buckling(rects, ybar, BMD):
    global E, mu, sigma_C, diaphragm_spacing

    h_rects = []
    v_rects = []

    #split into horizontal & vertical rects
    for i in rects:
        if (i[2] > i[3]): h_rects.append(i)
        else: v_rects.append(i)

    h_split = []
    taller = CrossSection.make_taller(v_rects)

    #create an array of 'taller' vertical rectangles, which are used to 'cleave' the horizontal rects s.t.
    #they can be classified according to the plate buckling cases

    for h in h_rects:
        h_split.extend(CrossSection.cleave(h, taller))

    #handles sorting case 1 & 2 plate buckling
    type_dict = {}
    for h in h_split:
        for real in h_rects:
            #check if intersect
            temp_int = CrossSection.intersect(h, real)
            if (temp_int[2] == 0 and temp_int[3] == 0): continue

            #create two rects, one shifted slightly left, one shifted slightly right
            #if both of these intersect an extended vertical, then the rectangle is case-1 plate buckling
            #if only one of these intersects, then rectangle is case-2 plate buckling

            wider_left = [h[0] - 0.6, h[1], h[2] + 1, h[3]]
            wider_right = [h[0] + 0.6, h[1], h[2] + 1, h[3]]

            int_left = CrossSection.int_list(wider_left, taller)
            int_right = CrossSection.int_list(wider_right, taller)

            #if rectangle below centroid axis its in tension, hence needs to be filtered out not to mess with results
            if (h[1] - h[3] / 2 > ybar) : 
                type_dict[tuple(h)] = (1 if (int_left and int_right) else 2)
    
    v_split = []
    wider = CrossSection.make_wider(h_rects)

    for v in v_rects:
        v_split.extend(CrossSection.cleave(v, wider))

    bottom = [0, ybar - 1000, 1000, 1000 * 2]

    #v-split = every vertical with the bottom part (tension) removed
    #case-3 plate buckling
    v_split_bottom = []
    for i in v_split:
        v_split_bottom.extend(CrossSection.inv_intersect(i, bottom))

    #create case-3 rects
    for v in v_split_bottom:
        type_dict[tuple(v)] = 3

    #all vertical rects are subject to case-4 shear buckling, hence those are lumped together
    for v in v_split:
        type_dict[tuple(v)] = 4

    
    #now do math for every type
    #originally begin with 'infinity' FOS, and go down to minimum check
    min1 = float("inf")
    min2 = float("inf")
    min3 = float("inf")
    min4 = float("inf")

    #making sure that the dictionary of rects & types is valid
    print_dict(type_dict)

    #find maximum moment in BMD -> used for calculating FOS for case 1-3 plate buckling
    BMD_max = max(BMD, key = abs)

    for i in type_dict.items():
        if (i[1] == 1):
            #M = sigma_crit * I / y_max
            #FOS = M_min / M_actual
            sigma_crit = 4 * numpy.pi ** 2 * E / 12 / (1 - mu) ** 2 * (i[0][3] / i[0][2]) ** 2
            M_min = sigma_crit * I / (max(abs(i[0][1] - i[0][3] - ybar), abs(i[0][1] + i[0][3] - ybar)))
            min1 = min(min1, M_min / BMD_max)

        elif (i[1] == 2):
            sigma_crit = 0.425 * numpy.pi ** 2 * E / 12 / (1 - mu) ** 2 * (i[0][3] / i[0][2]) ** 2
            M_min = sigma_crit * I / (max(abs(i[0][1] - i[0][3] - ybar), abs(i[0][1] + i[0][3] - ybar)))

            min2 = min(min2, M_min / BMD_max)

        elif (i[1] == 3):
            sigma_crit = 6 * numpy.pi ** 2 * E / 12 / (1 - mu) ** 2 * (i[0][2] / i[0][3]) ** 2
            M_min = sigma_crit * I / (max(abs(i[0][1] - i[0][3] - ybar), abs(i[0][1] + i[0][3] - ybar)))

            min3 = min(min3, M_min / BMD_max)

        elif (i[1] == 4):
            #check entire length of bridge w all diaphragms for maximum Pcrit & any failure caused by Pcrit (TODO)
            #min4 = FOS
            for j in range(1, len(diaphragm_spacing)):
                #sigma_crit = My / I
                #M = sigma_crit * I / y_max

                #FOS = M_min / M_actual


                a = diaphragm_spacing[j] - diaphragm_spacing[j - 1]
                M_actual = max(BMD[diaphragm_spacing[j]], BMD[diaphragm_spacing[j - 1]]) # need this for proper FOS calculations using Pcrit
                sigma_crit = 5 * numpy.pi ** 2 * E / 12 / (1 - mu) ** 2 * ((i[0][2] / a) ** 2 + (i[0][2] / i[0][3]) ** 2)

                M_min = sigma_crit * I / (max(abs(i[0][1] - i[0][3] - ybar), abs(i[0][1] + i[0][3] - ybar)))

                min4 = min(min4, M_min / M_actual)

    return {
        "TYPE 1 PLATE BUCKLING" : min1, 
        "TYPE 2 PLATE BUCKLING" : min2, 
        "TYPE 3 PLATE BUCKLING" : min3, 
        "TYPE 4 PLATE BUCKLING" : min4
    }

#print dictionary in readable format
def print_FOS(fos_dict):
    """
    Print a dictionary of FOS values in aligned columns.
    """
    # Determine the longest key
    max_key_len = max(len(str(k)) for k in fos_dict)
    
    for k, v in fos_dict.items():
        # Left-align key, left-align value (with 6 decimal places)
        print(f"{k.ljust(max_key_len)} : {v:<12.6f}")


def print_dict(dict):
    for i in dict.items():
        print (i[0], i[1])


if __name__ == "__main__":
    #define everything
    BMD_ENV = BMD.BME()
    SFD_ENV = BMD.SFE()

    rects = CrossSection.get_rects()
    print ("rects", rects)

    #print ([i if i[2] > i[3] else None for i in rects])

    #flexural stresses
    I = CrossSection.I(rects)
    ybar = CrossSection.ybar(rects)
    y_top = CrossSection.ybar_top(rects)
    y_bot = CrossSection.ybar_bot(rects)

    #shear stresses
    Q = CrossSection.Q(rects, ybar)
    print ("Q", Q)
    b = CrossSection.width_at_centroid(rects, ybar)

    #flexural stresses
    FOS = flex_stress(BMD_ENV, I, y_top, y_bot)
    FOS = FOS | shear_stress(SFD_ENV, Q, I, b)
    FOS = FOS | plate_buckling(rects, ybar, BMD_ENV)

    FOS = dict(sorted(FOS.items(), key = lambda item: item[1]))
    print()
    print_FOS (FOS)
    #print (FOS_flex, FOS_shear, FOS_plate_buckling)

