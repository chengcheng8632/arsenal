# -*- coding: UTF-8 -*-
from GCC_estimator.AimdRateControl import BandWidthUsage
minNumDeltas = 60
maxAdaptOffsetMs = 15
overusingTimeThreshold = 10


class OveruseDetector:
    def __init__(self, overuse_threshold_factor):
        self.k_up = 0.0087
        self.k_down = 0.039
        self.overusing_time_threshold = 10 # default 100, experiment 10
        self.threshold = 12.5 # default 12.5
        self.last_update_ms = -1
        self.prev_offset = 0
        self.time_over_using = -1
        self.overuse_counter = 0
        self.hypothesis = BandWidthUsage.normal
        self.overuseThresholdFactor = overuse_threshold_factor

    def State(self):
        return self.hypothesis

    def UpdateThreshold(self, modified_offset, now_ms):
        """
        :param modified_offset: 即 m_i, offset
        :param now_ms:
        :return:
        """
        if self.last_update_ms == -1:
            self.last_update_ms = now_ms
        k = self.k_down if abs(modified_offset) < self.threshold else self.k_up
        time_delta_ms = min(now_ms - self.last_update_ms, 100)
        self.threshold += k * (abs(modified_offset) - self.threshold) * time_delta_ms
        self.threshold = 2 if self.threshold < 2 else self.threshold
        self.threshold = 600 if self.threshold > 600 else self.threshold
        self.last_update_ms = now_ms

    def Detect(self, offset, ts_delta, num_of_deltas, now_ms):
        if num_of_deltas < 2:
            return 0, 0
        # minNumDeltas = 60
        # offset 即 trendline ！！！ 这参数命名实在是看不太懂
        # trendline * 周期包组个数 即为 m_i
        # 这里的 T 即是 m_i
        T = min(num_of_deltas, minNumDeltas) * offset
        if T > self.overuseThresholdFactor * self.threshold:  # 这里的 threshold 是动态阈值
            if self.time_over_using == -1:
                # Initialize the timer. Assume that we've been
                # over-using half of the time since the previous
                # sample
                # 初始化时间，假设我们自从上次采样已经使用了一半的时间
                self.time_over_using = ts_delta / 2
            else:
                # 否则直接增加自增 发送时间差
                self.time_over_using += ts_delta
            # 过度使用计数器加 1
            self.overuse_counter += 1
            # 如果过度使用时间线超过了过度使用时间线的阈值，并且过度使用的计数器大于 1（说明并非第一次）
            if self.time_over_using > self.overusing_time_threshold and self.overuse_counter > 1:
                # 过度使用带宽时间置为 0，计数器，将原始的 BandWidthUsage.overusing 的值赋给超参数
                self.time_over_using = 0
                self.overuse_counter = 0
                self.hypothesis = BandWidthUsage.overusing
        elif T <= -self.threshold:   # 如果小于 threshold，那么过度使用带宽时间置为 -1？
            self.time_over_using = -1
            self.overuse_counter = 0
            # 将非过度使用的标志赋值给 hypothesis
            self.hypothesis = BandWidthUsage.underusing
        else:
            # 正常
            self.time_over_using = -1
            self.overuse_counter = 0
            self.hypothesis = BandWidthUsage.normal
        self.prev_offset = offset  # 这里的 prev_offset 有啥用？？
        self.UpdateThreshold(T, now_ms)   # 更新阈值
        return T, self.threshold

    def ApplyHyperParameters(self, overuse_threshold_factor):
        self.overuseThresholdFactor = overuse_threshold_factor
