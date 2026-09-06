from django.contrib.auth import authenticate
from ninja import Router, Schema
from ninja.errors import HttpError
from ninja_jwt.tokens import RefreshToken

router = Router(tags=["auth"])


class LoginIn(Schema):
    username: str
    password: str


class TokenOut(Schema):
    access: str
    refresh: str


class RefreshIn(Schema):
    refresh: str


class AccessOut(Schema):
    access: str


@router.post("/login/", response=TokenOut)
def login(request, payload: LoginIn):
    user = authenticate(request, username=payload.username, password=payload.password)
    if user is None:
        raise HttpError(401, "Usuário ou senha inválidos.")
    refresh = RefreshToken.for_user(user)
    return TokenOut(access=str(refresh.access_token), refresh=str(refresh))


@router.post("/refresh/", response=AccessOut)
def refresh_token(request, payload: RefreshIn):
    try:
        refresh = RefreshToken(payload.refresh)
    except Exception:
        raise HttpError(401, "Token de refresh inválido ou expirado.")
    return AccessOut(access=str(refresh.access_token))
