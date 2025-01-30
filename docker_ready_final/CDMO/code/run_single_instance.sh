#!/bin/bash

# Check if an argument is provided
if [ -z "$1" ]; then
    echo "Usage: $0 <number between 1 and 21>"
    exit 1
fi

# Validate that the argument is a number between 1 and 21
if ! [[ "$1" =~ ^[0-9]+$ ]]; then
    echo "Error: Argument must be a valid number."
    exit 1
fi

if (( "$1" < 1 || "$1" > 21 )); then
    echo "Error: Number must be between 1 and 21."
    exit 1
fi

# Store the argument
ARG_NUM=$1

# Navigate to the MIP directory and run the script
cd MIP || exit
echo "MIP running-----------------------"
python3 mip_model.py "$ARG_NUM"

# Navigate back to the parent directory
cd ..

cd CP || exit
echo "CP running-----------------------"
python3 convert_instances.py
python3 run_instance.py "$ARG_NUM"

# Navigate back to the parent directory
cd ..
echo "SMT running-----------------------"
cd SMT || exit
python3 get_smt_json.py "$ARG_NUM"
