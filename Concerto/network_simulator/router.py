# -*- coding: utf-8 -*-
from il.network_simulator.packet import Packet
import sys


class TimeOutException(Exception):
    def __init__(self, atleast):
        self.atleast = atleast


class PacketQueueInOneSecond(object):
    def __init__(self):
        self.packet_buffer = []
        self.ip_netflow_map = dict()  # 键为 ip，值为 1s 内的流量

    def offer(self, packet):
        """
        只保留最近 1 秒钟的 packet
        并统计各个 ip 最近一秒钟的流量
        :param packet:
        :return:
        """
        if len(self.packet_buffer) > 0:
            if packet.arrival_time_ms - self.packet_buffer[0].arrival_time_ms > 1000:
                trash_packet = self.packet_buffer.pop(0)
                self.ip_netflow_map[trash_packet.source_ip] -= Packet.max_payload_size
            if packet.source_ip not in self.ip_netflow_map.keys():
                self.ip_netflow_map[packet.source_ip] = Packet.max_payload_size
            else:
                self.ip_netflow_map[packet.source_ip] = self.ip_netflow_map[packet.source_ip] + Packet.max_payload_size
        self.packet_buffer.append(packet)

    def get_ip_bandwidth(self, ip, router_bandwidth):
        """
        获得除了 ip 之外的可用带宽
        :param ip:
        :param router_bandwidth:
        :return:
        """
        other_sum = 0
        for ip_key in self.ip_netflow_map.keys():
            if ip_key != ip:
                other_sum += self.ip_netflow_map[ip_key]
        return max(router_bandwidth - other_sum, 0)


class Router(object):
    def __init__(self, bitrate, buffer_size=10, sender=None, receiver=None, transfer_delay=2):
        self.buffer_size = buffer_size
        self.buffer = []
        self.bitrate = bitrate
        self.interval = 0
        self.set_bitrate(bitrate)

        self.receiver = receiver
        self.sender = sender

        self.transfer_delay = transfer_delay

        self.receive_time_line = 0
        self.send_time_line = 0

        self.read_bitrate_time = 0  # save last time when router read bitrate

        self.i_mat = 0
        self.i_line = 0
        self.file_list = []
        self.current_mat = []
        self.base_dir = ''
        self.mat = ''

        self.fix_bitrate = False
        self.read_interval = 1000
        self.stop_time = sys.maxsize

        self.sender_map = dict()
        self.receiver_map = dict()

        self.pqios = PacketQueueInOneSecond()

    def set_receiver(self, receiver_map):
        self.receiver_map = receiver_map

    def set_sender(self, sender_map):
        self.sender_map = sender_map
        for sender in self.sender_map.values():
            sender.set_receiver(self)

    def receive(self, packet):
        packet.add_delay(self.transfer_delay)
        self.receive_time_line = packet.arrival_time_ms

        if self.send_time_line > self.receive_time_line:
            if len(self.buffer) < self.buffer_size:
                self.buffer.append(packet)
            else:
                # print('buffer of router is full')
                pass
        else:
            # considering time line, router receives future packet
            # router doesn't know if it should dump packet
            # keep this packet until send_time_line > receive_time_line
            self.buffer.append(packet)

    def send(self):
        """
        根据 packet 的目标接收者 ip 找到目标接收者，调用接收者的 receiver.receive()
        因此， packet 除了 source ip 还需要添加 destination ip
        :return:
        """
        if self.buffer and len(self.buffer) != 0:
            packet = self.buffer.pop(0)
            # print('arrival_time:', packet.arrival_time_ms, ', buffer_capacity:', len(self.buffer))
            # print 'arrival_time:', packet.arrival_time_ms, ',send_time:', self.send_time_line
            if len(self.buffer) == 0:
                packet.arrival_time_ms = self.receive_time_line
                self.send_time_line = self.receive_time_line
            else:
                packet.arrival_time_ms = self.send_time_line
            self.pqios.offer(packet)
            # add route bandwidth to packet
            route_bandwidth = self.pqios.get_ip_bandwidth(packet.source_ip, self.bitrate)
            packet.set_bandwidth(route_bandwidth)
            self.receiver_map[packet.destination_ip].receive(packet)
        # send_time_line increases
        # else:
        #     print('hello world!')
        self.send_time_line += self.interval

    def set_bitrate(self, bitrate):
        self.bitrate = bitrate
        self.interval = 1000 / (float(self.bitrate) / Packet.max_payload_size)

    def choose_sender_send(self):
        """
        从 sender_map 中找最早发送数据包的那个 sender
        :return:
        """
        sender_list = self.sender_map.values()
        nearly_send_time = 0
        nearly_send_sender = None
        for sender in sender_list:
            if nearly_send_sender is None or nearly_send_time > sender.next_send_time():
                nearly_send_time = sender.next_send_time()
                nearly_send_sender = sender
        nearly_send_sender.send()

    def start(self):
        """
        start with a new sender bitrate
        :return:
        """
        while True:
            if self.receive_time_line > self.stop_time:
                raise TimeOutException('now is %.1f minute' % (self.stop_time/1000/60))
            elif self.receive_time_line < self.send_time_line:
                self.choose_sender_send()
            else:
                self.send()


if __name__ == '__main__':
    pass
