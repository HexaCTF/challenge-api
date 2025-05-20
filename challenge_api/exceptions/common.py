from typing import Any

class CommonException(Exception):
    def __init__(self, error_msg: str):
        super().__setattr__('error_msg', error_msg)

    def __str__(self):
        return f"{self.__class__.__name__}: {self.__dict__}"

class EmptyValueException(CommonException):
    def __init__(self, error_msg: str):
        super().__init__(error_msg)
        super().__setattr__('_attributes', {})

    def __getattr__(self, name: str) -> Any:
        try:
            return self._attributes[name]
        except KeyError:
            raise AttributeError(f"{name} not found in attributes")

    def __setattr__(self, name: str, value: Any) -> None:
        if name in ('error_msg', '_attributes'):
            super().__setattr__(name, value)
        else:
            self._attributes[name] = value

    def __delattr__(self, name: str) -> None:
        if name in self._attributes:
            del self._attributes[name]
        else:
            super().__delattr__(name)

    def __str__(self):
        return f"{self.__class__.__name__}: {self._attributes}"
