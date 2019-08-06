class BitrateController:
    def __init__(self, min_bitrate_bps):
        self.delay_based_bitrate_bps = 0
        self.loss_based_bitrate_bps = 0
        self.current_bitrate_bps = 30000
        self.min_bitrate_bps = min_bitrate_bps
        self.max_bitrate_bps = 2000 * 1000

    def OnDelayBasedBweResult(self, delay_based_bitrate_bps):
        self.delay_based_bitrate_bps = delay_based_bitrate_bps
        self.CapBitrateToThresholds(delay_based_bitrate_bps)

    def OnLossBasedBweResult(self, bitrate):
        self.loss_based_bitrate_bps = bitrate


    def CapBitrateToThresholds(self, bitrate_bps):
        if bitrate_bps > self.delay_based_bitrate_bps > 0:
            bitrate_bps = self.delay_based_bitrate_bps
        if bitrate_bps > self.loss_based_bitrate_bps > 0:
            bitrate_bps = self.loss_based_bitrate_bps
        if bitrate_bps > self.max_bitrate_bps:
            bitrate_bps = self.max_bitrate_bps
        if bitrate_bps < self.min_bitrate_bps:
            bitrate_bps = self.min_bitrate_bps
        self.current_bitrate_bps = bitrate_bps

    def TargetSendRate(self):
        return self.current_bitrate_bps
