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
# CPF VARCHAR(11) PRIMARY KEY
# SENHA VARCHAR(12) NOT NULL UNIQUE
# E-MAIL VARCHAR(255) NOT NULL UNIQUE
# NOME VARCHAR(100) NOT NULL UNIQUE

SQLALCHEMY_DATABASE_URL = "mysql+pymysql://usuario:senha@localhost:3306/biblioteca"

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# =========================================================================
# ESTRUTURA DA ENTIDADE (Tabela)
# =========================================================================
class UsuarioEntity(Base):
    __tablename__ = "usuarios"

    # SUBSTITUIR QUANDO A TABELA ESTIVER FEITA
    # CPF VARCHAR(11) PRIMARY KEY
    # SENHA VARCHAR(12) NOT NULL UNIQUE
    # E-MAIL VARCHAR(255) NOT NULL UNIQUE
    # NOME VARCHAR(100) NOT NULL UNIQUE
    cpf = Column(String(11), primary_key=True)
    senha = Column(String(12), nullable=False)
    email = Column(String(255), nullable=False, unique=True)
    nome = Column(String(100), nullable=False, unique=True)


Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# =========================================================================
# ESQUEMAS DE VALIDAÇÃO (Pydantic para o Front-end)
# =========================================================================
class CadastroModel(BaseModel):
    # CPF VARCHAR(11) PRIMARY KEY
    # SENHA VARCHAR(12) NOT NULL UNIQUE
    # E-MAIL VARCHAR(255) NOT NULL UNIQUE
    # NOME VARCHAR(100) NOT NULL UNIQUE
    # TODO: Se tiver em formato de cpf, validar o cpf, senão, analisar se é matrícula.
    cpf: str
    senha: str
    email: EmailStr
    nome: str

    @field_validator("cpf")
    def validar_cpf_campo(cls, v):
        if not validar_cpf(v):
            raise ValueError("CPF inválido")
        return v

    @field_validator("senha")
    def validar_senha(cls, v):
        if len(v) > 12:
            raise ValueError("Senha deve ter no máximo 12 caracteres")
        return v


class LoginModel(BaseModel):
    # ACEITA CPF OU MATRICULA
    # CPF VARCHAR(11) PRIMARY KEY
    # SENHA VARCHAR(12) NOT NULL UNIQUE
    identificador: str
    senha: str

    @field_validator("identificador")
    def validar_identificador(cls, v):
        if is_cpf(v):
            if not validar_cpf(v):
                raise ValueError("CPF inválido")
        elif is_matricula(v):
            pass
        else:
            raise ValueError("Identificador deve ser um CPF ou matrícula válidos")
        return v


# =========================================================================
# FUNÇÕES DE SEGURANÇA
# =========================================================================

def verificar_senha(senha_fornecida: str, senha_cadastrada: str) -> bool:
    return senha_fornecida == senha_cadastrada

def validar_cpf(cpf: str) -> bool:
    # Remove pontos e traços (ex: "123.456.789-09" -> "12345678909")
    cpf = cpf.replace(".", "").replace("-", "")

    # Verifica se tem 11 dígitos e se não é uma sequência repetida (ex: "11111111111")
    if len(cpf) != 11 or cpf == cpf[0] * 11:
        return False

    # Valida o primeiro dígito verificador
    soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
    primeiro = (soma * 10 % 11) % 10
    if primeiro != int(cpf[9]):
        return False

    # Valida o segundo dígito verificador
    soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
    segundo = (soma * 10 % 11) % 10
    if segundo != int(cpf[10]):
        return False

    return True

def is_cpf(valor: str) -> bool:
    # CPF tem 11 dígitos (com ou sem formatação)
    return len(valor.replace(".", "").replace("-", "")) == 11

def is_matricula(valor: str) -> bool:
    # Ajuste a regra conforme o padrão de matrícula da sua universidade
    return valor.isdigit() and len(valor) == 10


# =========================================================================
# ROTAS DA API
# =========================================================================

@app.post("/cadastro", status_code=status.HTTP_201_CREATED)
def cadastrar_usuario(usuario: CadastroModel, db: Session = Depends(get_db)):
    # 1. Verifica se o CPF já existe
    usuario_existente_cpf = db.query(UsuarioEntity).filter(UsuarioEntity.cpf == usuario.cpf).first()
    if usuario_existente_cpf:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CPF já cadastrado no sistema."
        )

    # 2. Verifica se o E-mail já existe
    usuario_existente_email = db.query(UsuarioEntity).filter(UsuarioEntity.email == usuario.email).first()
    if usuario_existente_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Este e-mail já está sendo utilizado."
        )

    # 3. Transforma o modelo Pydantic na Entidade do Banco de Dados
    novo_usuario = UsuarioEntity(
        nome=usuario.nome,
        cpf=usuario.cpf,
        email=usuario.email,
        senha=usuario.senha
    )

    # 4. Salva no banco
    db.add(novo_usuario)
    db.commit()
    db.refresh(novo_usuario)

    return {"message": "Usuário cadastrado com sucesso!"}


@app.post("/login", status_code=status.HTTP_200_OK)
def login_usuario(credenciais: LoginModel, db: Session = Depends(get_db)):
    # Busca o usuário pelo CPF ou matrícula
    usuario = db.query(UsuarioEntity).filter(UsuarioEntity.cpf == credenciais.identificador).first()

    # Se não encontrar ou a senha não bater
    if not usuario or not verificar_senha(credenciais.senha, usuario.senha):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="CPF/Matrícula ou senha incorretos."
        )

    return {
        "message": "Login realizado com sucesso!",
        "usuario": {
            "nome": usuario.nome,
            "email": usuario.email
        }
    }


@app.get("/")
def home():
    return {"status": "API Campus conectada ao banco de dados"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)