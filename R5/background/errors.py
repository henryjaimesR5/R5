class BackgroundError(Exception):
    message = "Background error occurred"

    def __init__(self):
        super().__init__(self.message)


class BackgroundDisabledError(BackgroundError):
    message = "Background disabled"
