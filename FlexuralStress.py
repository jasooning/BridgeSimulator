import BMD
import CrossSection
#find peak flexural stresses
sigma_T = 30 #MPa
sigma_C = 6 #MPa

if __name__ == "__main__":


    ENV = BMD.envelope()

    rects = CrossSection.get_rects()

    I = CrossSection.I(rects)
    yb = CrossSection.ybar_bot(rects)
    yt = CrossSection.ybar_top(rects)

    Mmax = max(ENV)

    #tension on bottom
    sT = Mmax * yb / I

    #compression on top
    sC = Mmax * yt / I

    #print whether they pass or fail
    print ("ST", sT, "PASS" if (sT < sigma_T) else "FAIL")
    print ("SC", sC, "PASS" if (sC < sigma_C) else "FAIL")