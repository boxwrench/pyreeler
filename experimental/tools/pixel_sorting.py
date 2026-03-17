"""Pixel Sorting module for PyReeler experimental.

Glitch aesthetic through row/column pixel reordering.
Threshold, interval, mask, and angle variants.

Usage:
    from experimental.tools.pixel_sorting import pixel_sort, threshold_mask

    sorted_img = pixel_sort(image, threshold=200, angle=90)
"""
import numpy as np
from PIL import Image


def brightness_sort_row(row, threshold=128, reverse=False):
    """Sort a single row by pixel brightness.

    Args:
        row: 1D array of RGB values (flattened or per-channel)
        threshold: Minimum brightness to include in sorting
        reverse: Sort dark to light if True

    Returns:
        Sorted row array
    """
    # Calculate brightness (perceptual luminance)
    if len(row.shape) == 2 and row.shape[1] == 3:
        # RGB input
        brightness = 0.299 * row[:, 0] + 0.587 * row[:, 1] + 0.114 * row[:, 2]
    else:
        # Already grayscale
        brightness = row

    # Find contiguous segments above threshold
    mask = brightness >= threshold

    if not mask.any():
        return row

    # Sort each contiguous segment
    result = row.copy()
    in_segment = False
    start_idx = 0

    for i, is_above in enumerate(mask):
        if is_above and not in_segment:
            # Start of segment
            start_idx = i
            in_segment = True
        elif not is_above and in_segment:
            # End of segment - sort it
            segment = result[start_idx:i]
            if len(segment.shape) == 2:
                # Sort by brightness
                seg_brightness = 0.299 * segment[:, 0] + 0.587 * segment[:, 1] + 0.114 * segment[:, 2]
                sort_idx = np.argsort(seg_brightness)
                if reverse:
                    sort_idx = sort_idx[::-1]
                result[start_idx:i] = segment[sort_idx]
            in_segment = False

    # Handle segment that extends to end
    if in_segment:
        segment = result[start_idx:]
        if len(segment.shape) == 2:
            seg_brightness = 0.299 * segment[:, 0] + 0.587 * segment[:, 1] + 0.114 * segment[:, 2]
            sort_idx = np.argsort(seg_brightness)
            if reverse:
                sort_idx = sort_idx[::-1]
            result[start_idx:] = segment[sort_idx]

    return result


def pixel_sort(image, threshold=200, angle=90, interval=0):
    """Sort pixels in an image.

    Args:
        image: PIL Image or numpy array
        threshold: Brightness threshold (0-255)
        angle: Sort direction (0=horizontal, 90=vertical, 45=diagonal)
        interval: If > 0, sort every Nth row/column only

    Returns:
        PIL Image
    """
    if isinstance(image, Image.Image):
        img_array = np.array(image)
    else:
        img_array = image.copy()

    original_shape = img_array.shape

    # Handle rotation for angle
    if angle == 90:
        # Vertical sort (sort columns)
        img_array = np.transpose(img_array, (1, 0, 2))
    elif angle == 45:
        # Diagonal sort (rotate 45, sort, rotate back - simplified)
        from scipy.ndimage import rotate
        img_array = rotate(img_array, 45, reshape=True, order=1)
    elif angle != 0:
        # Arbitrary angle - rotate
        from scipy.ndimage import rotate
        img_array = rotate(img_array, angle, reshape=True, order=1)

    # Sort each row
    for i in range(img_array.shape[0]):
        if interval > 0 and i % interval != 0:
            continue
        img_array[i] = brightness_sort_row(img_array[i], threshold)

    # Undo rotation
    if angle == 90:
        img_array = np.transpose(img_array, (1, 0, 2))
    elif angle != 0:
        from scipy.ndimage import rotate
        img_array = rotate(img_array, -angle, reshape=False, order=1)
        # Crop back to original size
        h, w = original_shape[:2]
        ch, cw = img_array.shape[:2]
        y_offset = (ch - h) // 2
        x_offset = (cw - w) // 2
        img_array = img_array[y_offset:y_offset+h, x_offset:x_offset+w]

    return Image.fromarray(np.clip(img_array, 0, 255).astype(np.uint8))


