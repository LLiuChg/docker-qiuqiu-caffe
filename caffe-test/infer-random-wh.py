#-*- coding:UTF-8 -*-
from __future__  import division
import math
import sys
import os
os.environ['GLOG_minloglevel'] = '3'
sys.path.insert(0,"/root/dog-qiuqiu/caffe/python")
import caffe
import numpy as np
import cv2
from collections import Counter
import time,os
from tqdm import tqdm

#nms算法
def nms(dets, thresh=0.4):
	#dets:N*M,N是bbox的个数，M的前4位是对应的（x1,y1,x2,y2），第5位是对应的分数
	#thresh:0.3,0.5....
	x1 = dets[:, 0]
	y1 = dets[:, 1]
	x2 = dets[:, 2]
	y2 = dets[:, 3]
	scores = dets[:, 4]
	areas = (x2 - x1 + 1) * (y2 - y1 + 1)#求每个bbox的面积
	order = scores.argsort()[::-1]#对分数进行倒排序
	keep = []#用来保存最后留下来的bbox
	while order.size > 0:
		i = order[0]#无条件保留每次迭代中置信度最高的bbox
		keep.append(i)
		#计算置信度最高的bbox和其他剩下bbox之间的交叉区域
		xx1 = np.maximum(x1[i], x1[order[1:]])
		yy1 = np.maximum(y1[i], y1[order[1:]])
		xx2 = np.minimum(x2[i], x2[order[1:]])
		yy2 = np.minimum(y2[i], y2[order[1:]])
		#计算置信度高的bbox和其他剩下bbox之间交叉区域的面积
		w = np.maximum(0.0, xx2 - xx1 + 1)
		h = np.maximum(0.0, yy2 - yy1 + 1)
		inter = w * h
		#求交叉区域的面积占两者（置信度高的bbox和其他bbox）面积和的必烈
		ovr = inter / (areas[i] + areas[order[1:]] - inter)
		#保留ovr小于thresh的bbox，进入下一次迭代。
		inds = np.where(ovr <= thresh)[0]
		#因为ovr中的索引不包括order[0]所以要向后移动一位
		order = order[inds + 1]
	return keep

#定义sigmod函数
def sigmod(x):
  	return 1.0 / (1.0 + math.exp(-x))

#检测模型前向运算
def Load_YOLO_model(net,test_img,feature_conv_name):
	# input_img = cv2.resize(test_img,(INPUT_SIZE_w,INPUT_SIZE_h),interpolation=cv2.INTER_AREA)
	input_img = cv2.resize(test_img,(INPUT_SIZE_w,INPUT_SIZE_h))
	input_img = cv2.cvtColor(input_img, cv2.COLOR_BGR2RGB)
	input_img = input_img.transpose(2,0,1)
	input_img = input_img.reshape((1,3,INPUT_SIZE_h,INPUT_SIZE_w))
	out = net.forward_all(data=input_img/255.)
	shape = []
	for i in range(2):
		# print(out[feature_conv_name[i]])
		shape.append(out[feature_conv_name[i]].transpose(0, 3, 2, 1)[0])
	return shape

#处理前向输出feature_map
def feature_map_handle(length, shape, test_img, box_list):
	ih,iw,_ = test_img.shape
	confidence = CONFIDENCE_DICT[str(length)]
	
	for i in range(len(shape)):
		#print(len(shape[i]))
		for j in range(len(shape[0])):
			anchors_boxs_shape = shape[i][j].reshape((3, CLASS_NUM + 5))
			#将每个预测框向量包含信息迭代出来
			for k in range(3):
				anchors_box = anchors_boxs_shape[k]
				#print(anchors_box[0],anchors_box[1],anchors_box[2],anchors_box[3],anchors_box[4],anchors_box[5])
				
				#计算实际置信度,阀值处理,anchors_box[7]
				score = sigmod(anchors_box[4])
				if score > confidence:
					#tolist()数组转list
					cls_list = anchors_box[5:CLASS_NUM + 5].tolist()
					label = cls_list.index(max(cls_list))
					obj_score = score * sigmod(anchors_box[label+5])
					x = ((sigmod(anchors_box[0]) + i)/float(len(shape)))*iw
					y = ((sigmod(anchors_box[1]) + j)/float(len(shape[0])))*ih
					feature_map_size = int(INPUT_SIZE_w/32)
					if length == feature_map_size:
						w = (((BIAS_W[k+3]) * math.exp(anchors_box[2]))/INPUT_SIZE_w)*iw
						h = (((BIAS_H[k+3]) * math.exp(anchors_box[3]))/INPUT_SIZE_h)*ih
					elif length == feature_map_size*2: 
						w = (((BIAS_W[k]) * math.exp(anchors_box[2]))/INPUT_SIZE_w)*iw
						h = (((BIAS_H[k]) * math.exp(anchors_box[3]))/INPUT_SIZE_h)*ih
					x1 = int(x - w * 0.5)
					x2 = int(x + w * 0.5)
					y1 = int(y - h * 0.5)
					y2 = int(y + h * 0.5)
					box_list.append([x1,y1,x2,y2,round(obj_score,4),label])


