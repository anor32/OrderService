class ObjectNotFound(Exception):
    def __init__(self, message: str = "Объект не найден"):
        self.message = message
        super().__init__(self.message)


class IdempotencyError(Exception):
    def __init__(self, message: str = "Ошибка идемпотентности"):
        self.message = message
        super().__init__(self.message)


class NotEnoughStockError(Exception):
    def __init__(
        self, message: str = "количество товара на складе не достаточно"
    ):
        self.message = message
        super().__init__(self.message)
