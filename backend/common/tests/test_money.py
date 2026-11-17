import pytest

from common.money import Money, format_inr


@pytest.mark.parametrize(
    "paise,expected",
    [
        (0, "₹0"),
        (99, "₹0.99"),
        (100, "₹1"),
        (99900, "₹999"),
        (100000, "₹1,000"),
        (1249900, "₹12,499"),
        (12450000, "₹1,24,500"),
        (1000000000, "₹1,00,00,000"),
        (123456789, "₹12,34,567.89"),
        (-150000, "-₹1,500"),
    ],
)
def test_format_inr_indian_grouping(paise, expected):
    assert format_inr(paise) == expected


def test_money_is_integer_only():
    with pytest.raises(TypeError):
        Money(10.5)
    with pytest.raises(TypeError):
        Money(True)
    assert (Money(1000) + Money(250)) * 2 == Money(2500)
    assert Money(1249900).as_dict() == {"amount": 1249900, "currency": "INR", "formatted": "₹12,499"}
