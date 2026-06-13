import os
from fastapi import FastAPI, HTTPException, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
from datetime import date

from sqlalchemy import create_engine, Column, String, Integer, Date, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

app = FastAPI(
    title="Campus API",
    description="API do Sistema de Biblioteca Campus",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================================================================
# BANCO DE DADOS
# Localmente usa a variável de ambiente DATABASE_URL se existir,
# senão cai no freesqldatabase. No Render, configure DATABASE_URL
# nas Environment Variables do serviço.
# =========================================================================
SQLALCHEMY_DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "mysql+pymysql://sql10830296:FCveFXdEL9@sql10.freesqldatabase.com:3306/sql10830296"
)

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# =========================================================================
# ENTIDADES
# =========================================================================
class UsuarioEntity(Base):
    __tablename__ = "USUARIOS"
    cpf        = Column(String(11),  primary_key=True, name="CPF_MATRICULA")
    senha      = Column(String(12),  nullable=False,   name="SENHA")
    email      = Column(String(255), nullable=False, unique=True, name="E_MAIL")
    nome       = Column(String(100), nullable=False, unique=True, name="NOME")
    tipo       = Column(String(10),  nullable=False,   name="TIPO")


class LivroEntity(Base):
    __tablename__ = "LIVROS"
    id          = Column(Integer,     primary_key=True, autoincrement=True, name="ID")
    titulo      = Column(String(200), nullable=False,   name="TITULO")
    autor       = Column(String(150), nullable=False,   name="AUTOR")
    categoria   = Column(String(100), nullable=False,   name="CATEGORIA")
    isbn        = Column(String(20),  nullable=True, unique=True, name="ISBN")
    copias      = Column(Integer,     nullable=False, default=1, name="COPIAS")
    disponiveis = Column(Integer,     nullable=False, default=1, name="DISPONIVEIS")


class EmprestimoEntity(Base):
    __tablename__ = "EMPRESTIMOS"
    id                     = Column(Integer,     primary_key=True, autoincrement=True, name="ID")
    cpf_aluno              = Column(String(11),  nullable=False, name="CPF_ALUNO")
    id_livro               = Column(Integer,     nullable=False, name="ID_LIVRO")
    data_solicitacao       = Column(Date,        nullable=False, name="DATA_SOLICITACAO")
    data_devolucao_prevista = Column(Date,       nullable=True,  name="DATA_DEVOLUCAO_PREVISTA")
    data_devolucao_real    = Column(Date,        nullable=True,  name="DATA_DEVOLUCAO_REAL")
    status                 = Column(String(20),  nullable=False, default="pendente", name="STATUS")


class MensagemEntity(Base):
    __tablename__ = "MENSAGENS"
    id           = Column(Integer,     primary_key=True, autoincrement=True, name="ID")
    cpf_remetente = Column(String(11), nullable=False,  name="CPF_REMETENTE")
    nome_remetente = Column(String(100), nullable=False, name="NOME_REMETENTE")
    tipo_remetente = Column(String(10),  nullable=False, name="TIPO_REMETENTE")
    mensagem     = Column(Text,         nullable=False,  name="MENSAGEM")
    resposta     = Column(Text,         nullable=True,   name="RESPOSTA")
    data_envio   = Column(Date,         nullable=False,  name="DATA_ENVIO")


Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# =========================================================================
# MODELOS
# =========================================================================
class CadastroModel(BaseModel):
    cpf: str
    senha: str
    email: EmailStr
    nome: str
    tipo: str

    @field_validator("cpf")
    def validar_cpf_campo(cls, v):
        v = v.replace(".", "").replace("-", "")
        if not validar_cpf(v):
            raise ValueError("CPF inválido")
        return v

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
        v = v.replace(".", "").replace("-", "")
        if is_cpf(v):
            if not validar_cpf(v):
                raise ValueError("CPF inválido")
        elif is_matricula(v):
            pass
        else:
            raise ValueError("Identificador inválido")
        return v


class LivroModel(BaseModel):
    titulo: str
    autor: str
    categoria: str
    isbn: Optional[str] = None
    copias: int = 1


class EmprestimoModel(BaseModel):
    cpf_aluno: str
    id_livro: int


class AceitarEmprestimoModel(BaseModel):
    data_devolucao_prevista: date


class MensagemModel(BaseModel):
    cpf_remetente: str
    nome_remetente: str
    tipo_remetente: str
    mensagem: str


class RespostaModel(BaseModel):
    resposta: str


# =========================================================================
# FUNÇÕES AUXILIARES
# =========================================================================
def verificar_senha(s1, s2): return s1 == s2

def validar_cpf(cpf: str) -> bool:
    cpf = cpf.replace(".", "").replace("-", "")
    if len(cpf) != 11 or cpf == cpf[0] * 11: return False
    soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
    if (soma * 10 % 11) % 10 != int(cpf[9]): return False
    soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
    return (soma * 10 % 11) % 10 == int(cpf[10])

