import sys
from il.network_simulator.feedbackPacket import FeedbackPacket
from il.network_simulator.frame import Frame


class Receiver(object):
    def __init__(self, ip, sender=None, buffer_size=10, transfer_delay=2):
        self.buffer_size = buffer_size
        self.buffer_list = []
        self.transfer_delay = transfer_delay

        self.feedbackPacket_size = 4
        self.feedbackPacket = FeedbackPacket()

        self.frame_buffer = []

        self.frame_buffer_size = 30
        self.frame = Frame(0, 0)

        self.sender = sender
        self.ip = ip

        self.bandwidth_pre_time = 0

    def receive(self, packet):
        self.buffer_list.append(packet)
        if len(self.buffer_list) > self.buffer_size:
            self.buffer_list.pop(0)
        loss = self.compute_loss()
        packet.arrival_time_ms += self.transfer_delay

        self.combine_frame(packet)
        self.add_packet_to_feedback(packet, loss)

    def combine_frame(self, packet):
        """
        use new packet to combine frame
        :param packet:
        :return:
        """
        if self.frame.frameId != packet.frame_id:
            # add frame delay interval
            self.feedbackPacket.frame_delay_interval.append(self.compute_frame_delay_interval())
            self.feedbackPacket.frame_delay.append(self.compute_frame_delay())
            # here test if new frame comes
            self.frame_buffer.append(self.frame)
            # print('frame_id:', self.frame.frameId, ',inner_frame_loss:', self.frame.compute_loss())
            self.feedbackPacket.frame_inner_loss.append(self.frame.compute_loss())

            if len(self.frame_buffer) > self.frame_buffer_size:
                self.frame_buffer.pop(0)
            self.frame = None
            self.frame = Frame(packet.frame_id, packet.payload_size)
            self.frame.packet_list.append(packet)
        else:
            self.frame.frame_size += packet.payload_size
            self.frame.packet_list.append(packet)
            self.feedbackPacket.frame_inner_loss.append(-1)
            self.feedbackPacket.frame_delay_interval.append(0)
            self.feedbackPacket.frame_delay.append(0)

        if len(self.frame_buffer) > 1:
            max_f_id = -1
            min_f_id = sys.maxsize
            for frame in self.frame_buffer:
                max_f_id = max(max_f_id, frame.frameId)
                min_f_id = min(min_f_id, frame.frameId)

    def compute_frame_delay_interval(self):
        """
        compute out frame delay interval by frame_buffer  and current_frame
        :return:
        """
        last_frame_arrival_time = 0
        last_frame_send_time = 0
        if len(self.frame_buffer) != 0:
            last_frame = self.frame_buffer[-1]
            last_packet = last_frame.packet_list[-1]
            first_packet = last_frame.packet_list[0]
            last_frame_send_time = first_packet.send_time_ms
            last_frame_arrival_time = last_packet.arrival_time_ms
        current_frame = self.frame
        first_packet = current_frame.packet_list[0]
        last_packet = current_frame.packet_list[-1]
        current_frame_send_time = first_packet.send_time_ms
        current_frame_arrival_time = last_packet.arrival_time_ms

        # print current_frame_arrival_time, last_frame_arrival_time
        # print current_frame_send_time, last_frame_send_time

        frame_delay_interval = (current_frame_arrival_time - last_frame_arrival_time) -\
                               (current_frame_send_time - last_frame_send_time)
        # print('frame_delay_interval:', frame_delay_interval)
        return frame_delay_interval

    def compute_frame_delay(self):
        """
        compute out frame delay interval by frame_buffer  and current_frame
        :return:
        """
        current_frame = self.frame
        first_packet = current_frame.packet_list[0]
        last_packet = current_frame.packet_list[-1]
        current_frame_send_time = first_packet.send_time_ms
        current_frame_arrival_time = last_packet.arrival_time_ms
        frame_delay = (current_frame_arrival_time - current_frame_send_time)
        # print('frame_delay:', frame_delay)
        return frame_delay

    def compute_feedback_average_bandwidth(self):
        feedback = self.feedbackPacket
        list_bandwidth = feedback.bandwidth
        start_bw = list_bandwidth[0]
        list_arrival_time = feedback.arrival_time_ms
        feedback_period = list_arrival_time[-1] - self.bandwidth_pre_time

        average_bandwidth = 0
        for i in range(1, len(list_bandwidth)):
            if start_bw != list_bandwidth[i]:
                period = list_arrival_time[i - 1] - self.bandwidth_pre_time
                average_bandwidth = average_bandwidth + period * start_bw
                self.bandwidth_pre_time = list_arrival_time[i - 1]
                start_bw = list_bandwidth[i]

        period = list_arrival_time[-1] - self.bandwidth_pre_time
        average_bandwidth = average_bandwidth + period * start_bw
        average_bandwidth = average_bandwidth / float(feedback_period)
        self.feedbackPacket.average_bandwidth = average_bandwidth
        self.bandwidth_pre_time = list_arrival_time[-1]

        pass

    def add_packet_to_feedback(self, packet, loss):
        """
        add packet to feedbackpacket, when feedbackpacket is full, send it to RL, then renew feedbackpacket
        :param packet:
        :param loss:
        :return:
        """
        self.feedbackPacket.loss.append(loss * 100)
        self.feedbackPacket.send_time_ms.append(packet.send_time_ms)
        self.feedbackPacket.arrival_time_ms.append(packet.arrival_time_ms)
        self.feedbackPacket.payload_size.append(packet.payload_size)
        self.feedbackPacket.bitrate_list.append(packet.bitrate)

        self.feedbackPacket.frame_id.append(packet.frame_id)
        self.feedbackPacket.frame_packet_start_seq.append(packet.frame_start_packet_seq)
        self.feedbackPacket.frame_packet_end_seq.append(packet.frame_end_packet_seq)

        self.feedbackPacket.bandwidth.append(packet.bandwidth)
        self.feedbackPacket.codec_bitrate.append(packet.codec_bitrate)
        if len(self.feedbackPacket.loss) >= self.feedbackPacket_size:
            self.compute_feedback_average_bandwidth()
            self.passback_feedback()
            self.feedbackPacket = FeedbackPacket([], [], [], [], [], [])

    def passback_feedback(self):
        self.sender.receive_feedback(self.feedbackPacket)

    def compute_loss(self):
        """
        problem: when seq increases to sys.maxsize??
        :return:
        """
        min_seq = sys.maxsize
        max_seq = 0
        for packet in self.buffer_list:
            min_seq = min(min_seq, packet.seq)
            max_seq = max(max_seq, packet.seq)
        loss = 1 - len(self.buffer_list)/float(max_seq - min_seq + 1)
        return loss

    def set_buffer_size(self, buffer_size):
        self.buffer_size = buffer_size
