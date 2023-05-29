package stock

import (
	"context"
	"fmt"
	"github.com/gin-gonic/gin"
	"github.com/redis/go-redis/v9"
	"net/http"
	"strconv"
	"time"
	"wdm/common"
)

// todo: refactor

func prepareTx(ctx *gin.Context) {
	var data common.ItemTxPrepareRequest
	if err := ctx.BindJSON(&data); err != nil {
		return
	}
	state, err := common.InitTxStateNX(ctx, rdb, data.TxId)
	if err != nil {
		panic(fmt.Sprintf("prepareTx: %v", err.Error()))
		return
	}
	if state == "" {
		doPrepareTx(ctx, &data)
		return
	}
	for key := "tx_" + data.TxId + ":state"; state == common.TxPreparing; {
		time.Sleep(10 * time.Millisecond)
		val, err := rdb.Get(ctx, key).Result()
		if err != nil {
			panic(fmt.Sprintf("prepareTx: %v", err.Error()))
		}
		state = common.TxState(val)
	}
	switch state {
	case common.TxAcknowledged, common.TxCommitted:
		ctx.Status(http.StatusOK)
		return
	case common.TxAborted:
		ctx.Status(http.StatusNotAcceptable)
		return
	default:
		panic(fmt.Sprintf("prepareTx: invalid state [%v]", state))
	}
}

func doPrepareTx(ctx *gin.Context, data *common.ItemTxPrepareRequest) {
	for i := range data.Items {
		itemId := data.Items[i].ItemId
		amount := data.Items[i].Amount
		stockKey := "item_" + itemId + ":stock"
		_, err := rIncrbyIfGe0XX.Run(ctx, rdb, []string{stockKey}, -amount).Result()
		if err == redis.Nil {
			// decr failed, rollback
			pipe := rdb.Pipeline()
			for j := i - 1; j >= 0; j-- {
				itemId := data.Items[j].ItemId
				amount := data.Items[j].Amount
				pipe.IncrBy(ctx, "item_"+itemId+":stock", int64(amount))
			}
			_, _ = pipe.Exec(ctx)
			state, _ := common.SwapTxStateXX(ctx, rdb, data.TxId, common.TxAborted)
			if state != common.TxPreparing {
				panic(fmt.Sprintf("doPrepareTx: invalid state [%v]", state))
			}
			ctx.Status(http.StatusNotAcceptable)
			return
		} else if err != nil {
			_, _ = common.SwapTxStateXX(ctx, rdb, data.TxId, common.TxAborted)
			ctx.String(http.StatusInternalServerError, "doPrepareTx: %v", err.Error())
			return
		}
	}
	// for rollback on aborting
	key := "tx_" + data.TxId + ":locked"
	pipe := rdb.Pipeline()
	for i := range data.Items {
		itemId := data.Items[i].ItemId
		amount := data.Items[i].Amount
		pipe.HSet(ctx, key, itemId, amount)
	}
	_, _ = pipe.Exec(ctx)
	state, _ := common.SwapTxStateXX(ctx, rdb, data.TxId, common.TxAcknowledged)
	if state != common.TxPreparing {
		panic(fmt.Sprintf("doPrepareTx: invalid state [%v]", state))
	}
	ctx.Status(http.StatusOK)
}

func commitTx(ctx *gin.Context) {
	txId := ctx.Param("tx_id")
	state, err := common.SwapTxStateXX(ctx, rdb, txId, common.TxCommitted)
	if err != nil {
		ctx.String(http.StatusBadRequest, "commitTx: ", err.Error())
		return
	}
	switch state {
	case common.TxAcknowledged:
		go func() { rdb.Del(context.Background(), "tx_"+txId+":locked") }()
		ctx.Status(http.StatusOK)
		return
	case common.TxCommitted:
		ctx.Status(http.StatusOK)
		return
	default:
		panic(fmt.Sprintf("commitTx: invalid state [%v]", state))
	}
}

func abortTx(ctx *gin.Context) {
	txId := ctx.Param("tx_id")
	state, err := common.SwapTxStateXX(ctx, rdb, txId, common.TxAborted)
	if err != nil {
		ctx.String(http.StatusBadRequest, "abortTx: ", err.Error())
		return
	}
	switch state {
	case common.TxAcknowledged:
		go rollbackTx("tx_" + txId + ":locked")
		ctx.Status(http.StatusOK)
		return
	case common.TxAborted:
		ctx.Status(http.StatusOK)
		return
	default:
		panic(fmt.Sprintf("abortTx: invalid state [%v]", state))
	}
}

func rollbackTx(stockKey string) {
	ctx := context.Background()
	for cursor := uint64(0); ; {
		keys, next, err := rdb.HScan(ctx, stockKey, cursor, "", 0).Result()
		if err != nil {
			panic(fmt.Sprintf("rollbackTx: %v", err.Error()))
		}
		n := len(keys)
		if n&1 != 0 {
			panic(fmt.Sprintf("rollbackTx: len error"))
		}
		pipe := rdb.Pipeline()
		for i := 0; i < n; i += 2 {
			itemId := keys[i]
			amount, err := strconv.ParseInt(keys[i+1], 10, 64)
			if err != nil {
				panic(fmt.Sprintf("rollbackTx: %v", err.Error()))
			}
			pipe.IncrBy(ctx, "item_"+itemId+":stock", amount)
		}
		_, _ = pipe.Exec(ctx)
		if next == 0 {
			break
		}
		cursor = next
	}
	rdb.Del(ctx, stockKey)
}
