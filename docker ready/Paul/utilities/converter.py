import sys

def main():
    if len(sys.argv) != 2:
        print("Usage: ./file_io.py <filename>")
        sys.exit(1)

    filename = sys.argv[1]

    try:
        f = open(filename, "r")
    except FileNotFoundError:
        print(f"Error: File {filename} not found")
        sys.exit(1)

    # Read the file
    lines = f.readlines()
    f.close()
    linesToWrite = []
    linesToWrite.append("m=" + lines[0].rstrip() + ";")
    linesToWrite.append("n=" + lines[1].rstrip() + ";")
    load = "l=["
    splitted = lines[2].split(" ")
    for i in range(len(splitted)):
        load += splitted[i].rstrip()
        if i != len(splitted) - 1:
            load += ","
        if i == len(splitted) - 1:
            load += "]"
    linesToWrite.append(load + ";")
    size = "s=["
    splitted = lines[3].split(" ")
    for i in range(len(splitted)):
        size += splitted[i].rstrip()
        if i != len(splitted) - 1:
            size += ","
        if i == len(splitted) - 1:
            size += "]"
    linesToWrite.append(size + ";")
    d = "D=["
    for i in range(4, len(lines)):
        splitted = lines[i].split(" ")
        for j in range(len(splitted) - 1):
            if j == 0:
                d += "|"
            d += splitted[j].rstrip()
            if j != len(splitted) - 2:
                d += ","

    d += "|]"
    linesToWrite.append(d + ";")

    fexit = open(filename.split(".")[0] + ".dzn", "w")
    for line in linesToWrite:
        fexit.write(line + "\n")
    fexit.close()

main()
    


 