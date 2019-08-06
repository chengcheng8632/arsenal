# -*- coding: UTF-8 -*-
from GCC_estimator.AcknowledgedBitrateEstimator import AcknowledgedBitrateEstimator
from GCC_estimator.LossBasedRateControl import LossBasedRateController
from GCC_estimator.DelayBasedRateControl import DelayBasedBwe
from GCC_estimator.BitrateController import BitrateController


class HyperParameters:
    def __init__(self, lowLossThreshold=0.02, highLossThreshold=0.1, overuseThresholdFactor=1,
                 multiIncreaseFactor=1.08, addIncreaseFactor=4000, multiDecreaseFactor=0.85):
        self.lowLossThreshold = lowLossThreshold
        self.highLossThreshold = highLossThreshold
        self.multiIncreaseFactor = multiIncreaseFactor
        self.addIncreaseFactor = addIncreaseFactor
        self.multiDecreaseFactor = multiDecreaseFactor
        self.overuseThresholdFactor = overuseThresholdFactor


class SendSideCongestionController:
    def __init__(self):
        self.hyper_params = HyperParameters()
        self.min_bitrate_bps = 30 * 1000
        self.bitrate_controller = BitrateController(self.min_bitrate_bps)
        self.acknowledged_bitrate_estimator = AcknowledgedBitrateEstimator()
        self.delay_based_bwe = DelayBasedBwe(self.hyper_params)
        self.delay_based_bwe.SetMinBitrate(self.min_bitrate_bps)
        self.loss_based_bwe = LossBasedRateController(self.hyper_params)

    def ApplyHyperParameters(self, lowLossThreshold, highLossThreshold, overuseThresholdFactor,
                             multiIncreaseFactor=1.08, addIncreaseFactor=4000, multiDecreaseFactor=0.85):
        self.hyper_params = HyperParameters(lowLossThreshold=lowLossThreshold,
                                            highLossThreshold=highLossThreshold,
                                            overuseThresholdFactor=overuseThresholdFactor,
                                            multiIncreaseFactor=multiIncreaseFactor,
                                            addIncreaseFactor=addIncreaseFactor,
                                            multiDecreaseFactor=multiDecreaseFactor)
        self.delay_based_bwe.ApplyHyperParameters(self.hyper_params)
        self.loss_based_bwe.ApplyHyperParameters(self.hyper_params)

    def OnRTCPFeedbackPacket(self, feedback_packet):
        # 基于丢包的带宽估计
        loss_based_bitrate_bps = self.loss_based_bwe.Estimate(feedback_packet.loss, self.bitrate_controller.current_bitrate_bps)
        self.bitrate_controller.OnLossBasedBweResult(loss_based_bitrate_bps)
        # 先验估计？
        self.acknowledged_bitrate_estimator.Estimate(feedback_packet)
        # 基于延迟的带宽估计
        delay_based_bitrate_bps, ts_delta, t_delta, trendline, mt, threashold = self.delay_based_bwe.Estimate(feedback_packet, self.acknowledged_bitrate_estimator.bitrate_bps())
        self.bitrate_controller.OnDelayBasedBweResult(delay_based_bitrate_bps)
        return self.bitrate_controller.TargetSendRate(), self.bitrate_controller.loss_based_bitrate_bps, \
               self.bitrate_controller.delay_based_bitrate_bps, ts_delta, t_delta, trendline, mt, threashold

    def SetStartBitrate(self, start_bitrate_bps):
        self.delay_based_bwe.SetStartBitrate(start_bitrate_bps)
        self.bitrate_controller.current_bitrate_bps = start_bitrate_bps


