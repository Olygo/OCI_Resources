# -*- coding: utf-8 -*-

# Use merge.py in order to merge cost or report files into a single file

# Pre requisite : Pandas library
# Pandas can be installed via pip from PyPI using:
# pip install pandas --user


import os
import glob
import pandas as pd

#set working directory
os.chdir("/home/opc/reports")

#find all csv files in the folder
#use glob pattern matching -> extension = 'csv'
#save result in list -> all_filenames

extension = 'csv'
all_filenames = [i for i in glob.glob('*.{}'.format(extension))]
#print(all_filenames)

#combine all files in the list
combined_csv = pd.concat([pd.read_csv(f) for f in all_filenames ])
#export to csv
combined_csv.to_csv( "combined_csv.csv", index=False, encoding='utf-8-sig')