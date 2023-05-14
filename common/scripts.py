lua_incrby_xx_ge_0 = """
local delta = tonumber(ARGV[1])
if delta == nil then
    return nil
end
local value = redis.call('GET', KEYS[1])
if value == nil then
    return nil
end
value = tonumber(value)
if value ~= nil and value >= 0 and value + delta >= 0 then
    redis.call('SET', KEYS[1], value + delta)  -- assume OK
    return value + delta
end
return nil
"""

lua_hdecr_ge_0 = """
local value = redis.call('HGET', KEYS[1], ARGV[1])
value = tonumber(value)
if value ~= nil and value > 0 then
    return redis.call('HINCRBY', KEYS[1], ARGV[1], -1)
end
return 0
"""
