#!/bin/bash

# Navigate to the MIP directory and run the script
cd MIP || exit
python3 mip_model.py

# Navigate back to the parent directory
cd ..

cd ConstraintProgramming || exit
python3 run_instance.py




