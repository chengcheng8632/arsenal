# coding=utf-8

from GCC_estimator.InterArrival import InterArrival
from GCC_estimator.TrendlineEstimator import TrendlineEstimator
from GCC_estimator.OveruseDetector import OveruseDetector
from GCC_estimator.AimdRateControl import AimdRateControl

absSendTimeFraction = 18
absSendTimeInterArrivalUpshift = 8
interArrivalShift = absSendTimeFraction + absSendTimeInterArrivalUpshift
defaultTrendlineWindowSize = 20
defaultTrendlineSmoothingCoeff = 0.9
defaultTrendlineThresholdGain = 4.0


class RateControlInput:
    def __init__(self, bw_state, incoming_bitrate, noise_var):
        self.bw_state = bw_state
        self.incoming_bitrate = incoming_bitrate
        self.noise_var = noise_var


class DelayBasedBwe:
    def __init__(self, c):
        self.inter_arrival = InterArrival()
        self.rate_control = AimdRateControl()
        self.trendline_estimator = TrendlineEstimator(defaultTrendlineWindowSize, defaultTrendlineSmoothingCoeff,
                                                      defaultTrendlineThresholdGain)
        self.detector = OveruseDetector(c.overuseThresholdFactor)

    def IncomingPacketFeedback(self, feedback_packet, index):
        send_time_ms = feedback_packet.send_time_ms[index]
        # send_time_ms 做了移位操作
        # 在 ComputeDeltas 中，timestamp_diff 和 send_time_ms 这个操作相匹配，可能是为了避免数字过大而溢出
        # default 0x00FFFFFF
        send_time_24bits = int(((int(send_time_ms * 2 ** absSendTimeFraction) + 500)/1000.0)) & 0xFFFFFFFF
        timestamp = send_time_24bits << absSendTimeInterArrivalUpshift
        # print type(timestamp)
        arrival_time_ms = feedback_packet.arrival_time_ms[index]
        # 得到组包的发送时间差 ts_delta 和 到达时间差 t_delta
        ts_delta, t_delta = self.inter_arrival.ComputeDeltas(timestamp, arrival_time_ms)
        # 这里又做了一个很奇怪的移位操作？？？把发送时间差又给造回来了？？
        ts_delta_ms = (1000.0 * ts_delta) / (1 << interArrivalShift)

        self.trendline_estimator.Update(t_delta, ts_delta_ms, arrival_time_ms)
        mt, threashold = self.detector.Detect(self.trendline_estimator.trendline_slope(), ts_delta,
                             self.trendline_estimator.num_of_deltas, arrival_time_ms)
        return ts_delta_ms, t_delta, self.trendline_estimator.trendline, mt, threashold

    def Estimate(self, feedback_packet, acknowledged_bitrate_bps):
        # overusing = False
        ts_delta, t_delta, trendline, mt, threashold = [], [], [], [], []
        for i in range(len(feedback_packet.send_time_ms)):
            # 对 feedback 包中的每个发送时间做累计
            ts_d, t_d, trendl, mtt, th = self.IncomingPacketFeedback(feedback_packet, i)
            ts_delta.append(ts_d)
            t_delta.append(t_d)
            trendline.append(trendl)
            mt.append(mtt)
            threashold.append(th)
        bw_state = self.detector.State()
        now_ms = int(feedback_packet.arrival_time_ms[-1])
        target_bitrate_bps = self.rate_control.Update(RateControlInput(bw_state, acknowledged_bitrate_bps, 0), now_ms)
        return target_bitrate_bps, ts_delta, t_delta, trendline, mt, threashold

    def SetMinBitrate(self, min_bitrate_bps):
        self.rate_control.SetMinBitrate(min_bitrate_bps)

    def ApplyHyperParameters(self, hyper_params):
        self.detector.ApplyHyperParameters(hyper_params.overuseThresholdFactor)
        self.rate_control.ApplyHyperParameters(hyper_params)

    def SetStartBitrate(self, start_bitrate_bps):
        self.rate_control.SetStartBitrate(start_bitrate_bps)
