# -*- coding: utf-8 -*-
import sys

print sys.path

from il.network_simulator.packet import Packet
from il.network_simulator.videoCodec import VideoCodec
from il.Congestion_controller.congestionControllerFactory import CongestionControllerFactory


class Sender(object):
    def __init__(self, bitrate, source_ip, destination_ip, controller_name, router=None):
        self.bitrate = bitrate
        self.interval = 0
        self.router = router

        self.source_ip = source_ip
        self.destination_ip = destination_ip

        self.buffer = []
        self.FLAG_STOP = False

        self.send_time_line = 0

        self.read_frame_interval = 33
        self.last_read_frame_time = 0

        self.inuse_bitrate = 0
        self.last_set_bitrate_time = 0
        self.set_bitrate_interval = 1000

        self.congestion_controller = CongestionControllerFactory.get_congestion_controller(controller_name)
        self.congestion_name = controller_name
        self.codec = VideoCodec()  # 初始化 codec

        self.set_bitrate(bitrate)

    def receive_feedback(self, feedback):
        bitrate = self.congestion_controller.estimate(feedback)
        # print("source_ip", self.source_ip,", bitrate:", bitrate)
        self.set_bitrate(bitrate)

    def set_bitrate(self, bitrate):
        """
        only once last time more than 1000
        replace inuse_bitrate with new bitrate
        :param bitrate:
        :return:
        """
        self.bitrate = bitrate
        if True or self.last_set_bitrate_time == 0 or \
                (self.send_time_line - self.last_set_bitrate_time > self.set_bitrate_interval and
                 abs(self.inuse_bitrate - bitrate) / float(self.inuse_bitrate) > 0.1):
            self.last_set_bitrate_time = self.send_time_line - self.send_time_line % self.set_bitrate_interval
            self.inuse_bitrate = bitrate
            self.codec.choose_bps(bitrate)
        self.set_real_send_bitrate(bitrate)

    def set_receiver(self, router):
        """
        set receiver
        in our this demo, router will be our receiver
        :param router:
        :return:
        """
        self.router = router

    def set_real_send_bitrate(self, bitrate):
        """
        self.bitrate = max(b_2s, self.bitrate)

        set_bitrate event will trigger this
        updating packet_buffer will trigger this
        :return:
        """
        pacer_send_birate = self.compute_pacer_send_bitrate()
        if pacer_send_birate > bitrate:
            self.bitrate = pacer_send_birate
        else:
            # print('bitrate:', self.bitrate, ', pacer_send_birate:', pacer_send_birate)
            pass
        self.interval = 1000 / (float(self.bitrate) / Packet.max_payload_size)

    def compute_pacer_send_bitrate(self):
        """
        pacer_send_bitrate
        b_2s,bitrate used to clear packet_buffer within 2 second
        :return:
        """
        sum_packet_payload = 0
        for packet in self.buffer:
            sum_packet_payload += packet.payload_size
        pacer_send_bitrate = sum_packet_payload / 2  # 2s
        return pacer_send_bitrate

    def next_send_time(self):
        return self.send_time_line + self.interval

    def plot_result(self):
        self.congestion_controller.plot_target_send_rate(self.congestion_name + ' ' + self.source_ip)

    def send(self):
        """
        send packet, add packet to router_buffer,
        at the same time, locked the buffer
        :return:
        """
        if self.send_time_line - self.last_read_frame_time > self.read_frame_interval:
            n = (self.send_time_line - self.last_read_frame_time) // self.read_frame_interval
            for i in range(int(n)):
                self.codec.add_frame()  # every 33ms add a frame
            self.last_read_frame_time = self.send_time_line - self.send_time_line % self.read_frame_interval

        # try to pour all frame in buffer into packet buffer
        # seem to add media packets to pacer buffer
        new_frame_packet_list = self.codec.read_frame_data(self.source_ip, self.destination_ip)
        self.buffer += new_frame_packet_list

        self.set_real_send_bitrate(self.bitrate)

        if self.buffer and len(self.buffer) != 0:
            packet = self.buffer.pop(0)
            packet.send_time_ms = self.send_time_line
            packet.arrival_time_ms = self.send_time_line
            packet.bitrate = self.inuse_bitrate
            self.router.receive(packet)
        else:
            self.router.receive_time_line = self.router.transfer_delay + self.send_time_line
        self.send_time_line += self.interval


if __name__ == '__main__':
    pass
