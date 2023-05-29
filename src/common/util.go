package common

import (
	"os"
	"strconv"
)

func MustS2I(s string) int {
	i, e := strconv.Atoi(s)
	if e != nil {
		panic("MustS2I not int " + s)
	}
	return i
}

func MustGetEnv(key string) string {
	val, ok := os.LookupEnv(key)
	if !ok || val == "" {
		panic("MustGetEnv not exist " + key)
	}
	return val
}
