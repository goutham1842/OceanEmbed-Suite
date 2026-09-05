"""
OceanEmbed — Tests for Grid and Coordinate Utilities.
"""

import numpy as np
try:
    import pytest
except ImportError:
    pytest = None

from src.data.grid import (
    DOMAIN,
    GRID_SHAPE,
    SIH_DEPTHS,
    get_region_id,
    get_region_name,
    make_grid,
    nearest_grid_index,
    normalize_depth,
    normalize_doy,
    normalize_lat,
    normalize_lon,
)


def test_domain_constants():
    assert DOMAIN["lat_min"] == 5.0
    assert DOMAIN["lat_max"] == 30.0
    assert DOMAIN["lon_min"] == 45.0
    assert DOMAIN["lon_max"] == 105.0
    assert DOMAIN["resolution"] == 0.25
    assert len(SIH_DEPTHS) == 15
    assert SIH_DEPTHS[0] == 0
    assert SIH_DEPTHS[-1] == 1000


def test_make_grid():
    lats, lons = make_grid()
    assert len(lats) == GRID_SHAPE[0]  # 101
    assert len(lons) == GRID_SHAPE[1]  # 241
    assert np.isclose(lats[0], 5.0)
    assert np.isclose(lats[-1], 30.0)
    assert np.isclose(lons[0], 45.0)
    assert np.isclose(lons[-1], 105.0)


def test_coordinate_normalization():
    # Lat normalization: [5, 30] -> [-1, 1]
    assert np.isclose(normalize_lat(5.0), -1.0)
    assert np.isclose(normalize_lat(30.0), 1.0)
    assert np.isclose(normalize_lat(17.5), 0.0)

    # Lon normalization: [45, 105] -> [-1, 1]
    assert np.isclose(normalize_lon(45.0), -1.0)
    assert np.isclose(normalize_lon(105.0), 1.0)
    assert np.isclose(normalize_lon(75.0), 0.0)

    # Depth normalization: [0, 1000] -> [0, 1]
    assert np.isclose(normalize_depth(0.0), 0.0)
    assert np.isclose(normalize_depth(500.0), 0.5)
    assert np.isclose(normalize_depth(1000.0), 1.0)

    # DOY normalization: [0, 365.25] -> [0, 1]
    assert 0.0 <= normalize_doy(180) <= 1.0


def test_region_classification():
    # Arabian Sea: lat ~ 15, lon ~ 65
    assert get_region_id(15.0, 65.0) == 0
    assert get_region_name(15.0, 65.0) == "Arabian Sea"

    # Bay of Bengal: lat ~ 15, lon ~ 90
    assert get_region_id(15.0, 90.0) == 1
    assert get_region_name(15.0, 90.0) == "Bay of Bengal"

    # Open Ocean: lat ~ 6.0, lon ~ 103.0
    assert get_region_id(6.0, 103.0) == 2
    assert get_region_name(6.0, 103.0) == "Open Ocean"


def test_nearest_grid_index():
    lat_idx, lon_idx = nearest_grid_index(5.1, 45.1)
    assert lat_idx == 0
    assert lon_idx == 0

    with pytest.raises(ValueError):
        nearest_grid_index(2.0, 70.0)  # out of domain
