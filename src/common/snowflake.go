package common

import (
	"fmt"
	"runtime"
	"sync/atomic"
	"time"
)

// distributed id generator

const wdmEpoch int64 = 1672531200000 // time.Date(2023, time.January, 1, 0, 0, 0, 0, time.UTC).UnixMilli()

// modified id generator based on Twitter Snowflake
type SnowflakeGenerator struct {
	lock      SpinLock
	timestamp int64
	machineId uint16
	sequence  uint16
}

func NewSnowFlakeGenerator(machineId string) *SnowflakeGenerator {
	return &SnowflakeGenerator{
		timestamp: time.Now().UnixMilli() - wdmEpoch,
		machineId: uint16(MustS2I(machineId)),
		sequence:  0,
	}
}

func (sg *SnowflakeGenerator) Next() SnowflakeID {
	sg.lock.Lock()
	defer sg.lock.Unlock()
	timestamp := time.Now().UnixMilli() - wdmEpoch
	if timestamp < sg.timestamp {
		panic("clock moves backwards")
	}
	if timestamp == sg.timestamp {
		sg.sequence = sg.sequence + 1
		if sg.sequence == 0 {
			for timestamp <= sg.timestamp {
				timestamp = time.Now().UnixMilli() - wdmEpoch
			}
		}
	} else {
		sg.sequence = 0
	}
	sg.timestamp = timestamp
	return SnowflakeID{timestamp: sg.timestamp, machineId: sg.machineId, sequence: sg.sequence}
}

type SnowflakeID struct {
	timestamp int64
	machineId uint16
	sequence  uint16
}

// since redis stores int as string, this implementation directly uses string as id
func (sid SnowflakeID) String() string {
	return fmt.Sprintf("t%vm%vs%v", sid.timestamp, sid.machineId, sid.sequence)
}

// spin lock

type SpinLock struct {
	locked atomic.Int32
}

func (sl *SpinLock) Lock() {
	for !sl.locked.CompareAndSwap(0, 1) {
		runtime.Gosched()
	}
}

func (sl *SpinLock) Unlock() {
	if val := sl.locked.Add(-1); val != 0 {
		panic("SpinLock double unlock")
	}
}
