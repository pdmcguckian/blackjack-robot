#!/bin/bash

unclutter -idle 0.2 &

source ~/.profile
workon cv

python3 ~/BJOS/main.py &


