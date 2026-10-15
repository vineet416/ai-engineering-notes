# Why I dropped "hash the URL" for ID generation.
#
# My first design: MD5 the long URL and keep the first 7 characters as the code.
# This script makes 1,000,000 different URLs and counts how many of them
# end up with a code that some other URL already has.
#
# Run from the project folder:  python scripts/hash_collisions.py

import hashlib
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.core.config import ID_OFFSET  # noqa: E402
from app.services.codes import encode  # noqa: E402

N = 1_000_000

seen = set()
collisions = 0
for i in range(N):
    url = f"https://example.com/products/{i}?ref=newsletter"
    code = hashlib.md5(url.encode()).hexdigest()[:7]
    if code in seen:
        collisions += 1
    seen.add(code)

counter_codes = {encode(i + ID_OFFSET) for i in range(1, N + 1)}

print(f"URLs shortened:              {N:,}")
print()
print("Design: md5(url), first 7 chars")
print(f"  collisions:                {collisions:,}")
print("  every one of these needs a DB check and a retry with a new code")
print()
print("Code: database id + base62")
print(f"  collisions:                {N - len(counter_codes):,}")
print(f"  first code: {encode(1 + ID_OFFSET)}   last code: {encode(N + ID_OFFSET)}")
