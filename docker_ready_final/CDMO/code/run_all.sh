#!/bin/bash

# Navigate to the MIP directory and run the script
echo "MIP running-----------------------"
cd MIP || exit
python3 mip_model.py

# Navigate back to the parent directory
cd ..

cd CP || exit
echo "CP running-----------------------"
python3 convert_instances.py
python3 run_instance.py

# Navigate back to the parent directory

cd ..
echo "SMT running-----------------------"
cd SMT || exit
python3 get_smt_json.py




