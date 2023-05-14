from typing import Optional, Union


def int_else_none(x: Union[str, bytes]) -> Optional[int]:
    try:
        i = int(x)
        return i
    except (ValueError, TypeError):
        return None
