package common

import (
	"fmt"
	"time"
)

const debug = true

func DEffect(f func()) {
	if debug {
		f()
	}
}

func DLog(format string, a ...any) {
	if debug {
		str := fmt.Sprintf(format, a...)
		str = nowString() + str + "\n"
		fmt.Print(str)
	}
}

func nowString() string {
	now := time.Now()
	return fmt.Sprintf("[%02v:%02v:%03v]", now.Minute(), now.Second(), now.UnixMilli()%1000)
}
