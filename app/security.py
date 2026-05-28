from fastapi.security import OAuth2PasswordBearer

auth = OAuth2PasswordBearer(tokenUrl="people/auth")
