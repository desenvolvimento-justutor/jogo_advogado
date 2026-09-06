from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404
from ninja import Router
from ninja.errors import HttpError
from ninja_jwt.authentication import JWTAuth

from .models import InstituicaoEnsino, Perfil
from .schemas import CadastroIn, InstituicaoOut, PerfilOut, PerfilUpdateIn

router = Router(tags=["contas"])

User = get_user_model()


@router.post("/cadastro/", response={201: PerfilOut})
def cadastrar(request, payload: CadastroIn):
    try:
        with transaction.atomic():
            user = User.objects.create_user(
                username=payload.username, email=payload.email, password=payload.password
            )
            perfil = Perfil.objects.create(
                usuario=user,
                nome_jogador=payload.nome_jogador,
                instituicao_id=payload.instituicao_id,
            )
    except IntegrityError:
        raise HttpError(400, "Nome de usuário ou e-mail já cadastrado.")
    return 201, perfil


@router.get("/instituicoes/", response=list[InstituicaoOut])
def listar_instituicoes(request, estado: str = None):
    qs = InstituicaoEnsino.objects.all()
    if estado:
        qs = qs.filter(estado=estado.upper())
    return list(qs)


@router.get("/perfil/me/", response=PerfilOut, auth=JWTAuth())
def meu_perfil(request):
    perfil = get_object_or_404(Perfil, usuario=request.user)
    return perfil


@router.patch("/perfil/me/", response=PerfilOut, auth=JWTAuth())
def atualizar_meu_perfil(request, payload: PerfilUpdateIn):
    perfil = get_object_or_404(Perfil, usuario=request.user)
    for campo, valor in payload.dict(exclude_unset=True).items():
        setattr(perfil, campo, valor)
    perfil.save()
    return perfil
