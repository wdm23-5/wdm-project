package common

type CreateOrderResponse struct {
	OrderId string `json:"order_id"`
}

type FindOrderResponse struct {
	OrderId   string   `json:"order_id"`
	Paid      bool     `json:"paid"`
	Items     []string `json:"items"`
	UserId    string   `json:"user_id"`
	TotalCost int      `json:"total_cost"`
}

type CreateItemResponse struct {
	ItemId string `json:"item_id"`
}

type FindItemResponse struct {
	Price int `json:"price"`
	Stock int `json:"stock"`
}

type ItemTxPrepareRequest struct {
	TxId  string `json:"tx_id"`
	Items []struct {
		ItemId string `json:"item_id"`
		Amount int    `json:"amount"`
	} `json:"items"`
}

type CreditTxPrepareRequest struct {
	TxId   string `json:"tx_id"`
	Credit int    `json:"credit"`
}
