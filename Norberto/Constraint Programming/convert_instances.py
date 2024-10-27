import os

def convert_all_dat_to_minizinc_input(dat_files_dir, output_dir):
    """
    Converts all .dat files in the specified directory to .dzn files and saves them in the output directory.
    """
    dat_files = [f for f in os.listdir(dat_files_dir) if f.endswith('.dat')]
    
    # Ensure output directory exists
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    for dat_file in dat_files:
        full_path = os.path.join(dat_files_dir, dat_file)
        
        # Read the .dat file and process it
        with open(full_path, 'r') as file:
            lines = file.readlines()
        
        # Extract data from the .dat file
        m = int(lines[0])
        n = int(lines[1])
        l = list(map(int, lines[2].split()))
        s = list(map(int, lines[3].split()))
        D = [list(map(int, line.split())) for line in lines[4:]]
        
        # Convert to MiniZinc format
        minizinc_data = f"m = {m};\n"
        minizinc_data += f"n = {n};\n"
        minizinc_data += f"l = [{', '.join(map(str, l))}];\n"
        minizinc_data += f"s = [{', '.join(map(str, s))}];\n"
        
        minizinc_data += "D = [|"
        for row in D:
            minizinc_data += ", ".join(map(str, row)) + " \n|"
        minizinc_data = minizinc_data.rstrip(" |\n| ") + "|];\n"
        
        # Save the converted data to a .dzn file in the output directory
        output_file = os.path.join(output_dir, os.path.splitext(dat_file)[0] + ".dzn")
        with open(output_file, 'w') as out_file:
            out_file.write(minizinc_data)
        
        print(f"Converted {dat_file} to {output_file}")

# Directory where .dat files are stored
dat_files_dir = '../Instances/'  # Modify this to the actual directory with your .dat files

# Output directory for the converted .dzn files
output_dir = './dzn_files/'

# Run the conversion
convert_all_dat_to_minizinc_input(dat_files_dir, output_dir)
