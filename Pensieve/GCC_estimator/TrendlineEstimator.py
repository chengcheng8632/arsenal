# coding=utf-8

deltaCounterMax = 1000


class TrendlineEstimator:
    def __init__(self, window_size, smoothing_coef, threshold_gain):
        self.window_size = window_size
        self.smoothing_coef = smoothing_coef
        self.threshold_gain = threshold_gain
        self.num_of_deltas = 0
        self.first_arrival_time_ms = -1
        self.accumulated_delay = 0
        self.smoothed_delay = 0
        self.delay_hist = []
        self.trendline = 0

    def LinearFitSlope(self, points):
        sum_x, sum_y = 0, 0
        for point in points:
            # 每个 point 中存放着累积延迟，均衡平滑延迟
            sum_x += point[0]  # trans_i
            sum_y += point[1]  # smo_delay_i
        # 再对累积延迟和均衡平滑延迟做平均
        x_avg = sum_x / len(points)
        y_avg = sum_y / len(points)

        numerator, denominator = 0, 0
        for point in points:
            numerator += (point[0] - x_avg) * (point[1] - y_avg)
            denominator += (point[0] - x_avg) * (point[0] - x_avg)
        if denominator == 0:
            return 0
        return numerator/denominator

    def Update(self, recv_delta_ms, send_delta_ms, arrival_time_ms):
        """
        :param recv_delta_ms: 组包接收时间差
        :param send_delta_ms: 组包发送时间差
        :param arrival_time_ms: 包的到达时间
        :return:
        """
        # 计算单个包组传输增长的延迟
        # delay_i = delta_arrival - delata_timestamp
        delta_ms = recv_delta_ms - send_delta_ms

        self.num_of_deltas += 1
        if self.num_of_deltas > deltaCounterMax:  # 1000
            self.num_of_deltas = deltaCounterMax
        if self.first_arrival_time_ms == -1:
            # 用第一个 arrival_time_ms 来初始化 first_arrival_time_ms
            self.first_arrival_time_ms = arrival_time_ms
        # Expponential backoff filter
        # 做每个包组的叠加
        # acc_delay_i = delay_0 + delay_1 + ... + delay_i
        self.accumulated_delay += delta_ms
        # 通过累积延迟计算一个均衡平滑延迟值，其中 alpha = 0.9， 这里的 alpha 即 self.smoothing_coef
        # smo_delay_i = alpha * smo_delay_i-1 + (1 - alpha) * acc_delay_i
        self.smoothed_delay = self.smoothing_coef * self.smoothed_delay + (1-self.smoothing_coef)*self.accumulated_delay
        # Simple linear regression
        # 第 i 个包组的传输持续时间， 其中 delay_hist 是一个 2 * n 的矩阵
        # trans_i = t_i - first_arrival_i
        # 此处传值是否应该是 acc_delay_i ??
        self.delay_hist.append((arrival_time_ms-self.first_arrival_time_ms, self.smoothed_delay))
        if len(self.delay_hist) > self.window_size:
            # 如果长度超过限定的窗口长度，出队
            self.delay_hist.pop(0)
        if len(self.delay_hist) == self.window_size:
            # 如果长度等于窗口长度，那么计算 trendline
            self.trendline = self.LinearFitSlope(self.delay_hist)

    def trendline_slope(self):
        # 增加 trendline 的斜率
        return self.trendline * self.threshold_gain
