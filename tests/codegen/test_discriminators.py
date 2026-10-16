from typing import Annotated, Literal

import pytest
from pydantic import Field, TypeAdapter, ValidationError, create_model

from fastapi_streams.codegen.python import generate_python
from tests.codegen.helpers import event_contract, load_models


@pytest.mark.parametrize("alias", ["event-type", "eventType", "class"])
def test_discriminator_uses_python_field_name_and_preserves_wire_alias(tmp_path, alias):
    first = create_model("First", kind=(Literal["first"], Field(alias=alias)))
    second = create_model("Second", kind=(Literal["second"], Field(alias=alias)))
    event = Annotated[first | second, Field(discriminator="kind")]
    files = generate_python(event_contract(event))
    with load_models(tmp_path, files) as models:
        adapter = TypeAdapter(models.EventsEvent)
        for value in ("first", "second"):
            parsed = adapter.validate_python({alias: value})
            assert parsed.model_dump(by_alias=True) == {alias: value}
        with pytest.raises(ValidationError):
            adapter.validate_python({alias: "unknown"})
