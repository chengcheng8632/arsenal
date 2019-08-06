class FeedbackPacket(object):
    """
    connect with Simulator
    """
    def __init__(self, loss=[], seq=[], send_time=[], arrival_time=[], payload_size=[], frame_id=[]):
        self.loss = loss
        self.sequence_number = seq
        self.send_time_ms = send_time
        self.arrival_time_ms = arrival_time
        self.payload_size = payload_size
        self.frame_id = frame_id
        self.frame_packet_start_seq = []
        self.frame_packet_end_seq = []
        self.frame_inner_loss = []
        self.frame_delay_interval = []
        self.frame_delay = []
        self.bandwidth = []
        self.bitrate_list = []
        self.codec_bitrate = []
        self.average_bandwidth = 0

    def to_string(self):
        print(self.loss)
        print(self.frame_delay)
        print(self.frame_delay_interval)
        print(self.send_time_ms)
        print(self.arrival_time_ms)
        # print(self.sequence_number)

    def __str__(self):
        return super(FeedbackPacket, self).__str__()


