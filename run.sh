#!/bin/bash


set -x 
source `pwd`/.venv/bin/activate

python pi_coffee_scale/run.py  --log=DEBUG
