import queue

import numpy as np
from PyQt6.QtCore import QThread, pyqtSignal

from bioview.types import UsrpConfiguration
from bioview.utils import apply_filter, get_filter


class ProcessWorker(QThread):
    logEvent = pyqtSignal(str, str)

    def __init__(
        self,
        channel_ifs,
        if_filter_bw,
        samp_rate,
        save_ds,
        channel_mapping,
        data_mapping,
        rx_queues: list[queue.Queue],
        save_queue: queue.Queue,
        disp_queue: queue.Queue,
        running: bool = True,
        quadrature: bool = True,
    ):
        super().__init__()

        self.rx_queues = rx_queues
        self.save_queue = save_queue
        self.disp_queue = disp_queue

        self.running = running

        self.channel_ifs = channel_ifs
        self.samp_rate = samp_rate
        self.channel_mapping = channel_mapping
        self.data_mapping = data_mapping
        self.save_ds = save_ds

        # Allow for saving either IQ or Amp/Phase (default)
        self.quadrature = quadrature

        # Load IF filters
        self.if_filts = [
            self._load_filter(freq, if_filter_bw[idx])
            for idx, freq in enumerate(channel_ifs)
        ]

        # Initialize states for all valid declared channel combinations
        self.phase_accumulator = {}
        self.filter_states = {}
        for ch_key in self.data_mapping.keys():
            self.phase_accumulator[ch_key] = 0.0
            self.filter_states[ch_key] = None

    def _load_filter(self, freq: float, bandwidth: float, order: int = 2):
        low_cutoff = freq - bandwidth / 2
        high_cutoff = freq + bandwidth / 2

        filter = get_filter(
            bounds=[low_cutoff, high_cutoff],
            samp_rate=self.samp_rate,
            btype="band",
            order=order,
        )
        return filter

    def _process_chunk(self, data, filter, if_freq, channel_key):
        # Early return for empty data
        if len(data) == 0:
            return np.array([]), np.array([])

        # Store last sample for continuity checking
        if hasattr(self, "last_samples") and channel_key in self.last_samples:
            # Check for significant discontinuity
            discontinuity = abs(data[0] - self.last_samples[channel_key])
            if discontinuity > 3 * np.std(data[: min(100, len(data))]):
                self.logEvent.emit(
                    "debug", f"Potential discontinuity detected in {channel_key}"
                )

        # Store last sample for next buffer
        if not hasattr(self, "last_samples"):
            self.last_samples = {}
        self.last_samples[channel_key] = data[-1]

        # Stateful filtering
        current_filter_state = self.filter_states.get(channel_key)
        filt_data, new_filter_state = apply_filter(
            data, filter, zi=current_filter_state
        )
        self.filter_states[channel_key] = new_filter_state

        # Get the current accumulated phase for this channel
        current_phase = self.phase_accumulator[channel_key]

        # Get phase for all samples
        phase_increment = 2 * np.pi * if_freq / self.samp_rate
        phases = current_phase + np.arange(len(filt_data)) * phase_increment

        # Down-convert from IF to baseband with phase continuity
        downconversion = np.exp(-1j * phases)
        baseband_data = filt_data * downconversion

        # Update phase accumulator for next buffer (mod 2π to prevent numerical drift)
        self.phase_accumulator[channel_key] = phases[-1] + phase_increment

        # Downsampling logic
        step = self.save_ds
        end_idx = len(baseband_data) - step + 1
        num_windows = (end_idx + step - 1) // step  # Calculate the number of windows

        if num_windows <= 0:
            return np.array([]), np.array([])

        # Create indices for the start of each window
        start_indices = np.arange(0, end_idx, step)

        # Use advanced indexing to get all the windows
        window_indices = start_indices[:, np.newaxis] + np.arange(step)
        windows = baseband_data[window_indices]

        if self.quadrature:
            first_comp = np.mean(np.real(windows), axis=1)
            second_comp = np.mean(np.imag(windows), axis=1)
        else:
            first_comp = np.mean(np.abs(windows), axis=1)
            second_comp = np.mean(np.angle(windows, True), axis=1)

        return first_comp, second_comp

    def _process_save(self, buffer):
        # Use numpy preallocated array for speed
        num_channels = len(self.data_mapping)
        save_list = np.empty((num_channels, int(buffer.shape[1] // self.save_ds), 2))

        for r_idx, row in enumerate(self.channel_mapping):
            x = buffer[r_idx, :]
            for t_idx, channel_key in enumerate(row):
                channel_idx = self.data_mapping[channel_key][1]
                # Pass the channel key for state tracking
                first_comp, second_comp = self._process_chunk(
                    data=x,
                    filter=self.if_filts[t_idx],
                    if_freq=self.channel_ifs[t_idx],
                    channel_key=channel_key,
                )
                self.logEvent.emit(
                    "debug", f"Processed channel {channel_key} with index {channel_idx}"
                )
                save_list[channel_idx, :, 0] = first_comp
                save_list[channel_idx, :, 1] = second_comp

        # Return all processed samples
        return save_list

    def run(self):
        # Preallocate empty buffer to get faster performance
        data_buf = None
        samples = [None] * len(self.rx_queues)

        while self.running:
            try:
                # Get from all queues
                for idx, rx_q in enumerate(self.rx_queues):
                    samples[idx] = rx_q.get()
                data_buf = np.transpose(np.vstack(samples))

                buffer_data = np.transpose(np.vstack(data_buf))
                processed = self._process_save(buffer_data)

                # Add to save queue
                if self.save_queue is not None:
                    try:
                        self.save_queue.put(processed)
                    except queue.Full:
                        self.logEvent.emit("debug", "[USRP] Save Queue Full")

                # Add to display queue
                try:
                    # TODO: Check for phase here
                    self.disp_queue.put(processed[:, :, 0])
                except queue.Full:
                    self.logEvent.emit("debug", "[USRP] Display Queue Full")

            except queue.Empty:
                self.logEvent.emit("debug", "[USRP] Rx Queue Empty")
                continue
            except queue.Full:
                self.logEvent.emit("debug", "[USRP] Rx Queue Full")
                continue
            except Exception as e:
                self.logEvent.emit("error", f"[USRP] Processing error: {e}")
                continue

        self.logEvent.emit("debug", "[USRP] Processing stopped")

    def stop(self):
        self.running = False
