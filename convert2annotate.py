import os
import pandas as pd

def read_txt():
	file_dir = 'C:\\Users\\User\\Downloads\\BBox-Label-Tool-master\\BBox-Label-Tool-master\\Labels\\001//'
	file = ''
	while file in file_dir:
		print(file)
		file_object = open(file,'r')
		print(file_object)

read_txt()