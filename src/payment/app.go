package payment

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

func Main() {
	gatewayUrl = common.MustGetEnv("GATEWAY_URL")

	snowGen = common.NewSnowFlakeGenerator(common.MustGetEnv("MACHINE_ID"))

	rdb = redis.NewClient(&redis.Options{
		Addr:     fmt.Sprintf("%v:%v", common.MustGetEnv("REDIS_HOST"), common.MustGetEnv("REDIS_PORT")),
		Password: common.MustGetEnv("REDIS_PASSWORD"),
		DB:       common.MustS2I(common.MustGetEnv("REDIS_DB")),
	})

	router := gin.New()
	common.DEffect(func() {
		router.Use(gin.Logger())
	})

	common.DEffect(func() {
		router.GET("/ping", func(ctx *gin.Context) {
			ctx.String(http.StatusOK, common.NowString()+" payment "+snowGen.Next().String())
		})

		router.DELETE("/drop-database", func(ctx *gin.Context) {
			rdb.FlushDB(ctx)
			ctx.Status(http.StatusOK)
		})
	})

	_ = router.Run("localhost:8080")
}
