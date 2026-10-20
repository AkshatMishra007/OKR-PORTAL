from typing import Annotated

from pydantic import StringConstraints

NonEmptyStr = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=1,
    ),
]

UsernameStr = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=3,
        max_length=50,
    ),
]

PasswordStr = Annotated[
    str,
    StringConstraints(
        min_length=8,
        max_length=128,
    ),
]
