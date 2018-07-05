import os

#write to trainval
def write_trainval():
	x = 531
	file = open(r'C:\Users\User\Documents\Python Scripts\Sublime\yolov2-tensorflow-master\data\pascal_voc\VOCdevkit\VOC2007\ImageSets\Main\trainval.txt','w')
	for i in range(x):
		file.write(str(i))
		file.write('\n')
	file.close()

def write_x_train():
	file = open(r'C:\Users\User\Documents\Python Scripts\Sublime\yolov2-tensorflow-master\data\pascal_voc\VOCdevkit\VOC2007\ImageSets\Main\pothole_train.txt','w')	
	value = 1
	for i in range(532):
		if(i == 0):
			pass
		elif(i == 41):
			value = -1
		else:
			value = 1
		file.write(str(i)+" "+str(value))
		file.write('\n')
	file.close()

write_x_train()
