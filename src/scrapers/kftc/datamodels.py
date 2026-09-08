from pydantic import BaseModel, SecretStr


class KftcLoginCredential(BaseModel):
    username: str
    password: SecretStr
