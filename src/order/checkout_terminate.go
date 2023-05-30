package order

import (
	"context"
	"fmt"
	"github.com/gin-gonic/gin"
	"net/http"
	"time"
	"wdm/common"
)

// ------- commit -------

const luaCommitCkTx = `
-- k1: paying_tx; k2: tx_state; k3: paid
-- a1: tx_id; a2: TxCommitted

local locked = redis.call('GET', KEYS[1])
if locked ~= ARGV[1] then
    -- not locked by this tx
    return false
end
redis.call('SET', KEYS[2], ARGV[2])
redis.call('SET', KEYS[3], 1)
return true
`

func commitCkTx(ctx *gin.Context, orderId, txId string) error {
	_, err := rsCommitPayTx.Run(
		ctx, rdb,
		[]string{keyPayingTx(orderId), common.KeyTxState(txId), keyPaid(orderId)},
		txId, common.TxCommitted,
	).Result()
	if err != nil {
		return fmt.Errorf("commitCkTx: %v", err)
	}
	return nil
}

//goland:noinspection GoUnusedParameter
func commitItemTx(ctx context.Context, txId string) {
	// todo: use message queue
	for {
		_, err := http.Post(gatewayUrl+"/tx/commit/"+txId, "text/plain", nil)
		if err != nil {
			time.Sleep(10 * time.Millisecond)
			continue
		}
		break
	}
}

// ------- abort -------

// todo
const luaAbortTxXX = `
-- k1: paying_lock; k2: tx_state
-- a1: tx_id; a2: new TxState; a3: unlock?

local locked = redis.call('GET', KEYS[1])
if locked ~= ARGV[1] then
    -- not locked by this tx
    return false
end

local unlock = tonumber(ARGV[3])
if unlock ~= nil and unlock ~= 0 then
    redis.call('DEL', KEYS[1])
end

redis.call('SET', KEYS[2], ARGV[2])
return true
`

//goland:noinspection GoUnusedParameter
func abortItemTx(ctx context.Context, txId string) {
	// todo: use message queue
	for {
		_, err := http.Post(gatewayUrl+"/tx/abort/"+txId, "text/plain", nil)
		if err != nil {
			time.Sleep(10 * time.Millisecond)
			continue
		}
		break
	}
}
