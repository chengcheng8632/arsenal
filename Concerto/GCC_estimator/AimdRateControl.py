# coding=utf-8

import math


class RateControlState:
    hold = 0
    increase = 1
    decrease = 2


class RateControlRegion:
    nearMax = 0
    awayMax = 1
    maxUnknown = 2


class BandWidthUsage:
    overusing = 0
    underusing = 1
    normal = 2


class AimdRateControl:
    """
    Additive Increase Multiplicative Decrease
    """
    def __init__(self):
        self.max_configured_bitrate_bps = 30000000
        self.min_configured_bitrate_bps = 30000
        self.current_bitrate_bps = 30000
        self.avg_max_bitrate_kbps = -1
        self.var_max_bitrate_kbps = 0.4
        self.rate_control_state = RateControlState.hold
        self.rate_control_region = RateControlRegion.maxUnknown
        self.time_first_incoming_estimate = -1
        self.time_last_bitrate_change = -1
        self.bitrate_is_initialized = False
        self.addIncreaseFactor = 4000
        self.multiIncreaseFactor = 1.08
        self.multiDecreaseFactor = 0.85
        self.rtt = 200

    def Update(self, input_data, now_ms):
        """
        :param input_data: RateControlInput 类型
        :param now_ms:
        :return:
        """
        # 如果bitrate 不是初始化的
        if not self.bitrate_is_initialized:
            # 初始化时间为 5000
            initializationTimeMs = 5000
            # 第一个时间小于 0
            if self.time_first_incoming_estimate < 0:
                # RateControlInput.incoming_bitrate >= 0
                if input_data.incoming_bitrate >= 0:
                    self.time_first_incoming_estimate = now_ms
            elif now_ms - self.time_first_incoming_estimate > initializationTimeMs and input_data.incoming_bitrate >= 0:
                    self.current_bitrate_bps = input_data.incoming_bitrate
                    self.bitrate_is_initialized = True
        self.current_bitrate_bps = self.ChangeBitrate(input_data, now_ms)
        return self.current_bitrate_bps

    def ChangeBitrate(self, input_data, now_ms):
        incoming_bitrate_bps = input_data.incoming_bitrate
        new_bitrate_bps = self.current_bitrate_bps
        if (not self.bitrate_is_initialized) and input_data.bw_state != BandWidthUsage.overusing:
            # 如果速率是被初始化的，并且 RateControlInput 的 bw 状态不是过度使用，返回上次估计的速率
            return self.current_bitrate_bps
        # 否则改变状态
        self.ChangeState(input_data)
        incoming_bitrate_kbps = incoming_bitrate_bps / 1000
        std_max_bit_rate = (self.var_max_bitrate_kbps * self.avg_max_bitrate_kbps)**2
        if self.rate_control_state == RateControlState.hold:
            # 如果为保持那么什么都不做
            pass
        elif self.rate_control_state == RateControlState.increase:
            # 如果速率控制状态为增长
            if self.avg_max_bitrate_kbps >= 0 and \
                    incoming_bitrate_kbps > self.avg_max_bitrate_kbps + 2 * std_max_bit_rate:  # default 2
                # 如果平均最大速率大于 0 k，并且将来的速率大于平均最大速率
                self.rate_control_region = RateControlRegion.maxUnknown
                self.avg_max_bitrate_kbps = -1.0
            elif self.rate_control_region == RateControlRegion.nearMax:
                new_bitrate_bps += self.AdditiveRateIncrease(now_ms)
            else:
                new_bitrate_bps += self.MultiplicativeRateIncrease(now_ms, new_bitrate_bps)
            self.time_last_bitrate_change = now_ms
        elif self.rate_control_state == RateControlState.decrease:
            new_bitrate_bps = self.multiDecreaseFactor * incoming_bitrate_bps + 0.5
            if new_bitrate_bps > self.current_bitrate_bps:
                # Avoid increasing the rate when over-using.
                if self.rate_control_region != RateControlRegion.maxUnknown:
                    new_bitrate_bps = self.multiDecreaseFactor * self.avg_max_bitrate_kbps * 1000 + 0.5
                new_bitrate_bps = min(new_bitrate_bps, self.current_bitrate_bps)
            self.rate_control_region = RateControlRegion.nearMax
            if incoming_bitrate_kbps < self.avg_max_bitrate_kbps - 3 * std_max_bit_rate:
                self.avg_max_bitrate_kbps = -1.0
            self.bitrate_is_initialized = True
            self.UpdateMaxBitRateEstimate(incoming_bitrate_kbps)
            self.rate_control_state = RateControlState.hold
            self.time_last_bitrate_change = now_ms
        return self.ClampBitrate(new_bitrate_bps, incoming_bitrate_bps)
    
    def SetMinBitrate(self, min_bitrate_bps):
        self.min_configured_bitrate_bps = min_bitrate_bps
        self.current_bitrate_bps = max(min_bitrate_bps, self.current_bitrate_bps)
    
    def ChangeState(self, input_data):
        """
        利用 input_data 来改变当前 aimd 的状态
        :param input_data:
        :return:
        """
        if input_data.bw_state == BandWidthUsage.normal:
            # 如果 input_data 带宽状态为常规，并且 aimd 当前状态为保持，那么切换 aimd 状态为增长
            if self.rate_control_state == RateControlState.hold:
                self.rate_control_state = RateControlState.increase
        elif input_data.bw_state == BandWidthUsage.overusing:
            # 如果 input_start 为过度使用，那么切换 aimd 状态为减少
            self.rate_control_state = RateControlState.decrease
        elif input_data.bw_state == BandWidthUsage.underusing:
            # 如果 input_state 状态为未占满，切换 aimd 状态为增长
            self.rate_control_state = RateControlState.increase

    def AdditiveRateIncrease(self, now_ms):
        bits_per_frame = self.current_bitrate_bps / 30
        number = int(20)
        if type(bits_per_frame) == type(number):
            print(bits_per_frame)
        packets_per_frame = math.ceil(float(bits_per_frame)/(8*1200))
        avg_packet_size_bits = bits_per_frame / packets_per_frame
        response_time = self.rtt + 100
        near_max_increase_rate_bps = max(self.addIncreaseFactor, (avg_packet_size_bits*1000)/response_time)
        return (now_ms - self.time_last_bitrate_change) * near_max_increase_rate_bps / 1000

    def MultiplicativeRateIncrease(self, now_ms, current_bitrate_bps):
        alpha = self.multiIncreaseFactor
        if self.time_last_bitrate_change > -1:
            time_since_last_update_ms = now_ms - self.time_last_bitrate_change
            time_since_last_update_ms = 1000 if time_since_last_update_ms < 1000 else time_since_last_update_ms
            alpha = pow(alpha, time_since_last_update_ms / 1000)
        multiplicative_increase_bps = max(current_bitrate_bps * (alpha - 1.0), 1000.0)
        return multiplicative_increase_bps

    def UpdateMaxBitRateEstimate(self, incoming_bitrate_kbps):
        alpha = 0.05
        if self.avg_max_bitrate_kbps == -1.0:
            self.avg_max_bitrate_kbps = incoming_bitrate_kbps
        else:
            self.avg_max_bitrate_kbps = (1 - alpha) * self.avg_max_bitrate_kbps + alpha * incoming_bitrate_kbps
        norm = max(self.avg_max_bitrate_kbps, 1.0)
        self.var_max_bitrate_kbps = (1 - alpha) * self.var_max_bitrate_kbps + alpha * (
                self.avg_max_bitrate_kbps - incoming_bitrate_kbps) * (
                self.avg_max_bitrate_kbps - incoming_bitrate_kbps) / norm
        if self.var_max_bitrate_kbps < 0.4:
            self.var_max_bitrate_kbps = 0.4
        elif self.var_max_bitrate_kbps > 2.5:
            self.var_max_bitrate_kbps = 2.5

    def ClampBitrate(self, new_bitrate_bps, incoming_bitrate_bps):
        max_bitrate_bps = 1.5 * incoming_bitrate_bps + 10000
        if new_bitrate_bps > self.current_bitrate_bps and new_bitrate_bps > max_bitrate_bps:
            new_bitrate_bps = max(self.current_bitrate_bps, max_bitrate_bps)
        new_bitrate_bps = max(new_bitrate_bps, self.min_configured_bitrate_bps)
        return new_bitrate_bps

    def ApplyHyperParameters(self, hyper_params):
        self.multiIncreaseFactor = hyper_params.multiIncreaseFactor
        self.addIncreaseFactor = hyper_params.addIncreaseFactor
        self.multiDecreaseFactor = hyper_params.multiDecreaseFactor

    def SetStartBitrate(self, start_bitrate_bps):
        self.current_bitrate_bps = start_bitrate_bps
        self.bitrate_is_initialized = True
