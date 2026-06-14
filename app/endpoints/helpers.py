from typing import Any
from pydantic import BaseModel, ValidationError

def do_patch_validation(value: dict[str, Any], clazz: type[BaseModel]) -> dict[str, Any]:
    """
    Performs the Pydantic validation for the given value BUT discards any 'missing' error types
    as that is to be expected from a PATCH.

    :param value:
    :param clazz:
    :return: the supplied value
    """
    try:
        clazz.model_validate(value) # https://pydantic.dev/docs/validation/latest/concepts/models/
    except ValidationError as ex:
        errors = [e for e in ex.errors() if e.get("type", "missing") != "missing"]
        if errors:
            raise ValidationError.from_exception_data(title="Patch Error", line_errors=errors)

    return value