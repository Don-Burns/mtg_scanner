from dataclasses import dataclass
from pathlib import Path
from typing import Self

import cv2 as cv
import cv2.typing as ct
import pytest

from mtg_scanner.image_processing.card_detection import detect_card_edge

DATA_DIR = Path(__file__).parent.parent / "data" / "input"
EXPECTED_DIR = Path(__file__).parent.parent / "data" / "expected"
DEBUG_DIR = Path(__file__).parent.parent / "data" / "debug"


@dataclass
class _Corners:
    top_left: tuple[int, int]
    top_right: tuple[int, int]
    bottom_left: tuple[int, int]
    bottom_right: tuple[int, int]

    @classmethod
    def from_contour(cls, contour: ct.MatLike) -> Self:
        x, y, w, h = cv.boundingRect(contour)
        return cls(
            top_left=(x, y),
            top_right=(x + w, y),
            bottom_left=(x, y + h),
            bottom_right=(x + w, y + h),
        )


@pytest.mark.parametrize(
    # going with corners to make it less sensitive to the algorithm/processing changing the shape of the contour
    # This is a bit of a trade off for a more understandable output vs precise testing
    ("img_name", "expected_corners"),
    (
        pytest.param(
            "card_on_white.jpg",
            _Corners(
                top_left=(90, 151),
                top_right=(535, 151),
                bottom_left=(90, 754),
                bottom_right=(535, 754),
            ),
        ),
    ),
)
def test_edge_detection(img_name: str, expected_corners: _Corners) -> None:
    # Load the image
    image = cv.imread(str(DATA_DIR / img_name))
    if image is None:
        raise FileNotFoundError("Image not found")

    card_bounds = detect_card_edge(image)

    try:
        assert _Corners.from_contour(card_bounds) == expected_corners
    except AssertionError as err:
        # Save the result if assertion fails for visual inspection/debugging
        out_path = DEBUG_DIR / img_name
        line_thickness = 10
        # NOTE: debug point to see the contours on the whole image
        image = cv.drawContours(
            image=image,
            contours=[card_bounds],
            contourIdx=-1,  # -ve to draw all
            color=(0, 255, 0),
            thickness=line_thickness,
        )
        rect = _Corners.from_contour(card_bounds)
        image = cv.rectangle(
            image,
            rect.top_left,
            rect.bottom_right,
            color=(0, 0, 255),
            thickness=line_thickness,
        )
        image = cv.putText(
            img=image,
            text="Red = Corners, Green = Contour",
            org=(10, 50),
            fontFace=cv.FONT_HERSHEY_SIMPLEX,
            fontScale=1,
            color=(0, 0, 0),
            thickness=line_thickness // 2,
            lineType=cv.LINE_AA,
        )
        cv.imwrite(str(out_path), image)

        raise AssertionError(
            f"Card bounds do not match expected. Result of bounds on image saved to {out_path}"
        ) from err
