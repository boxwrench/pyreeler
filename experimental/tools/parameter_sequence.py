"""ParameterSequence module for PyReeler experimental.

Record and replay parameter changes over time for reproducible experiments
and shareable "recipes".

Usage:
    from experimental.tools.parameter_sequence import ParameterSequence

    # Record a sequence
    seq = ParameterSequence()
    seq.record(0, 'threshold', 200)
    seq.record(30, 'threshold', 100)
    seq.save('my_sequence.json')

    # Replay in render loop
    for frame in range(60):
        threshold = seq.get_value(frame, 'threshold', default=128)
        result = pixel_sort(image, threshold=threshold)
"""
import json
from typing import Any, List, Tuple, Union


class ParameterSequence:
    """Record and replay parameter changes over time.

    Enables reproducible experiments by capturing parameter curves as
    keyframes that can be saved, shared, and replayed.

    Attributes:
        keyframes: List of (frame, param, value) tuples representing changes

    Example:
        >>> seq = ParameterSequence()
        >>> seq.record(0, 'threshold', 200)
        >>> seq.record(30, 'threshold', 100)
        >>> seq.get_value(15, 'threshold')  # Interpolated: 150.0
    """

    def __init__(self):
        self.keyframes: List[Tuple[int, str, Any]] = []

    def record(self, frame: int, param: str, value: Any) -> None:
        """Record a parameter change at a specific frame.

        Args:
            frame: Frame number where change occurs
            param: Parameter name (e.g., 'threshold', 'sigma')
            value: New value for the parameter
        """
        self.keyframes.append((frame, param, value))

    def get_value(self, frame: int, param: str, default: Any = None) -> Any:
        """Get interpolated parameter value at frame.

        Performs linear interpolation between keyframes. Returns default
        if no keyframes exist for this parameter.

        Args:
            frame: Frame to sample at
            param: Parameter name to look up
            default: Value to return if no keyframes found

        Returns:
            Interpolated value at the given frame
        """
        # Get all keyframes for this parameter, sorted by frame
        relevant = [(f, v) for f, p, v in self.keyframes if p == param]
        relevant.sort(key=lambda x: x[0])

        if not relevant:
            return default

        # Find surrounding keyframes
        before = [(f, v) for f, v in relevant if f <= frame]
        after = [(f, v) for f, v in relevant if f > frame]

        if not before:
            return relevant[0][1]  # Before first keyframe
        if not after:
            return before[-1][1]   # After last keyframe

        # Linear interpolation between keyframes
        f1, v1 = before[-1]
        f2, v2 = after[0]
        t = (frame - f1) / (f2 - f1)

        # Handle numeric types with interpolation
        if isinstance(v1, (int, float)) and isinstance(v2, (int, float)):
            return v1 + (v2 - v1) * t
        else:
            # For non-numeric types, return nearest keyframe
            return v1 if t < 0.5 else v2

    def get_all_at_frame(self, frame: int) -> dict[str, Any]:
        """Get all parameter values at a given frame.

        Args:
            frame: Frame to sample

        Returns:
            Dictionary of {param_name: interpolated_value}
        """
        # Collect all unique parameter names
        params = set(p for _, p, _ in self.keyframes)

        return {param: self.get_value(frame, param) for param in params}

    def save(self, path: str) -> None:
        """Export sequence to JSON.

        Args:
            path: Output file path (should end in .json)
        """
        with open(path, 'w') as f:
            json.dump(self.keyframes, f, indent=2)

    @classmethod
    def load(cls, path: str) -> 'ParameterSequence':
        """Import sequence from JSON.

        Args:
            path: Path to JSON file created by save()

        Returns:
            New ParameterSequence with loaded keyframes
        """
        seq = cls()
        with open(path, 'r') as f:
            seq.keyframes = json.load(f)
        return seq

    def copy(self) -> 'ParameterSequence':
        """Create a deep copy of this sequence.

        Returns:
            New ParameterSequence with copied keyframes
        """
        seq = ParameterSequence()
        seq.keyframes = self.keyframes.copy()
        return seq

    def scale_time(self, factor: float) -> 'ParameterSequence':
        """Create a time-scaled version of this sequence.

        Args:
            factor: Multiplier for all frame numbers (>1 = slower, <1 = faster)

        Returns:
            New ParameterSequence with scaled timing
        """
        seq = ParameterSequence()
        seq.keyframes = [(int(f * factor), p, v) for f, p, v in self.keyframes]
        return seq

    def __repr__(self) -> str:
        params = sorted(set(p for _, p, _ in self.keyframes))
        return f"ParameterSequence({len(self.keyframes)} keyframes, params={params})"


