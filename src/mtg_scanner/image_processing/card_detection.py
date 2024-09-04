from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import cv2 as cv
import numpy as np

if TYPE_CHECKING:
    import cv2.typing as ct

logger = logging.getLogger(__name__)


def detect_card_edge(image: ct.MatLike) -> ct.MatLike:
    """https://learnopencv.com/contour-detection-using-opencv-python-c/"""
    # Convert the image to grayscale
    grayscale_img = cv.cvtColor(image, cv.COLOR_BGR2GRAY)
    # set all pixels above threshold to 255 and all others to 0
    # gives a black and white mask of the image for cleaner contours
    ret, threshold_img = cv.threshold(
        grayscale_img, thresh=70, maxval=255, type=cv.THRESH_BINARY
    )
    # NOTE: cv.CHAIN_APPROX_NONE is the most accurate, but cv.CHAIN_APPROX_SIMPLE is faster with less "resolution"
    # may be worth playing with the `mode` in the future to see if it affects the results
    contours, hierarchy = cv.findContours(
        image=threshold_img,
        mode=cv.RETR_CCOMP,
        method=cv.CHAIN_APPROX_NONE,
    )

    # filter only parent contours
    # each contour is part of a hierarchy
    # the hierarchy "mask" is a 4-element array
    # next is the next contour in the image at the same hierarchical level
    # previous is the previous contour in the image at the same hierarchical level
    # first_child is the first child of the contour currently being considered
    # parent is the index of the parent contour

    # the outer edge of the image gets identified as a contour, so we need to find the first children of the outer edge
    try:
        outer_border_contour_index = [
            i
            for i, (next_, previous, first_child, parent) in enumerate(hierarchy[0])
            if parent == -1 and next_ == -1 and first_child > -1
        ][0]
    except IndexError:
        logger.debug("No outer border contour found")
        outer_border_contour_index = None

    # grab largest contour by area
    # this should help remove any tiny contour noise
    contours_to_consider = list(contours)
    # drop the outer border contour if one was found
    if outer_border_contour_index is not None:
        contours_to_consider.pop(outer_border_contour_index)
    card_contour = max(contours_to_consider, key=cv.contourArea)

    return card_contour


def blackout_outside_contour(img: ct.MatLike, contour: ct.MatLike) -> ct.MatLike:
    """
    SO link: https://stackoverflow.com/questions/28759253/how-to-crop-the-internal-area-of-a-contour
    """
    mask = np.zeros_like(img)
    mask = cv.drawContours(
        image=mask,
        contours=[contour],
        contourIdx=-1,
        color=(255, 255, 255),
        thickness=cv.FILLED,
    )
    out = np.zeros_like(img)
    out[mask == 255] = img[mask == 255]

    return out


def crop_img_to_contour(img: ct.MatLike, contour: ct.MatLike) -> ct.MatLike:
    """
    SO link: https://stackoverflow.com/questions/28759253/how-to-crop-the-internal-area-of-a-contour
    """
    x, y, w, h = cv.boundingRect(contour)
    cropped_image = img[y : y + h, x : x + w]
    return cropped_image
