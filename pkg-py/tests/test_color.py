from __future__ import annotations

import pytest
from brand_yml import read_brand_yml
from syrupy.extensions.json import JSONSnapshotExtension
from utils import path_examples, pydantic_data_from_json


@pytest.fixture
def snapshot_json(snapshot):
    return snapshot.use_extension(JSONSnapshotExtension)


def test_brand_color_ex_direct_posit(snapshot_json):
    brand = read_brand_yml(path_examples("brand-color-direct-posit.yml"))

    assert brand.color is not None
    assert brand.color.foreground == "#151515"
    assert brand.color.background == "#FFFFFF"
    assert brand.color.primary == "#447099"
    assert brand.color.secondary == "#707073"
    assert brand.color.tertiary == "#C2C2C4"
    assert brand.color.success == "#72994E"
    assert brand.color.info == "#419599"
    assert brand.color.warning == "#EE6331"
    assert brand.color.danger == "#9A4665"
    assert brand.color.light == "#FFFFFF"
    assert brand.color.dark == "#404041"

    assert snapshot_json == pydantic_data_from_json(brand)


def test_brand_color_ex_palette_posit(snapshot_json):
    brand = read_brand_yml(path_examples("brand-color-palette-posit.yml"))

    # Same final values as above, but re-uses color definitions from `with`
    assert brand.color is not None
    assert brand.color.foreground == "#151515"
    assert brand.color.background == "#FFFFFF"
    assert brand.color.primary == "#447099"
    assert brand.color.secondary == "#707073"
    assert brand.color.tertiary == "#C2C2C4"
    assert brand.color.success == "#72994E"
    assert brand.color.info == "#419599"
    assert brand.color.warning == "#EE6331"
    assert brand.color.danger == "#9A4665"
    assert brand.color.light == "#FFFFFF"
    assert brand.color.dark == "#404041"

    assert brand.color.palette is not None
    assert brand.color.palette == {
        "white": "#FFFFFF",
        "black": "#151515",
        "blue": "#447099",
        "orange": "#EE6331",
        "green": "#72994E",
        "teal": "#419599",
        "burgundy": "#9A4665",
    }

    assert snapshot_json == pydantic_data_from_json(brand)


def test_brand_color_ex_palette_internal(snapshot_json):
    brand = read_brand_yml(path_examples("brand-color-palette-internal.yml"))

    # Named theme colors are reused in BrandColor
    assert brand.color is not None
    assert brand.color.background == "#FFFFFF"
    assert brand.color.primary == "#447099"
    assert brand.color.info == brand.color.primary
    assert brand.color.light == brand.color.background

    assert brand.color.palette is not None
    assert brand.color.palette == {
        "white": "#FFFFFF",
        "black": "#151515",
        "blue": "#447099",
        "orange": "#EE6331",
        "green": "#72994E",
        "teal": "#419599",
        "burgundy": "#9A4665",
    }

    assert snapshot_json == pydantic_data_from_json(brand)
