if __name__ == "__main__":
    filename = "./Design Iterations/design1.txt"

    with open(filename, "r") as f:
        for line in f:
            line = line.rstrip("\n")
            temp = "polygon" + line
            print (temp)