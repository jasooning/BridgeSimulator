import numpy
from pylab import loadtxt
import plot

# masses of m1 = wagons, m2 = locomotive
m1 = 420 # locomotive
m2 = 277 # first car
m3 = 304 # last car
#spacing constants between applied loads (as given from front of train) [offsets]
spacing = [0, -176, -340, -516, -680, -856]

#dimensions of bridge
length = 1250

#returns tuple of tuples for both reactions (A on left, B on right), found as a sum of moments
#returns array of tuples (position, force)
def find_reactions(pos):
    global m1, m2, length
    out = {}
    #create array of train forces

    for i in range (len(spacing)):
        if not (0 <= pos + spacing[i] <= 1250): continue
        if (i < 2):
            out[pos + spacing[i]] = - m1 / 2
            continue
        elif (i < 4):
            out[pos + spacing[i]] = - m2 / 2
            continue
        else :
            out[pos + spacing[i]] = -m3 / 2
            continue

    b = 0
    for i in out.keys():
        b += (i - 25) * out[i]
    
    b /= -1200
    a = -sum(out.values()) - b
    out[25] = a
    out[1225] = b

    return out
    


#gives an array of force magnitudes (positive up, negative down), for every millimetre along the length of the bridge
#takes input of array of tuples (position (from left), force magnitude)
def sfd(forces):
    out = []

    value = 0

    for i in range(1251):
        if i in forces:
            value += forces[i]
        out.append(value)

    return out

def bmd(pos):
    d = find_reactions(pos)
    forces = sfd(d)
    out = []

    for i in range(1251):
        out.append(numpy.sum(forces[:i]))
    
    return out

def BME():
    env = bmd(0)
    for i in range(0, 1251 + 856, 10):
        #print ("WORKING")
        bmdd = bmd(i)
        env = [m if abs(m) > abs(e) else e for m, e in zip(env, bmdd)]
        #env = maxl(env, bmdd)
    print ("DONE")
    return env

def SFE():
    env = sfd(find_reactions(0))
    for i in range(0, 1251 + 856, 10):
        sfdd = sfd(find_reactions(i))
        env = [abs(m) if abs(m) > abs(e) else e for m, e, in zip(env, sfdd)]
    
    return env

def min_max(min, max, abss):
    return [(abs(m) if abss else m) if abs(m) > abs(e) else abs(e) for m, e in zip(min, max)]

def min_max_sfe():

    min = sfd(find_reactions(0))
    max = sfd(find_reactions(0))
    for i in range(0, 1251 + 856, 10):
        sfdd = sfd(find_reactions(i))
        min = [m if m < e else e for m, e in zip(min, sfdd)]
        max = [m if m > e else e for m, e in zip(max, sfdd)]
    return min, max

def min_max_bme():
    min = bmd(0)
    max = bmd(0)
    for i in range(0, 1251 + 856, 10):
        bmdd = bmd(i)
        min = [m if m < e else e for m, e in zip(min, bmdd)]
        max = [m if m > e else e for m, e in zip(max, bmdd)]
    return min, max


def maxl(a, b):
    out = []
    for i in range(len(a)):
        out.append(max(a[i], b[i]))
    return out

def combine(MIN_SFD, MAX_SFD, ENV_SFD, MIN_BMD, MAX_BMD, ENV_BMD):
    out = []
    for i in range(len(ENV_SFD)):
        out.append(str(i) + "," + str(MIN_SFD[i]) + "," + str(MAX_SFD[i]) + "," + str(ENV_SFD[i]) + "," + str(MIN_BMD[i]) + "," + str(MAX_BMD[i]) + "," + str(ENV_BMD[i]))
    return out


if __name__ == "__main__":


    R = find_reactions(1028)
    SFD = sfd(R)
    BMD = bmd(1028)

    MIN_SFD, MAX_SFD = min_max_sfe()
    MIN_BMD, MAX_BMD = min_max_bme()

    ENV_BMD = min_max(MIN_BMD, MAX_BMD, False)
    ENV_SFD = min_max(MIN_SFD, MAX_SFD, True)

    L = combine(MIN_SFD, MAX_SFD, ENV_SFD, MIN_BMD, MAX_BMD, ENV_BMD)
    L.insert(0, "POSITION (mm),MIN SFE (N),MAX SFE (N),SFE (N),MIN BME (N mm),MAX BME (N mm),BME (N mm)")

    del L[1], L[-1]

    plot.plot(L, False)

#for i in range(len(BMD)):
#    print (i, BMD[i])

#print(ENV)



'''
    with open ("/Users/gregoryparamonau/Desktop/BRIDGE/BMD1.txt", "w") as file:
        for i in range(len(BMD)):
            file.write(str(i) + " " + str(SFD[i]) + " " + str(BMD[i]) + " " + str(ENV_SFD[i]) + " " + str(ENV_BMD[i]) + " \n")'''


