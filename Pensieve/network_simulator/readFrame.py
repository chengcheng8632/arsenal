# -*- coding: utf-8 -*-
"""
read frame data from log.txt, then output serial Object, at same time they are saved on disk
"""
try:
    import cPickle as pickle
except ImportError:
    import pickle
import re
import matplotlib.pyplot as plt

import numpy as np


def generate_frame_size():
    f_f_size = open("../videoFrame/frame_size.pk", "wb", 0)
    d = dict()

    base_path = "log/"
    for i_file in range(1, 21):
        list_size = []
        file_name = base_path + str(i_file) + ".txt"
        file_frame = open(file_name, "r")
        while True:
            line = file_frame.readline()
            if not line:
                break

            frame_size = re.search(r'.* size=(.*) bytes.*$', line)

            if frame_size:
                list_size.append(int(frame_size.group(1).strip()))

        d[i_file/10.0] = list_size
        file_frame.close()
    pickle.dump(d, f_f_size, 0)

    f_f_size.close()

    f_f_size = open("../videoFrame/frame_size.pk", "rb", 0)

    fsize = pickle.load(f_f_size)
    for key in fsize.keys():
        print(key)
    # 方差
    # 前后两个值的差

    print('fsize:', len(fsize))
    f_f_size.close()


def plot_every_frame_size_fig():
    f_f_size = open("../videoFrame/frame_size.pk", "rb", 0)

    fsize = pickle.load(f_f_size)
    fig = plt.figure()
    legend_name = []
    # plot_key = [1.6, 1.4, 1.2, 1.0, 0.7]
    index = 0.1
    for key in fsize.keys():
        # if key not in plot_key:
        #     continue
        data = fsize[key]
        legend_name.append(str(key*1000))
        plot_data = []
        for i in range(len(data) // 30):
            plot_data.append(sum(data[i*30:i*30 + 30]) * 8/1000)
        plt.plot(plot_data)
        pre = plot_data[:-1]
        later = plot_data[1:]
        ave = sum(plot_data)/len(plot_data)
        std = np.std(plot_data)
        print(index, ',', ave, ',', std, ',', std/ave)
        index += 0.1
        # print(sum(data) * 8/len(data)/30)

    # 方差
    # 前后两个值的差
    plt.legend(legend_name)
    plt.show()
    f_f_size.close()


def read_array_from_log(file_name):
    """
    得到 file 中的帧数据
    :param file_name:
    :return:
    """
    file_frame = open(file_name, "r")
    list_size = []
    while True:
        line = file_frame.readline()
        if not line:
            break
        frame_size = re.search(r'.* size=(.*) bytes.*$', line)
        if frame_size:
            list_size.append(int(frame_size.group(1).strip()))
    return list_size


def save_key_csv(plot_key, csv_name):
    f_f_size = open("../videoFrame/frame_size.pk", "rb", 0)
    new_size = []
    fsize = pickle.load(f_f_size)
    for key in plot_key:
        data = fsize[key]
        plot_data = []
        for i in range(len(data) // 30):
            plot_data.append(sum(data[i*30:i*30 + 30]) * 8/1000)
        new_size.append(plot_data)
    f_f_size.close()
    save_csv(csv_name, new_size)
    pass


def save_csv(file_name, fsize):
    """
    将绘图的 x, y 保存成 csv 格式
    就是每行的数据都保存成 x(i),y(i)
    用于以后使用 gnuplot 绘图
    :param x:
    :param y:
    :return:
    """
    file_name = r'csv/' + file_name
    csv = open(file_name + '.csv', 'w+')

    for i in range(len(fsize[0])):
        line = str(i+1)
        for j in range(len(fsize)):
            line += ',' + str(fsize[j][i])
        csv.write(str(line)+'\n')
    csv.close()
    pass


if __name__ == '__main__':
    # generate_frame_size()
    plot_every_frame_size_fig()
    # plot_key = [1.6, 1.4, 1.2, 1.0, 0.7]
    # save_key_csv(plot_key, 'test')
    # frame_rate = 30
    # data = read_array_from_log('one.txt')
    # print(len(data), sum(data) * 8 / (len(data)/frame_rate) / 1e6)
    # plot_data = []
    # for i in range(len(data) // frame_rate):
    #     plot_data.append(sum(data[i * frame_rate:i*frame_rate + frame_rate]) * 8 / 1000)
    # plt.plot(plot_data)
    # plt.show()

