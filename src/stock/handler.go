package stock

import (
	"github.com/gin-gonic/gin"
	"github.com/redis/go-redis/v9"
	"net/http"
	"strconv"
	"wdm/common"
)

func createItem(ctx *gin.Context) {
	priceStr := ctx.Param("price")
	price, err := strconv.Atoi(priceStr)
	if err != nil {
		ctx.String(http.StatusMethodNotAllowed, err.Error())
		return
	}
	itemId := snowGen.Next().String()

	pipe := rdb.TxPipeline()
	pipe.Set(ctx, "item_"+itemId+":price", price, 0)
	pipe.Set(ctx, "item_"+itemId+":stock", 0, 0)
	_, err = pipe.Exec(ctx)
	if err != nil {
		ctx.String(http.StatusInternalServerError, err.Error())
		return
	}

	ctx.JSON(http.StatusOK, common.CreateItemResponse{ItemId: itemId})
}

func findItem(ctx *gin.Context) {
	itemId := ctx.Param("item_id")

	pipe := rdb.TxPipeline()
	priceCmd := pipe.Get(ctx, "item_"+itemId+":price")
	stockCmd := pipe.Get(ctx, "item_"+itemId+":stock")
	_, _ = pipe.Exec(ctx)

	priceStr, err := priceCmd.Result()
	if err == redis.Nil {
		ctx.String(http.StatusNotFound, itemId)
		return
	} else if err != nil {
		ctx.String(http.StatusInternalServerError, err.Error())
		return
	}

	stockStr, err := stockCmd.Result()
	if err == redis.Nil {
		ctx.String(http.StatusNotFound, itemId)
		return
	} else if err != nil {
		ctx.String(http.StatusInternalServerError, err.Error())
		return
	}

	ctx.JSON(http.StatusOK, common.FindItemResponse{
		Price: common.MustS2I(priceStr),
		Stock: common.MustS2I(stockStr),
	})
}

func addStock(ctx *gin.Context) {
	itemId := ctx.Param("item_id")
	amountStr := ctx.Param("amount")
	amount, err := strconv.Atoi(amountStr)
	if err != nil {
		ctx.String(http.StatusMethodNotAllowed, err.Error())
		return
	}

	_, err = rIncrbyIfGe0XX.Run(ctx, rdb, []string{"item_" + itemId + ":stock"}, amount).Result()
	if err == redis.Nil {
		ctx.String(http.StatusBadRequest, itemId)
		return
	} else if err != nil {
		ctx.String(http.StatusInternalServerError, err.Error())
		return
	}

	ctx.Status(http.StatusOK)
}

func removeStock(ctx *gin.Context) {
	itemId := ctx.Param("item_id")
	amountStr := ctx.Param("amount")
	amount, err := strconv.Atoi(amountStr)
	if err != nil {
		ctx.String(http.StatusMethodNotAllowed, err.Error())
		return
	}

	_, err = rIncrbyIfGe0XX.Run(ctx, rdb, []string{"item_" + itemId + ":stock"}, -amount).Result()
	if err == redis.Nil {
		ctx.String(http.StatusBadRequest, itemId)
		return
	} else if err != nil {
		ctx.String(http.StatusInternalServerError, err.Error())
		return
	}

	ctx.Status(http.StatusOK)
}
