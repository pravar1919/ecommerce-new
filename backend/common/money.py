"""Money is always integer paise. Never use floats for money."""

from dataclasses import dataclass

CURRENCY = "INR"


def format_inr(paise: int) -> str:
    """Format paise as INR with Indian digit grouping, e.g. 12449900 -> '₹1,24,499'.

    Paise are shown only when non-zero (₹1,249.50).
    """
    negative = paise < 0
    rupees, rem = divmod(abs(paise), 100)
    digits = str(rupees)
    if len(digits) > 3:
        head, tail = digits[:-3], digits[-3:]
        groups = []
        while len(head) > 2:
            groups.insert(0, head[-2:])
            head = head[:-2]
        if head:
            groups.insert(0, head)
        digits = ",".join([*groups, tail])
    out = f"₹{digits}" + (f".{rem:02d}" if rem else "")
    return f"-{out}" if negative else out


@dataclass(frozen=True, slots=True)
class Money:
    paise: int
    currency: str = CURRENCY

    def __post_init__(self) -> None:
        if not isinstance(self.paise, int) or isinstance(self.paise, bool):
            raise TypeError("Money.paise must be an int")

    def __add__(self, other: Money) -> Money:
        return Money(self.paise + other.paise, self.currency)

    def __sub__(self, other: Money) -> Money:
        return Money(self.paise - other.paise, self.currency)

    def __mul__(self, qty: int) -> Money:
        return Money(self.paise * qty, self.currency)

    @property
    def formatted(self) -> str:
        return format_inr(self.paise)

    def as_dict(self) -> dict:
        return {"amount": self.paise, "currency": self.currency, "formatted": self.formatted}


def money_dict(paise: int | None) -> dict | None:
    return None if paise is None else Money(int(paise)).as_dict()
