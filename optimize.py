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

#first function, test BMD & find max and min values
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

def plate_buckling(rects, ybar, BMD):
    global E, mu, sigma_C, diaphragm_spacing

    h_rects = []
    v_rects = []

    #split into horizontal & vertical rects
    for i in rects:
        if (i[2] > i[3]): h_rects.append(i)
        else: v_rects.append(i)

    #split horizontal rects into sections
    done = False
    #create deep copy of list

    h_split = []
    taller = CrossSection.make_taller(v_rects)

    for h in h_rects:
        h_split.extend(CrossSection.cleave(h, taller))

    type_dict = {}
    for h in h_split:
        for real in h_rects:
            #check if intersect
            temp_int = CrossSection.intersect(h, real)
            if (temp_int[2] == 0 and temp_int[3] == 0): continue

            #inv_intersect h[expand by 1] with real
            #if nothing left (ie only rect = none) then type 1
            #if a bit left () -> type 2

            wider_left = [h[0] - 0.6, h[1], h[2] + 1, h[3]]
            wider_right = [h[0] + 0.6, h[1], h[2] + 1, h[3]]

            int_left = CrossSection.int_list(wider_left, taller)
            int_right = CrossSection.int_list(wider_right, taller)

            type_dict[tuple(h)] = (1 if (int_left and int_right) else 2)
    
    #find case 3:
    #only consider case where compression on top
    #take exclusive_or of vertical ones and 'bottom rect'

    bottom = [0, ybar - 1000, 1000, 1000 * 2]

    v_split = []
    for i in v_rects:
        v_split.extend(CrossSection.inv_intersect(i, bottom))

    for v in v_split:
        type_dict[tuple(v)] = 3
    
    for v in v_rects:
        type_dict[tuple(v)] = 4

    
    #now do math for every type

    min1 = float("inf")
    min2 = float("inf")
    min3 = float("inf")
    min4 = float("inf")

    print_dict(type_dict)

    # find the smallest diaphragm spacing
    BMD_max = max(BMD, key = abs)

    for i in type_dict.items():
        if (i[1] == 1):
            #M = sigma_crit * I / y_max
            #FOS = M_min / M_actual
            sigma_crit = 4 * numpy.pi ** 2 * E / 12 / (1 - mu) ** 2 * (i[0][3] / i[0][2]) ** 2
            M_min = sigma_crit * I / (max(abs(i[0][1] - i[0][3] - ybar), abs(i[0][1] + i[0][3] - ybar)))
            min1 = min(min1, M_min / BMD_max)

            #min1 = min(min1, 4 * numpy.pi ** 2 * E / 12 / (1 - mu) ** 2 * (i[0][3] / i[0][2]) ** 2)
        elif (i[1] == 2):
            sigma_crit = 0.425 * numpy.pi ** 2 * E / 12 / (1 - mu) ** 2 * (i[0][3] / i[0][2]) ** 2
            M_min = sigma_crit * I / (max(abs(i[0][1] - i[0][3] - ybar), abs(i[0][1] + i[0][3] - ybar)))

            min2 = min(min2, M_min / BMD_max)

            #min2 = min(min2, 0.425 * numpy.pi ** 2 * E / 12 / (1 - mu) ** 2 * (i[0][3] / i[0][2]) ** 2)
        elif (i[1] == 3):
            sigma_crit = 6 * numpy.pi ** 2 * E / 12 / (1 - mu) ** 2 * (i[0][2] / i[0][3]) ** 2
            M_min = sigma_crit * I / (max(abs(i[0][1] - i[0][3] - ybar), abs(i[0][1] + i[0][3] - ybar)))

            min3 = min(min3, M_min / BMD_max)

            #min3 = min(min3, 6 * numpy.pi ** 2 * E / 12 / (1 - mu) ** 2 * (i[0][2] / i[0][3]) ** 2)
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


                #min4 = min(min4, 5 * numpy.pi ** 2 * E / 12 / (1 - mu) ** 2 * ((i[0][2] / a) ** 2 + (i[0][2] / i[0][3]) ** 2))
            #need diaphragm spacing here : TODO
            pass

    #find case-1s
    #2-sides restrained on cross-section (horizontally)

    return {
        "TYPE 1 PLATE BUCKLING" : min1, 
        "TYPE 2 PLATE BUCKLING" : min2, 
        "TYPE 3 PLATE BUCKLING" : min3, 
        "TYPE 4 PLATE BUCKLING" : min4 #sigma_C / min4
    }

def rect_equal(a, b, eps=1e-9):
    """
    Compare two rectangles [x, y, w, h] for equality using a tolerance.
    Returns True if all corresponding values are within eps.
    """
    return all(abs(ai - bi) < eps for ai, bi in zip(a, b))

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
    FOS_flex = flex_stress(BMD_ENV, I, y_top, y_bot)
    FOS_shear = shear_stress(SFD_ENV, Q, I, b)
    FOS_plate_buckling = plate_buckling(rects, ybar, BMD_ENV)

    print_dict(FOS_flex)
    print_dict(FOS_shear)
    print_dict(FOS_plate_buckling)
    #print (FOS_flex, FOS_shear, FOS_plate_buckling)

