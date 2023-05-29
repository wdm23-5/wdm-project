package stock

import (
	"fmt"
	"github.com/gin-gonic/gin"
	"github.com/redis/go-redis/v9"
	"net/http"
	"wdm/common"
)

var gatewayUrl string
var snowGen *common.SnowflakeGenerator
var rdb *redis.Client
var rIncrbyIfGe0XX *redis.Script

func main() {
	gatewayUrl = common.MustGetEnv("GATEWAY_URL")

	snowGen = common.NewSnowFlakeGenerator(common.MustGetEnv("MACHINE_ID"))

	rdb = redis.NewClient(&redis.Options{
		Addr:     fmt.Sprintf("%v:%v", common.MustGetEnv("REDIS_HOST"), common.MustGetEnv("REDIS_PORT")),
		Password: common.MustGetEnv("REDIS_PASSWORD"),
		DB:       common.MustS2I(common.MustGetEnv("REDIS_DB")),
	})
	rIncrbyIfGe0XX = redis.NewScript(common.LuaIncrbyIfGe0XX)

	router := gin.New()
	common.DEffect(func() {
		router.Use(gin.Logger())
	})

	router.POST("/item/create/:price", createItem)
	router.GET("/find/:item_id", findItem)
	router.POST("/add/:item_id/:amount", addStock)
	router.POST("/subtract/:item_id/:amount", removeStock)

	router.POST("/tx/prepare/:tx_id", prepareTx)
	router.POST("/tx/commit/:tx_id", commitTx)
	router.POST("/tx/abort/:tx_id", abortTx)

	common.DEffect(func() {
		router.DELETE("/drop-database", func(ctx *gin.Context) {
			rdb.FlushDB(ctx)
			ctx.Status(http.StatusOK)
		})
	})

	_ = router.Run("localhost:8080")
}
