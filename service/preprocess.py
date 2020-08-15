import numpy as np
import pydicom
import os
import scipy.ndimage

MIN_BOUND = -1000.0
MAX_BOUND = 400.0
PIXEL_MEAN = 0.25


def normalize(image):
    image = (image - MIN_BOUND) / (MAX_BOUND - MIN_BOUND)
    image[image > 1] = 1.
    image[image < 0] = 0.
    return image


def zero_center(image):
    image = image - PIXEL_MEAN
    return image


def preprocess(paths):
    slices = [pydicom.read_file(path) for path in paths]
    try:
        slices.sort(key=lambda x: float(x.ImagePositionPatient[2]))
    except Exception as err:
        print("Not a CT scan, skipping!")
        return list()
    if len(slices) == 0:
        print("Not a CT scan, skipping!")
        return list()
    try:
        slice_thickness = np.abs(slices[0].ImagePositionPatient[2] - slices[1].ImagePositionPatient[2])
    except Exception as err1:
        try:
            slice_thickness = np.abs(slices[0].SliceLocation - slices[1].SliceLocation)
        except Exception as err2:
            print("Not enough slices, skipping!")
            return list()
    for s in slices:
        s.SliceThickness = slice_thickness
    return slices


def get_pixels_hu(slices):
    image = np.stack([s.pixel_array for s in slices])
    image = image.astype(np.int16)
    image[image == -2000] = 0
    for slice_number in range(len(slices)):
        intercept = slices[slice_number].RescaleIntercept
        slope = slices[slice_number].RescaleSlope
        if slope != 1:
            image[slice_number] = slope * image[slice_number].astype(np.float64)
            image[slice_number] = image[slice_number].astype(np.int16)
        image[slice_number] += np.int16(intercept)
    return np.array(image, dtype=np.int16)


def resample(image, scan):
    new_spacing = [1, 1, 1]
    x = [scan[0].SliceThickness]
    y = list(scan[0].PixelSpacing)
    x.extend(y)
    spacing = np.array(x, dtype=np.float32)
    resize_factor = spacing / new_spacing
    new_real_shape = image.shape * resize_factor
    new_shape = np.round(new_real_shape)
    real_resize_factor = new_shape / image.shape
    new_spacing = spacing / real_resize_factor
    image = scipy.ndimage.interpolation.zoom(image, real_resize_factor, mode='nearest')
    return image, new_spacing


def get_3d_preprocessed_data(paths):
    slices = preprocess(paths)
    if len(slices) > 0:
        patient_pixels = get_pixels_hu(slices)
        pix_resampled, spacing = resample(patient_pixels, slices)
        print("Shape before resampling\t", patient_pixels.shape)
        print("Shape after resampling\t", pix_resampled.shape)
        return pix_resampled
    else:
        return None
