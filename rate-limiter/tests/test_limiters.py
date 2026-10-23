from app.limiters import (
    InMemoryFixedWindow,
    RedisFixedWindow,
    RedisTokenBucket,
)


def allowed(limiter, times, key="k"):
    return sum(limiter.allow(key, now=t).allowed for t in times)


def test_fixed_window_allows_limit_then_blocks(r):
    fw = RedisFixedWindow(r, 10, 60)
    assert allowed(fw, [1.0] * 15) == 10


def test_fixed_window_lets_double_burst_through_at_edge(r):
    fw = RedisFixedWindow(r, 10, 60)
    assert allowed(fw, [59.5] * 10 + [60.5] * 10) == 20


def test_token_bucket_blocks_double_burst(r):
    tb = RedisTokenBucket(r, 10, 60)
    assert allowed(tb, [59.5] * 10 + [60.5] * 10) == 10


def test_token_bucket_refills_over_time(r):
    tb = RedisTokenBucket(r, 10, 60)  # 1 token every 6 s
    assert allowed(tb, [0.0] * 10) == 10
    assert not tb.allow("k", now=5.0).allowed
    assert tb.allow("k", now=6.1).allowed


def test_token_bucket_never_goes_above_capacity(r):
    tb = RedisTokenBucket(r, 10, 60)
    tb.allow("k", now=0.0)
    # a whole day idle still only gives back 10 tokens
    assert allowed(tb, [86400.0] * 20) == 10


def test_token_bucket_retry_after(r):
    tb = RedisTokenBucket(r, 10, 60)
    allowed(tb, [0.0] * 10)
    d = tb.allow("k", now=0.0)
    assert not d.allowed
    assert 5.9 < d.retry_after <= 6.0


def test_token_bucket_uses_redis_clock_when_no_time_given(r):
    tb = RedisTokenBucket(r, 10, 60)
    assert sum(tb.allow("k").allowed for _ in range(12)) == 10


def test_keys_are_separate(r):
    fw = RedisFixedWindow(r, 10, 60)
    assert allowed(fw, [1.0] * 10, key="a") == 10
    assert fw.allow("b", now=1.0).allowed


def test_in_memory_counter_multiplies_limit_across_servers(r):
    servers = [InMemoryFixedWindow(10, 60) for _ in range(3)]
    assert sum(servers[i % 3].allow("k", now=1.0).allowed for i in range(30)) == 30


def test_shared_redis_counter_holds_across_servers(r):
    servers = [RedisFixedWindow(r, 10, 60) for _ in range(3)]
    assert sum(servers[i % 3].allow("k", now=1.0).allowed for i in range(30)) == 10
