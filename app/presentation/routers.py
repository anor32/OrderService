from fastapi import APIRouter, Response

from app.core.schemas import CreateOrderRequest, OrderResponse, PaymentRequest

router = APIRouter()


@router.get("/api/health", status_code=200)
async def health():
    return {"status": "ok"}


@router.post("/api/orders", status_code=201)
def create_order(data: CreateOrderRequest) -> OrderResponse:
    pass


@router.get("/api/orders/{order_id}", status_code=200)
def get_order(order_id) -> OrderResponse:
    pass


@router.post("/api/orders/payment-callback", status_code=200)
def callback_order(data: PaymentRequest):
    return Response(status_code=200)