# Common sequence presets

def ramp(start_frame: int, end_frame: int, param: str,
         start_val: Union[int, float], end_val: Union[int, float]) -> ParameterSequence:
    """Create a linear ramp sequence.

    Args:
        start_frame: Starting frame
        end_frame: Ending frame
        param: Parameter name
        start_val: Starting value
        end_val: Ending value

    Returns:
        ParameterSequence with two keyframes forming a ramp
    """
    seq = ParameterSequence()
    seq.record(start_frame, param, start_val)
    seq.record(end_frame, param, end_val)
    return seq


def pulse(peak_frame: int, param: str,
          base_val: Union[int, float], peak_val: Union[int, float],
          width: int = 10) -> ParameterSequence:
    """Create a single pulse (up then down).

    Args:
        peak_frame: Frame where pulse reaches maximum
        param: Parameter name
        base_val: Value before and after pulse
        peak_val: Maximum value during pulse
        width: Frames from base to peak (total pulse is 2*width)

    Returns:
        ParameterSequence with three keyframes forming a pulse
    """
    seq = ParameterSequence()
    seq.record(peak_frame - width, param, base_val)
    seq.record(peak_frame, param, peak_val)
    seq.record(peak_frame + width, param, base_val)
    return seq


def hold(frame: int, param: str, value: Any) -> ParameterSequence:
    """Create a single hold keyframe.

    Args:
        frame: Frame to hold at
        param: Parameter name
        value: Value to hold

    Returns:
        ParameterSequence with single keyframe
    """
    seq = ParameterSequence()
    seq.record(frame, param, value)
    return seq


if __name__ == "__main__":
    # Demo: Create and test a pixel sort threshold sequence
    print("ParameterSequence Demo")
    print("=" * 50)

    # Build a sequence
    seq = ParameterSequence()
    seq.record(0, 'threshold', 200)      # Start subtle
    seq.record(30, 'threshold', 100)     # Increase effect
    seq.record(60, 'threshold', 200)     # Fade out
    seq.record(0, 'angle', 90)           # Vertical sort
    seq.record(30, 'angle', 45)          # Diagonal at peak
    seq.record(60, 'angle', 90)          # Back to vertical

    print(f"Created: {seq}")
    print()

    # Sample values
    print("Sampling threshold values:")
    for f in [0, 15, 30, 45, 60]:
        thresh = seq.get_value(f, 'threshold', default=128)
        angle = seq.get_value(f, 'angle', default=0)
        print(f"  Frame {f:2d}: threshold={thresh:6.1f}, angle={angle:5.1f}")

    print()

    # Save/load demo
    import tempfile
    import os

    with tempfile.NamedTemporaryFile(suffix='.json', delete=False, mode='w') as f:
        temp_path = f.name

    try:
        seq.save(temp_path)
        print(f"Saved to: {temp_path}")

        loaded = ParameterSequence.load(temp_path)
        print(f"Loaded: {loaded}")
        # JSON converts tuples to lists, so compare as lists
        loaded_kf = [list(kf) for kf in loaded.keyframes]
        orig_kf = [list(kf) for kf in seq.keyframes]
        print(f"Roundtrip OK: {loaded_kf == orig_kf}")
    finally:
        os.unlink(temp_path)

    print()

    # Preset demo
    print("Preset: ramp from 0 to 100 over 60 frames")
    ramp_seq = ramp(0, 60, 'brightness', 0, 100)
    print(f"  Frame 30 value: {ramp_seq.get_value(30, 'brightness')}")

    print()
    print("Preset: pulse at frame 30")
    pulse_seq = pulse(30, 'glitch_amount', 0.0, 1.0, width=10)
    for f in [20, 25, 30, 35, 40]:
        print(f"  Frame {f}: {pulse_seq.get_value(f, 'glitch_amount')}")
