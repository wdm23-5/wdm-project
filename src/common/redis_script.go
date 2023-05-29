package common

// atomically increase the value if the key already exists and the result will still be >= 0
const LuaIncrbyIfGe0XX = `
local delta = tonumber(ARGV[1])
if delta == nil then
    return false
end
local value = redis.call('GET', KEYS[1])
if value == nil then
    return false
end
value = tonumber(value)
if value ~= nil and value + delta >= 0 then
    redis.call('SET', KEYS[1], value + delta)  -- assume OK
    return value + delta
end
return false
`

const LuaHDecrIfGe0XX = `
local value = redis.call('HGET', KEYS[1], ARGV[1])
if value == nil then
    return false
end
value = tonumber(value)
if value ~= nil and value - 1 >= 0 then
    redis.call('HSET', KEYS[1], ARGV[1], value - 1)
	return value - 1
end
return false
`

// cas if the key already exists
const LuaCASXX = `
local old = redis.call('GET', KEYS[1])
if old == nil or old ~= ARGV[1] then
    return false
end
redis.call('SET', KEYS[1], ARGV[2])
return true
`