def threshold_mask(image, lower, upper):
    """Create a mask for pixels within brightness range.

    Args:
        image: PIL Image or numpy array
        lower: Lower brightness threshold
        upper: Upper brightness threshold

    Returns:
        Binary mask as numpy array
    """
    if isinstance(image, Image.Image):
        img_array = np.array(image)
    else:
        img_array = image

    if len(img_array.shape) == 3:
        brightness = 0.299 * img_array[:, :, 0] + 0.587 * img_array[:, :, 1] + 0.114 * img_array[:, :, 2]
    else:
        brightness = img_array

    return (brightness >= lower) & (brightness <= upper)


def masked_sort(image, mask, angle=90):
    """Sort only pixels within mask.

    Args:
        image: PIL Image or numpy array
        mask: Binary mask (True = sort this pixel)
        angle: Sort direction

    Returns:
        PIL Image
    """
    if isinstance(image, Image.Image):
        img_array = np.array(image).copy()
    else:
        img_array = image.copy()

    # Apply mask - only sort masked pixels
    if angle == 90:
        img_array = np.transpose(img_array, (1, 0, 2))
        mask = mask.T

    # For each row, sort only masked pixels
    for i in range(img_array.shape[0]):
        row_mask = mask[i]
        if not row_mask.any():
            continue

        row = img_array[i]
        masked_pixels = row[row_mask]

        if len(masked_pixels) > 1:
            # Sort by brightness
            brightness = 0.299 * masked_pixels[:, 0] + 0.587 * masked_pixels[:, 1] + 0.114 * masked_pixels[:, 2]
            sort_idx = np.argsort(brightness)
            row[row_mask] = masked_pixels[sort_idx]

    if angle == 90:
        img_array = np.transpose(img_array, (1, 0, 2))

    return Image.fromarray(np.clip(img_array, 0, 255).astype(np.uint8))


def interval_sort(image, interval=5, threshold=200, angle=90):
    """Sort every Nth row/column.

    Args:
        image: PIL Image
        interval: Sort every Nth row (e.g., 5 = sort rows 0, 5, 10...)
        threshold: Brightness threshold
        angle: Sort direction

    Returns:
        PIL Image
    """
    return pixel_sort(image, threshold=threshold, angle=angle, interval=interval)


if __name__ == "__main__":
    # Demo: Create test pattern and sort it
    print("Pixel Sorting Demo")
    print("=" * 50)

    # Create test image (gradient with some structure)
    size = 256
    test_img = np.zeros((size, size, 3), dtype=np.uint8)

    # Gradient background
    for i in range(size):
        test_img[i, :] = [i, 128, 255 - i]

    # Add some bright spots
    test_img[50:80, 50:80] = 255
    test_img[150:200, 100:180] = 200

    pil_img = Image.fromarray(test_img)
    pil_img.save("pixel_sort_test_input.png")
    print(f"Created test image: {test_img.shape}")

    # Test different sorts
    print("\nTesting sort variants:")

    # Threshold sort
    sorted_img = pixel_sort(pil_img, threshold=150, angle=90)
    sorted_img.save("pixel_sort_test_threshold.png")
    print("  - Threshold sort (T=150, vertical)")

    # Interval sort
    sorted_img = interval_sort(pil_img, interval=10, threshold=100, angle=0)
    sorted_img.save("pixel_sort_test_interval.png")
    print("  - Interval sort (every 10th row)")

    # Masked sort
    mask = threshold_mask(pil_img, 180, 255)
    sorted_img = masked_sort(pil_img, mask, angle=90)
    sorted_img.save("pixel_sort_test_masked.png")
    print("  - Masked sort (brightness 180-255)")

    print("\nOutput files saved")