#3个feature_map的预选框的合并及NMS处理
def dect_box_handle(out_shape, test_img):
	box_list = []
	output_box = []
	for i in range(2):
		length =  len(out_shape[i])
		# print(length)
		# print(out_shape[i])
		feature_map_handle(length, out_shape[i], test_img, box_list)
	if box_list:
		retain_box_index = nms(np.array(box_list))
		for i in retain_box_index:
			output_box.append(box_list[i])
	return output_box

if __name__ == "__main__":
	#类别数目
	CLASS_NUM = 1
	#输入图片尺寸	
	INPUT_SIZE_w = 640
	INPUT_SIZE_h = 384
	#加载label文件
	LABEL_NAMES = ["person"]
	# with open('voc.names', 'r') as f:
	#    for line in f.readlines():
	#       LABEL_NAMES.append(line.strip())
	#置信度
	# CONFIDENCE_DICT = {"13":0.2, "26":0.2} 
	CONFIDENCE_DICT = {"20":0.45, "40":0.45} 
	#模型训练时设置的anchor_box比例
	#26, 48,  67, 84,  72,175, 189,126, 137,236, 265,259
	BIAS_W = [49, 48, 83, 123, 135, 169]
	BIAS_H = [60, 150, 146, 163, 228, 273]    # 7, 16,  12, 28,  19, 46,  31, 76,  57,135, 168,297
	#需要输出的３层feature_map的名称
	feature_conv_name = ["layer70-conv","layer80-conv"]
	#加载检测模型
	net = caffe.Net('./model/headCount_0514_best_no_bn.prototxt', './model/headCount_0514_best_no_bn.caffemodel', caffe.TEST)
	#################################
	img_dir = "./img/"
	xml_dir = "./det_res_txt/"
	LLL = []
	for img_name in tqdm(os.listdir(img_dir)):           #for img_name in tqdm(os.listdir(img_dir)):
		# print('###############')
		imgpath = os.path.join(img_dir, img_name)
		input_img = cv2.imread(imgpath)
		if input_img is None:
			print(img_name)
			LLL.append(img_name)
			continue
		imgw = input_img.shape[1]
		imgh = input_img.shape[0]
		out_shape = Load_YOLO_model(net,input_img,feature_conv_name)
		output_box = dect_box_handle(out_shape, input_img)

		tag = ''
		if len(output_box) == 0:
			tag = '_'
			# continue

		# save_name = xml_dir + img_name[0:-4] + '.txt'
		save_name = xml_dir + tag + img_name[0:-4] + '.txt'
		fw = open(save_name,'w')
		for i in output_box:
			res = ''
			# print("xmin is {},ymin is {}, xmax is {}, ymax is {}, score is {}".format(i[0],i[1],i[2],i[3], i[4]))
			xminv = i[0]
			yminv = i[1]
			xmaxv = i[2]
			ymaxv = i[3]
			w = (xmaxv - xminv) / imgw
			h = (ymaxv - yminv) / imgh
			xc = ((xmaxv - xminv) / 2 + xminv) / imgw
			yc = ((ymaxv - yminv) / 2 + yminv) / imgh
			res = res + '0 ' + str(xc) + ' '+ str(yc) + ' '+ str(w) + ' '+ str(h) + '\n'
			fw.write(res)

			cv2.rectangle(input_img, (i[0], i[1]), (i[2], i[3]), (255, 255, 0), 3)
			cv2.circle(input_img, (int(i[0]+0.5*(i[2]-i[0])), int(i[1]+0.5*(i[3]-i[1]))), 2, (0,255,0), 3)			
			cv2.putText(input_img, "Score:"+str(i[4]), (i[0], i[1]-5), 0, 0.7, (255, 0, 255), 2)	
			cv2.putText(input_img, "Label:"+str(LABEL_NAMES[i[5]]), (i[0], i[1]-20), 0, 0.7, (255, 255, 0), 2)
		# cv2.imshow("capture", input_img)
		# cv2.imwrite("qiuqiu.jpg",input_img)
		# cv2.waitKey(0)
		# cv2.imwrite('./Images1/' + img_name,input_img)
		cv2.imwrite('./det_res_img/' + tag + img_name,input_img)
	# cv2.waitKey(0)
	print(LLL)
