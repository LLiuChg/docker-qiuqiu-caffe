FROM ubuntu:16.04
RUN sed -i s:/archive.ubuntu.com:/mirrors.tuna.tsinghua.edu.cn/ubuntu:g /etc/apt/sources.list
RUN cat /etc/apt/sources.list
LABEL maintainer caffe-maint@googlegroups.com

COPY ./assets /root

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        cmake \
        git \
        wget \
        vim \
        libatlas-base-dev \
        libboost-all-dev \
        libgflags-dev \
        libgoogle-glog-dev \
        libhdf5-serial-dev \
        libleveldb-dev \
        liblmdb-dev \
        libopencv-dev \
        libprotobuf-dev \
        libsnappy-dev \
        protobuf-compiler \
        python-dev \
        python-numpy \
        #python-pip \
        python-setuptools \
        python-scipy && \
        #wget https://bootstrap.pypa.io/pip/2.7/get-pip.py && \
        cd /root && \
        python get-pip.py && \
        rm get-pip.py  && \
    rm -rf /var/lib/apt/lists/*

ENV CAFFE_ROOT=/opt/caffe
WORKDIR $CAFFE_ROOT

RUN mv /root/caffe /opt/ && \
    cd /opt/caffe  && \
    pip install --upgrade pip && \
    cd python && for req in $(cat requirements.txt) pydot; do pip install $req -i https://pypi.douban.com/simple/; done && cd .. && \
    pip install opencv-python==4.2.0.32 -i https://pypi.douban.com/simple/  && \
    pip install --upgrade scikit-image -i https://pypi.douban.com/simple/  && \
    pip install tqdm -i https://pypi.douban.com/simple/  && \
    mkdir build && cd build && \
    cmake -DCPU_ONLY=1 .. && \
    make -j"$(nproc)"

ENV PYCAFFE_ROOT $CAFFE_ROOT/python
ENV PYTHONPATH $PYCAFFE_ROOT:$PYTHONPATH
ENV PATH $CAFFE_ROOT/build/tools:$PYCAFFE_ROOT:$PATH
RUN echo "$CAFFE_ROOT/build/lib" >> /etc/ld.so.conf.d/caffe.conf && ldconfig

WORKDIR /workspace
