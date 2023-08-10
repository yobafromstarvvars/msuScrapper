#!/bin/bash
source venv/bin/activate;
python findPersonMsu.py $1 $2 $3;
python findPersonVk.py;
deactivate;