def is_cpf(v): return len(v.replace(".", "").replace("-", "")) == 11
def is_matricula(v): return v.isdigit() and len(v) == 10


# =========================================================================
# ROTAS — USUÁRIOS
# =========================================================================
@app.post("/cadastro", status_code=201)
def cadastrar_usuario(usuario: CadastroModel, db: Session = Depends(get_db)):
    if db.query(UsuarioEntity).filter(UsuarioEntity.cpf == usuario.cpf).first():
        raise HTTPException(400, "CPF já cadastrado.")
    if db.query(UsuarioEntity).filter(UsuarioEntity.email == usuario.email).first():
        raise HTTPException(400, "E-mail já utilizado.")
    db.add(UsuarioEntity(nome=usuario.nome, cpf=usuario.cpf,
                         email=usuario.email, senha=usuario.senha, tipo=usuario.tipo))
    db.commit()
    return {"message": "Usuário cadastrado com sucesso!"}


@app.post("/login")
def login_usuario(credenciais: LoginModel, db: Session = Depends(get_db)):
    u = db.query(UsuarioEntity).filter(UsuarioEntity.cpf == credenciais.identificador).first()
    if not u or not verificar_senha(credenciais.senha, u.senha):
        raise HTTPException(401, "CPF/Matrícula ou senha incorretos.")
    return {"message": "Login realizado!", "usuario": {"nome": u.nome, "email": u.email, "tipo": u.tipo, "cpf": u.cpf}}


@app.get("/usuarios")
def listar_usuarios(db: Session = Depends(get_db)):
    usuarios = db.query(UsuarioEntity).all()
    return [{"cpf": u.cpf, "nome": u.nome, "email": u.email, "tipo": u.tipo} for u in usuarios]


# =========================================================================
# ROTAS — LIVROS
# =========================================================================
@app.post("/livros", status_code=201)
def cadastrar_livro(livro: LivroModel, db: Session = Depends(get_db)):
    if livro.isbn and db.query(LivroEntity).filter(LivroEntity.isbn == livro.isbn).first():
        raise HTTPException(400, "ISBN já cadastrado.")
    novo = LivroEntity(titulo=livro.titulo, autor=livro.autor, categoria=livro.categoria,
                       isbn=livro.isbn, copias=livro.copias, disponiveis=livro.copias)
    db.add(novo)
    db.commit()
    db.refresh(novo)
    return {"message": "Livro cadastrado!", "id": novo.id}


@app.get("/livros")
def listar_livros(db: Session = Depends(get_db)):
    return [{"id": l.id, "titulo": l.titulo, "autor": l.autor, "categoria": l.categoria,
             "isbn": l.isbn, "copias": l.copias, "disponiveis": l.disponiveis,
             "status": "Disponível" if l.disponiveis > 0 else "Indisponível"} for l in db.query(LivroEntity).all()]


@app.delete("/livros/{livro_id}")
def deletar_livro(livro_id: int, db: Session = Depends(get_db)):
    l = db.query(LivroEntity).filter(LivroEntity.id == livro_id).first()
    if not l: raise HTTPException(404, "Livro não encontrado.")
    db.delete(l)
    db.commit()
    return {"message": "Livro removido!"}


# =========================================================================
# ROTAS — EMPRÉSTIMOS
# =========================================================================
@app.post("/emprestimos", status_code=201)
def solicitar_emprestimo(emp: EmprestimoModel, db: Session = Depends(get_db)):
    livro = db.query(LivroEntity).filter(LivroEntity.id == emp.id_livro).first()
    if not livro: raise HTTPException(404, "Livro não encontrado.")
    if livro.disponiveis < 1: raise HTTPException(400, "Livro indisponível.")

    ja_existe = db.query(EmprestimoEntity).filter(
        EmprestimoEntity.cpf_aluno == emp.cpf_aluno,
        EmprestimoEntity.id_livro == emp.id_livro,
        EmprestimoEntity.status.in_(["pendente", "ativo"])
    ).first()
    if ja_existe: raise HTTPException(400, "Você já tem uma solicitação ativa para este livro.")

    db.add(EmprestimoEntity(cpf_aluno=emp.cpf_aluno, id_livro=emp.id_livro,
                             data_solicitacao=date.today(), status="pendente"))
    db.commit()
    return {"message": "Solicitação de empréstimo enviada!"}


@app.get("/emprestimos")
def listar_emprestimos(db: Session = Depends(get_db)):
    emps = db.query(EmprestimoEntity).all()
    resultado = []
    for e in emps:
        u = db.query(UsuarioEntity).filter(UsuarioEntity.cpf == e.cpf_aluno).first()
        l = db.query(LivroEntity).filter(LivroEntity.id == e.id_livro).first()
        resultado.append({
            "id": e.id,
            "cpf_aluno": e.cpf_aluno,
            "nome_aluno": u.nome if u else "—",
            "id_livro": e.id_livro,
            "titulo_livro": l.titulo if l else "—",
            "autor_livro": l.autor if l else "—",
            "data_solicitacao": str(e.data_solicitacao),
            "data_devolucao_prevista": str(e.data_devolucao_prevista) if e.data_devolucao_prevista else None,
            "data_devolucao_real": str(e.data_devolucao_real) if e.data_devolucao_real else None,
            "status": e.status
        })
    return resultado


