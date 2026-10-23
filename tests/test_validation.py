import pytest

from cortex_engine.validation import validate_pair_lengths, validate_patch_coordinate


def test_equal_lengths():
    validate_pair_lengths(4, 4)


@pytest.mark.parametrize("lengths", [(3, 4), (0, 0), (129, 129)])
def test_invalid_lengths(lengths):
    with pytest.raises(ValueError):
        validate_pair_lengths(*lengths)


def test_valid_coordinate():
    validate_patch_coordinate(1, 3, n_layers=12, n_tokens=8)


@pytest.mark.parametrize("layer,pos", [(-1, 0), (12, 0), (1, -1), (1, 8)])
def test_invalid_coordinate(layer, pos):
    with pytest.raises(ValueError):
        validate_patch_coordinate(layer, pos, n_layers=12, n_tokens=8)
