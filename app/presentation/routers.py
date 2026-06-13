from fastapi import APIRouter, Response

from app.core.schemas import CreateOrderRequest, OrderResponse, PaymentRequest
from app.presentation.dependecies import DepOrderService

router = APIRouter()


@router.get("/api/health", status_code=200)
async def health():
    return {"status": "ok"}


@router.post("/api/orders", status_code=201)
async def create_order(
    request_data: CreateOrderRequest, service: DepOrderService
) -> OrderResponse:
    order = await service.create_order(request_data)
    resp = OrderResponse(**order.model_dump())
    return resp


@router.get("/api/orders/{order_id}", status_code=200)
def get_order(order_id) -> OrderResponse:
    pass


@router.post("/api/orders/payment-callback", status_code=200)
def callback_order(data: PaymentRequest):
    return Response(status_code=200)
