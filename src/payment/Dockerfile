FROM golang:1.19

WORKDIR /home/payment-service

COPY common common
COPY main/payment.go main/payment.go
COPY payment payment
COPY go.mod go.sum ./

RUN go build -v -o payment-app main/payment.go

EXPOSE 5000
