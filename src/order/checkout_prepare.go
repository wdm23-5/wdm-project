package order

import (
	"context"
	"fmt"
	"github.com/gin-gonic/gin"
	"net/http"
	"strconv"
	"wdm/common"
)

const luaPrepareCkTx = `
-- k1: user_id; k2: paid; k3: cart; k4: paying_tx; k5: tx_state
-- a1: tx_id; a2: TxPreparing

local user_id = redis.call('GET', KEYS[1])
if user_id == nil then
    return false
end

local paid = redis.call('GET', KEYS[2])
if paid == nil then
    return false
end

-- if paid, the paying tx will already be locked by the transaction id
-- failed transaction will delete this key
local locked = redis.call('SET', KEYS[4], ARGV[1], 'NX')
if locked == nil then
    -- lock failed
    return {user_id, paid}
end

redis.call('SET', KEYS[5], ARGV[2])

local cart = redis.call('HGETALL', KEYS[3])

return {user_id, paid, cart}
`

func prepareCkTx(ctx *gin.Context, orderId, txId string) (locked bool, info orderInfo, err error) {
	val, err := rsPrepareTxOrder.Run(ctx, rdb, []string{
		keyUserId(orderId),
		keyPaid(orderId),
		keyCart(orderId),
		keyPayingTx(orderId),
		common.KeyTxState(txId),
	}, txId, common.TxPreparing).Result()
	if err != nil {
		err = fmt.Errorf("prepareCkTx: %v", err)
		return
	}

	arr, ok := val.([]interface{})
	if !ok {
		err = fmt.Errorf("prepareCkTx: not an array of any")
		return
	}

	switch al := len(arr); al {
	case 2, 3:
		if info.userId, ok = arr[0].(string); !ok {
			err = fmt.Errorf("prepareCkTx: array[0] not a string")
			return
		}

		if paidStr, ok := arr[1].(string); !ok {
			err = fmt.Errorf("prepareCkTx: array[1] not a string")
			return
		} else if paid, errA := strconv.Atoi(paidStr); errA != nil {
			err = fmt.Errorf("prepareCkTx: array[1] not an int (%v)", errA)
			return
		} else {
			info.paid = paid != 0
		}

		if al == 2 {
			locked = false
			if err != nil {
				panic(fmt.Sprintf("prepareCkTx: error state %v", err))
			}
			return
		}

		cart, ok := arr[2].([]interface{})
		if !ok {
			err = fmt.Errorf("prepareCkTx: array[2] not an array of any")
			return
		}
		cl := len(cart)
		if cl == 0 {
			info.cart = make(map[string]int, 0)
			goto skipCart
		}
		if cl&1 != 0 {
			err = fmt.Errorf("prepareCkTx: array[2] array length error (%v)", cl)
			return
		}
		info.cart = make(map[string]int, cl>>1)
		for i := 0; i < cl; i += 2 {
			itemId, ok := cart[i].(string)
			if !ok {
				err = fmt.Errorf("prepareCkTx: array[2][%v] not a string", i)
				return
			}
			amountStr, ok := cart[i+1].(string)
			if !ok {
				err = fmt.Errorf("prepareCkTx: array[2][%v] not a string", i+1)
				return
			}
			amount, errA := strconv.Atoi(amountStr)
			if errA != nil {
				err = fmt.Errorf("prepareCkTx: array[2][%v] not an int (%v)", i+1, amountStr)
				return
			}
			info.cart[itemId] = amount
		}
	skipCart:
		locked = true
		if err != nil {
			panic(fmt.Sprintf("prepareCkTx: error state %v", err))
		}
		return

	default:
		err = fmt.Errorf("prepareCkTx: array length error (%v)", al)
		return
	}
}

func prepareCkStock(ctx *gin.Context, info orderInfo, txId string) (totalCost int, err error) {
	if len(info.cart) == 0 {
		panic("prepareCkStock")
	}

	// todo: group by id
	request := common.ItemTxPrepareRequest{TxId: txId, Items: make([]common.IdAmountPair, 0, len(info.cart))}
	for itemId, amount := range info.cart {
		if amount < 0 {
			panic("prepareCkStock: LuaHDecrIfGe0XX")
		}
		if amount == 0 {
			continue
		}
		request.Items = append(request.Items, common.IdAmountPair{Id: itemId, Amount: amount})
	}
	// todo
	prepareItemTx(ctx, txId)

	for i := 0; i < nThread; i++ {
		select {
		case cost := <-costCh:
			totalCost += cost
		case <-errCh:
			go func(i int) {
				// wait for all prepare to finish
				// todo: allow fast abort
				for i++; i < nThread; i++ {
					select {
					case <-costCh:
					case <-errCh:
					}
				}
				abortItemTx(ctx, txId)
			}(i)
			return 0, fmt.Errorf("abort tx %v", txId)
		}
	}
	return totalCost, nil
}

//goland:noinspection GoUnusedParameter
func prepareItemTx(ctx context.Context, txId string) error {
	resp, err := http.Post(gatewayUrl+"/tx/prepare/"+txId, "application/json", nil)
	if err != nil {
		return fmt.Errorf("prepareItemTx: post %v", err)
	}
	if resp.StatusCode != http.StatusOK {
		return fmt.Errorf("prepareItemTx: http %v", resp.Status)
	}
	return nil
}
