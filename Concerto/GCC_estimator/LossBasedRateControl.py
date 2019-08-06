
class LossBasedRateController:
    def __init__(self, hyper_params):
        self.lowLossThreshold = hyper_params.lowLossThreshold
        self.highLossThreshold = hyper_params.highLossThreshold

    # Loss-based Rate Controller
    def Estimate(self, loss, current_bitrate_bps):
        avg_loss = sum(loss)/len(loss)/100
        new_bitrate_bps = current_bitrate_bps
        if avg_loss <= self.lowLossThreshold:
            new_bitrate_bps = current_bitrate_bps * 1.08 + 1000
        elif avg_loss <= self.highLossThreshold:
            pass
        else:
            new_bitrate_bps = current_bitrate_bps * (1 - 0.5*avg_loss)
        return new_bitrate_bps

    def ApplyHyperParameters(self, hyper_params):
        self.lowLossThreshold = hyper_params.lowLossThreshold
        self.highLossThreshold = hyper_params.highLossThreshold




