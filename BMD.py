import numpy
from pylab import loadtxt

# masses of m1 = wagons, m2 = locomotive
m1 = 135
m2 = 182
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
            out[pos + spacing[i]] = - m2 / 2
            #out.append((pos + spacing[i], m2 / 2))
        else:
            out[pos + spacing[i]] = - m1 / 2
            #out.append((pos + spacing[i], m1 / 2))

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

def envelope():
    env = bmd(0)
    for i in range(0, 1251 + 856, 10):
        #print ("WORKING")
        bmdd = bmd(i)
        env = [m if abs(m) > abs(e) else e for m, e in zip(env, bmdd)]
        #env = maxl(env, bmdd)
    print ("DONE")
    return env

def maxl(a, b):
    out = []
    for i in range(len(a)):
        out.append(max(a[i], b[i]))
    return out

def print_hi():
    print("HI")

if __name__ == "__main__":


    R = find_reactions(1028)
    SFD = sfd(R)
    BMD = bmd(1028)

    ENV = envelope()

#for i in range(len(BMD)):
#    print (i, BMD[i])

#print(ENV)




    with open ("/Users/gregoryparamonau/Desktop/BRIDGE/BMD1.txt", "w") as file:
        for i in range(len(BMD)):
            file.write(str(i) + " " + str(SFD[i]) + " " + str(BMD[i]) + " " + str(ENV[i]) + " \n")


