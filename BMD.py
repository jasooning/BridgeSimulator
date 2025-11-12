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
        if (i < 2):
            out[pos + spacing[i]] = - m2 / 2
            #out.append((pos + spacing[i], m2 / 2))
        else:
            out[pos + spacing[i]] = - m1 / 2
            #out.append((pos + spacing[i], m1 / 2))
    
    #find B
    temp = {}
    for i in out.keys():
        if (i >= 0):
            temp[i] = out[i]
    out = temp

    b = 0
    for i in out.keys():
        b += (i - 25) * out[i]
    
    b /= -1200
    a = m1 + m1 + m2 - b
    out[25] = a
    out[1225] = b

    return out
    


#gives an array of force magnitudes (positive up, negative down), for every millimetre along the length of the bridge
#takes input of array of tuples (position (from left), force magnitude)
def sfd(forces):
    out = []

    value = 0

    for i in range(1250):
        if i in forces:
            value += forces[i]
        out.append(value)

    return out

def bmd(pos):
    d = find_reactions(pos)
    forces = sfd(d)

    out = []
    for i in range(1250):
        out.append(numpy.sum(forces[:i]))
    
    return out


R = find_reactions(1028)
SFD = sfd(R)
BMD = bmd(1028)

#for i in range(len(BMD)):
#    print (i, BMD[i])


with open ("/Users/gregoryparamonau/Desktop/BRIDGE/BMD1.txt", "w") as file:
    for i in range(len(BMD)):
        file.write(str(i) + " " + str(SFD[i]) + " " + str(BMD[i]) + " \n")

