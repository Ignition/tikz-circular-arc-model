#!/bin/bash

python ./generate.py "${1}" | pdflatex --jobname "${1%.*}" --
