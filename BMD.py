import numpy
import plot

#applied loads by car : m1 = locomotive, m2 = middle car, m3 = last car
m1, m2, m3 = 439, 289, 318 ##final load case
#m1, m2, m3 = 400 / 3, 400 / 3, 400 / 3  ## load case 1

#spacing constants between applied loads (as given from front of train) [offsets]
spacing = [0, -176, -340, -516, -680, -856]

#dimensions of bridge
#length of bridge kept constant at 1250 mm long

#interval at which the train is placed to generate SFE and BME
sample_frequency = 10

#returns dictionary containing position (mm) and applied load at said position (N)
#finds reaction forces for the train at a given position
def find_reactions(pos):
    out = {}

    #add all loads applied by train (using 'spacing')
    for i in range (len(spacing)):
        if not (0 < pos + spacing[i] < 1250): continue
        if (i < 2):
            out[pos + spacing[i]] = - m1 / 2
            continue
        elif (i < 4):
            out[pos + spacing[i]] = - m2 / 2
            continue
        else:
            out[pos + spacing[i]] = -m3 / 2
            continue
    
    #initialize reaction force at x = 1225 (far end of bridge)
    b = 0
    #calculate sum of moments around point a (x = 25) and add to b
    for i in out.keys():
        b += (i - 25) * out[i]

    #negate and divide by distance from x = 25
    b /= -1200
    #get reaction force at a via sum(F_x) = 0
    a = -sum(out.values()) - b

    #add two reaction forces to output dictionary
    if (25 in out):
        out[25] += a
    else:
        out[25] = a

    if (1225 in out):
        out[1225] += b
    else:
        out[1225] = b
    return out

#gives an array of force magnitudes (positive up, negative down), for every millimetre along the length of the bridge
#takes in dictionary of forces at locations
def sfd(forces):
    out = []
    value = 0

    for i in range(1251):
        if i in forces:
            value += forces[i]
        out.append(value)

    return out

#creates BMD using position
#first generates SFD at location
#then takes integral (sum) of SFD to produce BMD
def bmd(pos):
    d = find_reactions(pos)
    forces = sfd(d)
    out = []

    for i in range(1251):
        out.append(numpy.sum(forces[:i]))
    
    return out

#generates a BMD for every possible position of the train
#from when front wheels enter, to when back wheels leave
def BME():
    env = bmd(0)
    for i in range(0, 1251 + 856, sample_frequency):
        bmdd = bmd(i)
        #maxxes the two lists together, putting maximum value of two lists
        env = [m if abs(m) > abs(e) else e for m, e in zip(env, bmdd)]
    return env

#generates SFD for every possible position of train
#returns absolute max of shear force, since direction is irrelevant in calculations
def SFE():
    env = sfd(find_reactions(0))
    for i in range(0, 1251 + 856, sample_frequency):
        sfdd = sfd(find_reactions(i))
        env = [abs(m) if abs(m) > abs(e) else e for m, e, in zip(env, sfdd)]
    
    return env

#combines minimum and maximum SFE of BME together into one absolute maximum one
def min_max(min, max, abss):
    return [(abs(m) if abss else m) if abs(m) > abs(e) else abs(e) for m, e in zip(min, max)]

#returns tuple of lists (min_sfe, max_sfe)
#both positive and negative included
def min_max_sfe():
    minout = sfd(find_reactions(0))
    maxout = sfd(find_reactions(0))

    for i in range(0, 1251 + 856, sample_frequency):
        sfdd = sfd(find_reactions(i))

        for i in range(len(minout)):
            minout[i] = min(minout[i], sfdd[i])
            maxout[i] = max(maxout[i], sfdd[i])

    return minout, maxout

#same as min_max sfe but for bme
def min_max_bme():
    minout = bmd(0)
    maxout = bmd(0)
    for i in range(0, 1251 + 856, sample_frequency):
        bmdd = bmd(i)

        for i in range(len(minout)):
            minout[i] = min(minout[i], bmdd[i])
            maxout[i] = max(maxout[i], bmdd[i])

    return minout, maxout

#combines all SFEs and BMEs into one list of strings to be plotted
def combine(MIN_SFD, MAX_SFD, ENV_SFD, MIN_BMD, MAX_BMD, ENV_BMD):
    out = []
    for i in range(len(ENV_SFD)):
        out.append(str(i) + "," + str(MIN_SFD[i]) + "," + str(MAX_SFD[i]) + "," + str(ENV_SFD[i]) + "," + str(MIN_BMD[i]) + "," + str(MAX_BMD[i]) + "," + str(ENV_BMD[i]))
    return out


if __name__ == "__main__":
    MIN_SFD, MAX_SFD = min_max_sfe()
    MIN_BMD, MAX_BMD = min_max_bme()

    ENV_BMD = min_max(MIN_BMD, MAX_BMD, False)
    ENV_SFD = min_max(MIN_SFD, MAX_SFD, True)

    print("Maximum SFE: ", max(ENV_SFD))
    print("Maximum BME: ", max(ENV_BMD))

    L = combine(MIN_SFD, MAX_SFD, ENV_SFD, MIN_BMD, MAX_BMD, ENV_BMD)
    L.insert(0, "POSITION (mm),MIN SFE (N),MAX SFE (N),SFE (N),MIN BME (N mm),MAX BME (N mm),BME (N mm)")

    del L[1], L[-1]

    plot.plot(L, False)