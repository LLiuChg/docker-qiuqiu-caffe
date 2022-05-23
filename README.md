README

参考[caffe docker](https://github.com/BVLC/caffe/tree/master/docker)

```
$ docker build -t caffe-dog:cpu release/

$ docker run -it --name dog-caffe caffe-dog:cpu /bin/bash

$ docker cp caffe-test dog-caffe:/root

$ docker exec -it dog-caffe bash

$ cd /root 

$ python infer-random-wh.py
```



或者

```
$ docker build -t caffe-dog:cpu cpu
```



**上传docker**

```
$ docker login
$ docker images
$ docker tag caffe-dog:cpu chliu4890/dog-qiuqiu-caffe
$ docker images
$ docker push chliu4890/dog-qiuqiu-caffe

docker id : chliu4890
```

