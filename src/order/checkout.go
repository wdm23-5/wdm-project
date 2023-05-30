package order

import (
	"github.com/gin-gonic/gin"
	"github.com/redis/go-redis/v9"
	"net/http"
)

func checkoutOrder(ctx *gin.Context) {
	// todo: use message queue to limit rate

	orderId := ctx.Param("order_id")
	txId := snowGen.Next().String()

	locked, info, err := prepareCkTx(ctx, orderId, txId)
	if err == redis.Nil {
		ctx.Status(http.StatusNotFound)
		return
	}
	if err != nil {
		ctx.String(http.StatusInternalServerError, "checkoutOrder: %v", err)
		return
	}

	if !locked {
		if info.paid {
			// already paid
			ctx.Status(http.StatusOK)
		} else {
			// concurrent checkout
			ctx.Status(http.StatusTooManyRequests)
		}
		return
	}

	// tx prepared

	if len(info.cart) == 0 {
		// empty cart. commit directly
		err := commitCkTx(ctx, orderId, txId)
		if err != nil {
			ctx.String(http.StatusInternalServerError, "checkoutOrder: %v", err)
			return
		}
		ctx.Status(http.StatusOK)
		return
	}

	// vvvvvv todo vvvvvvv

	cost, err := prepareStock(ctx, info, txId)
	if err != nil {
		ctx.String(http.StatusBadRequest, "prepareStock: %v", err)
		return
	}

	// todo: return directly after message queue ok

	ctx.Status(http.StatusOK)
}
