# Turning a number into a short code and back.
#
# Base62 = 0-9, a-z, A-Z. Same idea as base 10, just with 62 "digits".
# 7 characters of base62 = 62**7 = about 3.5 trillion codes.
#
# Because the number comes from the database's auto-increment id,
# two links can never get the same code. No collisions, no retry loop.

ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
BASE = len(ALPHABET)  # 62


def encode(number: int) -> str:
    if number < 0:
        raise ValueError("number must be >= 0")
    if number == 0:
        return ALPHABET[0]
    chars = []
    while number > 0:
        number, remainder = divmod(number, BASE)
        chars.append(ALPHABET[remainder])
    return "".join(reversed(chars))


def decode(code: str) -> int:
    number = 0
    for char in code:
        number = number * BASE + ALPHABET.index(char)
    return number
