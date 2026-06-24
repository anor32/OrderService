class WrongRequest(Exception):
    def __init__(
        self,
        message: str = "Не верно сформирован запрос",
        status_code: int = 400,
    ):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class ClientServerError(Exception):
    def __init__(
        self,
        message: str = "Внешний сервер клиента не доступен",
        status_code: int = 503,
    ):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)
