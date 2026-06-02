from fastapi import FastAPI, HTTPException, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, field_validator

from sqlalchemy import create_engine, Column, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

app = FastAPI(
    title="Campus API - MySQL",
    description="API com suporte a banco de dados MySQL para o sistema do Campus",
    version="1.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================================================================
# CONFIGURAÇÃO DO BANCO DE DADOS
# =========================================================================
# Troque SUA_SENHA pela senha do usuário igor que você criou
SQLALCHEMY_DATABASE_URL = "mysql+pymysql://igor:1234@localhost:3306/DADOS_CADASTRADOS"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# =========================================================================
# ESTRUTURA DA TABELA
# =========================================================================
class UsuarioEntity(Base):
    __tablename__ = "USUARIOS"

    cpf = Column(String(11), primary_key=True, name="CPF_MATRICULA")
    senha = Column(String(12), nullable=False, name="SENHA")
    email = Column(String(255), nullable=False, unique=True, name="E_MAIL")
    nome = Column(String(100), nullable=False, unique=True, name="NOME")
    tipo = Column(String(10), nullable=False, name="TIPO")


Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# =========================================================================
# ESQUEMAS DE VALIDAÇÃO
# =========================================================================
class CadastroModel(BaseModel):
    cpf: str
    senha: str
    email: EmailStr
    nome: str
    tipo: str  # 'aluno' ou 'professor'

    @field_validator("cpf")
    def validar_cpf_campo(cls, v):
        v = v.replace(".", "").replace("-", "")  # limpa a formatação
        if not validar_cpf(v):
            raise ValueError("CPF inválido")
        return v  # retorna o CPF limpo (só números)

    @field_validator("senha")
    def validar_senha(cls, v):
        if len(v) > 12:
            raise ValueError("Senha deve ter no máximo 12 caracteres")
        return v

    @field_validator("tipo")
    def validar_tipo(cls, v):
        if v not in ("aluno", "professor"):
            raise ValueError("Tipo deve ser 'aluno' ou 'professor'")
        return v


class LoginModel(BaseModel):
    identificador: str
    senha: str

    @field_validator("identificador")
    def validar_identificador(cls, v):
        v = v.replace(".", "").replace("-", "")  # limpa a formatação
        if is_cpf(v):
            if not validar_cpf(v):
                raise ValueError("CPF inválido")
        elif is_matricula(v):
            pass
        else:
            raise ValueError("Identificador deve ser um CPF ou matrícula válidos")
        return v  # retorna limpo


# =========================================================================
# FUNÇÕES DE SEGURANÇA
# =========================================================================

def verificar_senha(senha_fornecida: str, senha_cadastrada: str) -> bool:
    return senha_fornecida == senha_cadastrada

def validar_cpf(cpf: str) -> bool:
    cpf = cpf.replace(".", "").replace("-", "")
    if len(cpf) != 11 or cpf == cpf[0] * 11:
        return False
    soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
    primeiro = (soma * 10 % 11) % 10
    if primeiro != int(cpf[9]):
        return False
    soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
    segundo = (soma * 10 % 11) % 10
    if segundo != int(cpf[10]):
        return False
    return True

def is_cpf(valor: str) -> bool:
    return len(valor.replace(".", "").replace("-", "")) == 11

def is_matricula(valor: str) -> bool:
    return valor.isdigit() and len(valor) == 10


# =========================================================================
# ROTAS DA API
# =========================================================================

@app.post("/cadastro", status_code=status.HTTP_201_CREATED)
def cadastrar_usuario(usuario: CadastroModel, db: Session = Depends(get_db)):
    if db.query(UsuarioEntity).filter(UsuarioEntity.cpf == usuario.cpf).first():
        raise HTTPException(status_code=400, detail="CPF já cadastrado no sistema.")

    if db.query(UsuarioEntity).filter(UsuarioEntity.email == usuario.email).first():
        raise HTTPException(status_code=400, detail="Este e-mail já está sendo utilizado.")

    novo_usuario = UsuarioEntity(
        nome=usuario.nome,
        cpf=usuario.cpf,
        email=usuario.email,
        senha=usuario.senha,
        tipo=usuario.tipo
    )

    db.add(novo_usuario)
    db.commit()
    db.refresh(novo_usuario)

    return {"message": "Usuário cadastrado com sucesso!"}


@app.post("/login", status_code=status.HTTP_200_OK)
def login_usuario(credenciais: LoginModel, db: Session = Depends(get_db)):
    usuario = db.query(UsuarioEntity).filter(UsuarioEntity.cpf == credenciais.identificador).first()

    if not usuario or not verificar_senha(credenciais.senha, usuario.senha):
        raise HTTPException(status_code=401, detail="CPF/Matrícula ou senha incorretos.")

    return {
        "message": "Login realizado com sucesso!",
        "usuario": {
            "nome": usuario.nome,
            "email": usuario.email,
            "tipo": usuario.tipo
        }
    }


@app.get("/")
def home():
    return {"status": "API Campus conectada ao banco de dados"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
