# coding=utf-8

timestampGroupLengthMs = 5
absSendTimeFraction = 18
absSendTimeInterArrivalUpshift = 8
interArrivalShift = absSendTimeFraction + absSendTimeInterArrivalUpshift
timestampToMs = 1000.0 / (1 << interArrivalShift)
reorderedResetThreshold = 3
arrivalTimeOffsetThresholdMs = 3000
burstDeltaThresholdMs = 5


class FrameGroup:
    def __init__(self):
        self.first_timestamp = 0  # 该组包开始时间
        self.timestamp = 0        # ？？？
        self.complete_time_ms = -1  # 该组包结束时间

    def IsFirstPacket(self):
        return self.complete_time_ms == -1


class InterArrival:
    def __init__(self):
        self.current_timestamp_group = FrameGroup()  # 当前组包
        self.prev_timestamp_group = FrameGroup()     # 前一组包
        self.timestamp_delta = 0
        self.arrival_time_delta_ms = 0
        self.timestampGroupLengthTicks = (timestampGroupLengthMs << interArrivalShift)/1000.0
        self.timestamp_to_ms_coeff = 1000.0 / (1 << interArrivalShift)

    def ComputeDeltas(self, timestamp, arrival_time_ms):
        """
        :param timestamp: 发送时间
        :param arrival_time_ms: 到达时间
        :return:
        """
        if self.current_timestamp_group.IsFirstPacket():
            # 如果是第一组包
            # 当前组包的发送时间设置成 timestamp
            # 当前组包的第一个发送时间设置成 timestamp
            # We don't have enough data to update the filter, so we store it until we
            # have two frames of data to process.
            self.current_timestamp_group.timestamp = timestamp
            self.current_timestamp_group.first_timestamp = timestamp
        elif self.NewTimestampGroup(arrival_time_ms, timestamp):
            # 如果是一个新组包
            # First packet of a later frame, the previous frame sample is ready
            if self.prev_timestamp_group.complete_time_ms >= 0:
                # 计算前一个组包和当前组包的发送时间差
                self.timestamp_delta = self.current_timestamp_group.timestamp - \
                                       self.prev_timestamp_group.timestamp
                # 计算前一个组包和当前组包的接收时间差
                self.arrival_time_delta_ms = self.current_timestamp_group.complete_time_ms - \
                                             self.prev_timestamp_group.complete_time_ms

            # 将当前组包赋值给前一个组包，并且将新组包赋值给当前组包
            self.prev_timestamp_group.timestamp = self.current_timestamp_group.timestamp
            self.prev_timestamp_group.complete_time_ms = self.current_timestamp_group.complete_time_ms
            self.prev_timestamp_group.first_timestamp = self.current_timestamp_group.first_timestamp
            # The new timestamp is now the current frame
            self.current_timestamp_group.first_timestamp = timestamp
            self.current_timestamp_group.timestamp = timestamp
        else:
            pass
        # 将新的到达时间赋值给当前组包
        self.current_timestamp_group.complete_time_ms = arrival_time_ms
        # 返回组包之间的发送时间差， 到达时间差
        return self.timestamp_delta, self.arrival_time_delta_ms

    def NewTimestampGroup(self, arrival_time_ms, timestamp):
        """
        判断是否是一组新包
        :param arrival_time_ms: 新包的到达时间
        :param timestamp:
        :return:
        """
        if self.current_timestamp_group.IsFirstPacket():
            # 如果是当前组包的第一个包，返回 false
            return False
        elif self.BelongsToBurst(arrival_time_ms, timestamp):
            return False
        else:
            timestamp_diff = timestamp - self.current_timestamp_group.first_timestamp
            # 这里是可能返回 true 的，因为 timestamp 在被传进来的时候也被做了移位操作
            return timestamp_diff > self.timestampGroupLengthTicks

    def BelongsToBurst(self, arrival_time_ms, timestamp):
        """
        如果是突发流量？
        就是指后来的包的发送时间早于先前的包的发送时间
        :param arrival_time_ms:
        :param timestamp:
        :return:
        """
        arrival_time_delta_ms = arrival_time_ms - self.current_timestamp_group.complete_time_ms
        timestamp_diff = timestamp - self.current_timestamp_group.timestamp
        ts_delta_ms = self.timestamp_to_ms_coeff * timestamp_diff + 0.5  # 多项式系数
        if ts_delta_ms == 0:
            return True
        propagation_delta_ms = arrival_time_delta_ms - ts_delta_ms
        # 传播时间差
        # 传播时间差和到达时间差小于突发时间差的阈值
        return propagation_delta_ms < 0 and arrival_time_delta_ms <= burstDeltaThresholdMs

