package common

import (
	"fmt"
	"github.com/gin-gonic/gin"
	"github.com/redis/go-redis/v9"
)

type TxState string

const (
	TxPreparing    TxState = "PRP"
	TxAcknowledged TxState = "ACK"
	TxCommitted    TxState = "CMT"
	TxAborted      TxState = "ABT"
)

func KeyTxState(txId string) string {
	return "tx_" + txId + ":state"
}

// not strictly atomic. panic on error if needed
func InitTxStateNX(ctx *gin.Context, rdb *redis.Client, txId string) (TxState, error) {
	key := KeyTxState(txId)
	val, err := rdb.Do(ctx, "SET", key, TxPreparing, "NX", "GET").Result()
	if err == redis.Nil {
		// not previously set, new tx
		return "", nil
	}
	if err != nil {
		return "", err
	}
	// there is a previous value
	str, ok := val.(string)
	if !ok {
		return "", fmt.Errorf("InitTxStateNX: [%v] is not string", val)
	}
	return TxState(str), nil
}

// not strictly atomic. panic on error if needed
func SwapTxStateXX(ctx *gin.Context, rdb *redis.Client, txId string, newState TxState) (TxState, error) {
	key := "tx_" + txId + ":state"
	val, err := rdb.Do(ctx, "SET", key, string(newState), "XX", "GET").Result()
	if err != nil {
		// including err == redis.Nil
		return "", err
	}
	str, ok := val.(string)
	if !ok {
		return "", fmt.Errorf("SwapTxStateXX: [%v] is not string", val)
	}
	return TxState(str), nil
}
