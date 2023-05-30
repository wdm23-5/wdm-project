FROM golang:1.19

WORKDIR /home/order-service

COPY common common
COPY main/order.go main/order.go
COPY order order
COPY go.mod go.sum ./

RUN go build -v -o order-app main/order.go

EXPOSE 5000
