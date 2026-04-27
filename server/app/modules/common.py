from pydantic import BaseModel, ConfigDict


class ApiResponseModel(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class ErrorEnvelope(ApiResponseModel):
    error: dict