@app.get("/emprestimos/usuario/{cpf}")
def emprestimos_do_usuario(cpf: str, db: Session = Depends(get_db)):
    emps = db.query(EmprestimoEntity).filter(EmprestimoEntity.cpf_aluno == cpf).all()
    resultado = []
    for e in emps:
        l = db.query(LivroEntity).filter(LivroEntity.id == e.id_livro).first()
        resultado.append({
            "id": e.id,
            "id_livro": e.id_livro,
            "titulo_livro": l.titulo if l else "—",
            "autor_livro": l.autor if l else "—",
            "data_solicitacao": str(e.data_solicitacao),
            "data_devolucao_prevista": str(e.data_devolucao_prevista) if e.data_devolucao_prevista else None,
            "status": e.status
        })
    return resultado


@app.put("/emprestimos/{emp_id}/aceitar")
def aceitar_emprestimo(emp_id: int, body: AceitarEmprestimoModel, db: Session = Depends(get_db)):
    e = db.query(EmprestimoEntity).filter(EmprestimoEntity.id == emp_id).first()
    if not e: raise HTTPException(404, "Empréstimo não encontrado.")
    if e.status != "pendente": raise HTTPException(400, "Empréstimo não está pendente.")
    livro = db.query(LivroEntity).filter(LivroEntity.id == e.id_livro).first()
    if livro: livro.disponiveis -= 1
    e.status = "ativo"
    e.data_devolucao_prevista = body.data_devolucao_prevista
    db.commit()
    return {"message": "Empréstimo aceito!"}


@app.put("/emprestimos/{emp_id}/rejeitar")
def rejeitar_emprestimo(emp_id: int, db: Session = Depends(get_db)):
    e = db.query(EmprestimoEntity).filter(EmprestimoEntity.id == emp_id).first()
    if not e: raise HTTPException(404, "Empréstimo não encontrado.")
    if e.status != "pendente": raise HTTPException(400, "Empréstimo não está pendente.")
    e.status = "rejeitado"
    db.commit()
    return {"message": "Empréstimo rejeitado."}


@app.put("/emprestimos/{emp_id}/devolver")
def devolver_emprestimo(emp_id: int, db: Session = Depends(get_db)):
    e = db.query(EmprestimoEntity).filter(EmprestimoEntity.id == emp_id).first()
    if not e: raise HTTPException(404, "Empréstimo não encontrado.")
    if e.status != "ativo": raise HTTPException(400, "Empréstimo não está ativo.")
    livro = db.query(LivroEntity).filter(LivroEntity.id == e.id_livro).first()
    if livro: livro.disponiveis += 1
    e.status = "devolvido"
    e.data_devolucao_real = date.today()
    db.commit()
    return {"message": "Devolução registrada!"}


# =========================================================================
# ROTAS — MENSAGENS (CHAT)
# =========================================================================
@app.post("/mensagens", status_code=201)
def enviar_mensagem(msg: MensagemModel, db: Session = Depends(get_db)):
    db.add(MensagemEntity(
        cpf_remetente=msg.cpf_remetente,
        nome_remetente=msg.nome_remetente,
        tipo_remetente=msg.tipo_remetente,
        mensagem=msg.mensagem,
        data_envio=date.today()
    ))
    db.commit()
    return {"message": "Mensagem enviada!"}


@app.get("/mensagens")
def listar_mensagens(db: Session = Depends(get_db)):
    msgs = db.query(MensagemEntity).order_by(MensagemEntity.id.desc()).all()
    return [{
        "id": m.id,
        "cpf_remetente": m.cpf_remetente,
        "nome_remetente": m.nome_remetente,
        "tipo_remetente": m.tipo_remetente,
        "mensagem": m.mensagem,
        "resposta": m.resposta,
        "data_envio": str(m.data_envio)
    } for m in msgs]


@app.get("/mensagens/usuario/{cpf}")
def mensagens_do_usuario(cpf: str, db: Session = Depends(get_db)):
    msgs = db.query(MensagemEntity).filter(MensagemEntity.cpf_remetente == cpf).order_by(MensagemEntity.id).all()
    return [{
        "id": m.id,
        "mensagem": m.mensagem,
        "resposta": m.resposta,
        "data_envio": str(m.data_envio)
    } for m in msgs]


@app.put("/mensagens/{msg_id}/responder")
def responder_mensagem(msg_id: int, body: RespostaModel, db: Session = Depends(get_db)):
    m = db.query(MensagemEntity).filter(MensagemEntity.id == msg_id).first()
    if not m: raise HTTPException(404, "Mensagem não encontrada.")
    m.resposta = body.resposta
    db.commit()
    return {"message": "Resposta enviada!"}


@app.get("/")
def home():
    return {"status": "API Campus online"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", 8000)), reload=True)
