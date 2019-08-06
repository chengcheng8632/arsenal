# from network_simulator.feedbackPacket import FeedbackPacket

initialWindowMs = 500
rateWindowMs = 150


class AcknowledgedBitrateEstimator:

    def __init__(self):
        self.sum = 0
        self.current_win_ms = 0
        self.prev_time_ms = -1
        self.bitrate_estimate = -1
        self.bitrate_estimate_var = 150  # default 50

    def bitrate_bps(self):
        return self.bitrate_estimate * 1000

    def UpdateWindow(self, now_ms, bytes, rate_window_ms):
        # reset if time moves backwards.
        if now_ms < self.prev_time_ms:
            self.prev_time_ms = -1
            self.sum = 0.0
            self.current_win_ms = 0
        if self.prev_time_ms >= 0:
            self.current_win_ms += (now_ms - self.prev_time_ms)
            # Reset if nothing has been received for more than a full window.
            # if now_ms - self.prev_time_ms > rate_window_ms:
            #     self.sum = 0
            #     self.current_win_ms %= rate_window_ms
        self.prev_time_ms = now_ms
        bitrate_sample = -1
        if self.current_win_ms >= rate_window_ms:
            bitrate_sample = 8 * self.sum / rate_window_ms
            self.current_win_ms %= rate_window_ms
            self.sum = 0
        self.sum += bytes
        return bitrate_sample

    def Update(self, now_ms, bits):
        # rate_window_ms = initialWindowMs if self.bitrate_estimate < 0 else rateWindowMs
        rate_window_ms = rateWindowMs
        bitrate_sample = self.UpdateWindow(now_ms, bits/8, rate_window_ms)
        if bitrate_sample < 0:
            return
        if self.bitrate_estimate < 0:
            # This is the very first sample we get. Use it to initialize the estimate.
            self.bitrate_estimate = bitrate_sample
            return
        # Define the sample uncertainty as a function of how far away it is from the
        # current estimate
        sample_uncertainty = 10.0 * abs(self.bitrate_estimate-bitrate_sample)/self.bitrate_estimate
        sample_var = sample_uncertainty ** 2
        # Update a bayesian estimate of the rate, weighting it lower if the sample
        # uncertainty is large.
        # The bitrate estimate uncertainty is increased with each update to model
        # that the bitrate changes over time.
        pred_bitrate_estimate_var = self.bitrate_estimate_var + 5
        self.bitrate_estimate = (sample_var*self.bitrate_estimate +
                                 pred_bitrate_estimate_var*bitrate_sample)/(sample_var+pred_bitrate_estimate_var)
        self.bitrate_estimate_var = sample_var*pred_bitrate_estimate_var/(sample_var+pred_bitrate_estimate_var)

    def Estimate(self, feedback):
        """
        :param feedback:
        :return:
        """
        for i in range(len(feedback.arrival_time_ms)):
            if self.IsInSendTimeHistory(feedback.send_time_ms[i]):
                self.Update(feedback.arrival_time_ms[i], feedback.payload_size[i])

    def IsInSendTimeHistory(self, send_time_ms):
        """
        send_time_ms >=0
        :param send_time_ms:
        :return:
        """
        return send_time_ms >= 0


