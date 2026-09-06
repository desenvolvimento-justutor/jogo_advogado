from ninja_jwt.tokens import RefreshToken


def bearer_header(user) -> dict:
    """Retorna o header de Authorization com um access token JWT válido para o usuário."""
    token = RefreshToken.for_user(user).access_token
    return {"HTTP_AUTHORIZATION": f"Bearer {token}"}
