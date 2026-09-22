"""
MathAI - Gerenciamento de Usuários (Auth & Faturamento)
Cadastro, login, perfil motivacional, dados de faturamento (CPF, CEP, Endereço)
e Verificação em Duas Etapas (2FA / OTP).
"""

import hashlib
import json
import random
import os
import re
import secrets
from datetime import datetime, timedelta
import requests
from src.database.db import pegar_conexao


def _hash_senha(senha: str) -> str:
    return hashlib.sha256(senha.encode("utf-8")).hexdigest()


def _garantir_tabelas_e_migracao():
    """Garante que as tabelas e colunas novas existam no SQLite."""
    con = pegar_conexao()
    cur = con.cursor()

    # 1. Tabela usuarios base
    cur.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            senha_hash TEXT NOT NULL,
            idade INTEGER,
            celular TEXT,
            motivos TEXT,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Migrações automáticas de colunas para bancos existentes
    novas_colunas = [
        ("cpf", "TEXT"),
        ("cep", "TEXT"),
        ("logradouro", "TEXT"),
        ("numero", "TEXT"),
        ("bairro", "TEXT"),
        ("cidade", "TEXT"),
        ("estado", "TEXT"),
        ("verificado", "INTEGER NOT NULL DEFAULT 0"),
        ("escolaridade", "TEXT"),
        ("faculdade", "TEXT"),
        ("curso", "TEXT"),
        ("concursos_foco", "TEXT")
    ]
    for col, tipo in novas_colunas:
        try:
            cur.execute(f"ALTER TABLE usuarios ADD COLUMN {col} {tipo}")
            con.commit()
        except Exception:
            pass  # Coluna já existe

    # 2. Tabela de códigos 2FA / OTP
    cur.execute("""
        CREATE TABLE IF NOT EXISTS codigos_verificacao (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            codigo TEXT NOT NULL,
            expira_em TIMESTAMP NOT NULL,
            usado INTEGER NOT NULL DEFAULT 0,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cur.execute("CREATE INDEX IF NOT EXISTS idx_codigos_email_codigo ON codigos_verificacao (email, codigo)")

    # 3. Tabela de sessões autenticadas seguras (por token de cliente no navegador)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS sessoes_lembradas (
            token TEXT PRIMARY KEY,
            usuario_id INTEGER NOT NULL,
            expira_em TIMESTAMP NOT NULL,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (usuario_id) REFERENCES usuarios (id) ON DELETE CASCADE
        )
    """)
    cur.execute("CREATE INDEX IF NOT EXISTS idx_sessoes_token ON sessoes_lembradas (token)")
    con.commit()
    con.close()


# Executa migração ao carregar módulo
_garantir_tabelas_e_migracao()


def formatar_cpf(cpf: str) -> str:
    """Extrai apenas dígitos e formata no padrão 000.000.000-00."""
    digitos = re.sub(r"\D", "", cpf or "")
    if len(digitos) == 11:
        return f"{digitos[:3]}.{digitos[3:6]}.{digitos[6:9]}-{digitos[9:]}"
    return cpf.strip() if cpf else ""


def validar_cpf(cpf: str) -> bool:
    """Valida dígitos do CPF (formato e dígitos verificadores básicos)."""
    digitos = re.sub(r"\D", "", cpf or "")
    if len(digitos) != 11:
        return False
    if digitos == digitos[0] * 11:
        return False

    # Primeiro dígito verificador
    soma = sum(int(digitos[i]) * (10 - i) for i in range(9))
    resto = (soma * 10) % 11
    d1 = 0 if resto == 10 else resto
    if d1 != int(digitos[9]):
        return False

    # Segundo dígito verificador
    soma = sum(int(digitos[i]) * (11 - i) for i in range(10))
    resto = (soma * 10) % 11
    d2 = 0 if resto == 10 else resto
    return d2 == int(digitos[10])


def buscar_endereco_por_cep(cep: str) -> dict | None:
    """
    Consulta o webservice público ViaCEP para autopreencher endereço.
    Retorna dict com logradouro, bairro, localidade (cidade), uf (estado) ou None.
    """
    cep_limpo = re.sub(r"\D", "", cep or "")
    if len(cep_limpo) != 8:
        return None
    try:
        resp = requests.get(f"https://viacep.com.br/ws/{cep_limpo}/json/", timeout=3.5)
        if resp.status_code == 200:
            dados = resp.json()
            if not dados.get("erro"):
                return {
                    "logradouro": dados.get("logradouro", ""),
                    "bairro": dados.get("bairro", ""),
                    "cidade": dados.get("localidade", ""),
                    "estado": dados.get("uf", "")
                }
    except Exception:
        pass
    return None


def gerar_codigo_verificacao(email: str) -> str:
    """
    Gera um código de 6 dígitos numéricos com validade de 15 minutos.
    Invalida códigos anteriores não usados deste e-mail.
    """
    codigo = f"{random.randint(100000, 999999)}"
    expira_em = (datetime.now() + timedelta(minutes=15)).strftime("%Y-%m-%d %H:%M:%S")

    con = pegar_conexao()
    cur = con.cursor()
    # Invalida códigos antigos
    cur.execute("UPDATE codigos_verificacao SET usado = 1 WHERE email = ? AND usado = 0", (email.lower(),))
    # Insere novo código
    cur.execute(
        "INSERT INTO codigos_verificacao (email, codigo, expira_em) VALUES (?, ?, ?)",
        (email.lower(), codigo, expira_em)
    )
    con.commit()
    con.close()
    return codigo


def enviar_email_codigo(email: str, codigo: str, nome: str = "Aluno") -> bool:
    """
    Envia o código de 6 dígitos para o e-mail cadastrado via SMTP.
    Se SMTP não estiver configurado no ambiente, retorna False (o app exibirá em modo teste).
    """
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = os.getenv("SMTP_PORT", "587")
    smtp_user = os.getenv("SMTP_USER")
    smtp_pass = os.getenv("SMTP_PASS")

    if not (smtp_host and smtp_user and smtp_pass):
        # Sem SMTP configurado — modo dev/simulação
        return False

    try:
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart

        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"🔑 Seu código de verificação MathAI: {codigo}"
        msg["From"] = f"MathAI <{smtp_user}>"
        msg["To"] = email

        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; background: #0a0a0f; color: #f8fafc; padding: 24px;">
            <div style="max-width: 480px; margin: 0 auto; background: #13111c; border: 1px solid #7c3aed; border-radius: 16px; padding: 32px; text-align: center;">
                <h1 style="color: #7c3aed; margin-bottom: 8px;">📐 MathAI</h1>
                <p style="color: #94a3b8; font-size: 14px;">Plataforma Cognitiva de Matemática</p>
                <h2 style="color: #f8fafc; margin-top: 24px;">Olá, {nome.split()[0]}!</h2>
                <p style="color: #cbd5e1; font-size: 15px;">Use o código de segurança abaixo para ativar sua conta:</p>
                <div style="background: rgba(124, 58, 237, 0.15); border: 2px dashed #f59e0b; border-radius: 12px; padding: 18px; margin: 24px 0;">
                    <span style="font-size: 32px; font-weight: bold; letter-spacing: 8px; color: #fbbf24;">{codigo}</span>
                </div>
                <p style="color: #64748b; font-size: 12px;">Este código é válido por 15 minutos. Se não foi você quem solicitou, desconsidere este e-mail.</p>
            </div>
        </body>
        </html>
        """
        msg.attach(MIMEText(html_body, "html"))

        with smtplib.SMTP(smtp_host, int(smtp_port), timeout=5) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.sendmail(smtp_user, email, msg.as_string())
        return True
    except Exception:
        return False


def verificar_codigo_otp(email: str, codigo: str) -> dict:
    """
    Verifica o código de 6 dígitos.
    Se válido: marca como usado, ativa o usuário (verificado=1) e retorna os dados do usuário.
    """
    con = pegar_conexao()
    cur = con.cursor()
    agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cur.execute("""
        SELECT id FROM codigos_verificacao
        WHERE email = ? AND codigo = ? AND usado = 0 AND expira_em >= ?
        ORDER BY id DESC LIMIT 1
    """, (email.lower().strip(), codigo.strip(), agora))
    registro = cur.fetchone()

    if not registro:
        con.close()
        return {
            "ok": False,
            "erro": "Código inválido ou expirado. Verifique os 6 dígitos ou clique em reenviar."
        }

    # Marca código como usado
    cur.execute("UPDATE codigos_verificacao SET usado = 1 WHERE id = ?", (registro["id"],))

    # Ativa usuário
    cur.execute("UPDATE usuarios SET verificado = 1 WHERE email = ?", (email.lower().strip(),))
    con.commit()

    # Busca usuário ativado
    cur.execute("""
        SELECT id, nome, email, cpf, idade, celular, cep, logradouro, numero, bairro, cidade, estado,
               escolaridade, faculdade, curso, motivos, concursos_foco, verificado
        FROM usuarios WHERE email = ?
    """, (email.lower().strip(),))
    row = cur.fetchone()
    con.close()

    if row:
        u = dict(row)
        u["motivos"] = json.loads(u.get("motivos") or "[]")
        u["concursos_foco"] = json.loads(u.get("concursos_foco") or "[]")
        return {"ok": True, "usuario": u}

    return {"ok": False, "erro": "Usuário não encontrado."}


def reenviar_codigo_otp(email: str, nome: str = "Aluno") -> dict:
    """Gera um novo código e tenta enviar por e-mail."""
    codigo = gerar_codigo_verificacao(email)
    enviado = enviar_email_codigo(email, codigo, nome)
    return {
        "ok": True,
        "enviado_email": enviado,
        "codigo_teste": codigo
    }


def cadastrar_usuario(
    nome: str,
    email: str,
    senha: str,
    cpf: str | None = None,
    idade: int | None = None,
    celular: str | None = None,
    cep: str | None = None,
    logradouro: str | None = None,
    numero: str | None = None,
    bairro: str | None = None,
    cidade: str | None = None,
    estado: str | None = None,
    motivos: list[str] | None = None,
    escolaridade: str | None = None,
    faculdade: str | None = None,
    curso: str | None = None,
    concursos_foco: list[str] | None = None
) -> dict:
    """
    Cria um novo usuário com status pendente de verificação (verificado=0)
    e gera o código OTP de 6 dígitos.
    """
    con = pegar_conexao()
    cur = con.cursor()
    cpf_formatado = formatar_cpf(cpf) if cpf else None

    try:
        cur.execute("""
            INSERT INTO usuarios (
                nome, email, senha_hash, cpf, idade, celular, cep,
                logradouro, numero, bairro, cidade, estado, motivos,
                escolaridade, faculdade, curso, concursos_foco, verificado
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
        """, (
            nome.strip(),
            email.strip().lower(),
            _hash_senha(senha),
            cpf_formatado,
            idade,
            celular.strip() if celular else None,
            cep.strip() if cep else None,
            logradouro.strip() if logradouro else None,
            numero.strip() if numero else None,
            bairro.strip() if bairro else None,
            cidade.strip() if cidade else None,
            estado.strip().upper() if estado else None,
            json.dumps(motivos or [], ensure_ascii=False),
            escolaridade.strip() if escolaridade else None,
            faculdade.strip() if faculdade else None,
            curso.strip() if curso else None,
            json.dumps(concursos_foco or [], ensure_ascii=False)
        ))
        con.commit()
        usuario_id = cur.lastrowid
        con.close()

        # Gera código OTP de verificação
        codigo_otp = gerar_codigo_verificacao(email)
        enviado_email = enviar_email_codigo(email, codigo_otp, nome)

        return {
            "ok": True,
            "pendente_verificacao": True,
            "email": email.strip().lower(),
            "enviado_email": enviado_email,
            "codigo_teste": codigo_otp,
            "usuario": {
                "id": usuario_id,
                "nome": nome.strip(),
                "email": email.strip().lower(),
                "cpf": cpf_formatado,
                "idade": idade,
                "celular": celular,
                "cep": cep,
                "escolaridade": escolaridade,
                "faculdade": faculdade,
                "curso": curso,
                "concursos_foco": concursos_foco or [],
                "motivos": motivos or [],
                "verificado": 0
            }
        }
    except Exception as e:
        con.close()
        if "UNIQUE" in str(e):
            return {"ok": False, "erro": "Este e-mail já está cadastrado. Faça login ou recupere sua conta."}
        return {"ok": False, "erro": str(e)}


def obter_ou_gerar_codigo_verificacao(email: str) -> str:
    """Retorna o código OTP ativo existente ou gera um novo caso não haja."""
    con = pegar_conexao()
    cur = con.cursor()
    agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cur.execute("""
        SELECT codigo FROM codigos_verificacao
        WHERE email = ? AND usado = 0 AND expira_em >= ?
        ORDER BY id DESC LIMIT 1
    """, (email.lower().strip(), agora))
    row = cur.fetchone()
    con.close()
    if row:
        return row["codigo"]
    return gerar_codigo_verificacao(email)


def fazer_login(email: str, senha: str) -> dict:
    """
    Autentica o usuário. Se o usuário existir mas não tiver sido verificado (verificado=0),
    retorna pendente_verificacao=True para exibir a tela de 6 dígitos.
    """
    con = pegar_conexao()
    cur = con.cursor()
    try:
        cur.execute("""
            SELECT id, nome, email, cpf, idade, celular, cep, logradouro, numero, bairro, cidade, estado,
                   escolaridade, faculdade, curso, motivos, concursos_foco, verificado
            FROM usuarios WHERE email = ? AND senha_hash = ?
        """, (email.strip().lower(), _hash_senha(senha)))
        row = cur.fetchone()
        if row:
            u = dict(row)
            u["motivos"] = json.loads(u.get("motivos") or "[]")
            u["concursos_foco"] = json.loads(u.get("concursos_foco") or "[]")

            # Verifica se conta foi verificada (2FA / ativação)
            if u.get("verificado") == 0:
                codigo_ativo = obter_ou_gerar_codigo_verificacao(u["email"])
                enviado_email = enviar_email_codigo(u["email"], codigo_ativo, u["nome"])
                return {
                    "ok": False,
                    "pendente_verificacao": True,
                    "email": u["email"],
                    "nome": u["nome"],
                    "codigo_teste": codigo_ativo,
                    "enviado_email": enviado_email,
                    "erro": "Sua conta ainda não foi verificada. Digite o código de 6 dígitos para ativar."
                }

            return {"ok": True, "usuario": u}
        return {"ok": False, "erro": "E-mail ou senha incorretos."}
    except Exception as e:
        return {"ok": False, "erro": str(e)}
    finally:
        con.close()


def buscar_usuario_por_email(email: str) -> dict | None:
    """Busca um usuário verificado pelo e-mail."""
    con = pegar_conexao()
    cur = con.cursor()
    try:
        cur.execute("""
            SELECT id, nome, email, cpf, idade, celular, cep, logradouro, numero, bairro, cidade, estado,
                   escolaridade, faculdade, curso, motivos, concursos_foco, verificado
            FROM usuarios WHERE email = ? AND verificado = 1
        """, (email.strip().lower(),))
        row = cur.fetchone()
        if row:
            u = dict(row)
            u["motivos"] = json.loads(u.get("motivos") or "[]")
            u["concursos_foco"] = json.loads(u.get("concursos_foco") or "[]")
            return u
        return None
    except Exception:
        return None
    finally:
        con.close()


def buscar_usuario_por_id(usuario_id: int) -> dict | None:
    """Busca dados completos do usuário pelo ID."""
    con = pegar_conexao()
    cur = con.cursor()
    try:
        cur.execute("""
            SELECT id, nome, email, cpf, idade, celular, cep, logradouro, numero, bairro, cidade, estado,
                   escolaridade, faculdade, curso, motivos, concursos_foco, verificado
            FROM usuarios WHERE id = ?
        """, (usuario_id,))
        row = cur.fetchone()
        if row:
            u = dict(row)
            u["motivos"] = json.loads(u.get("motivos") or "[]")
            u["concursos_foco"] = json.loads(u.get("concursos_foco") or "[]")
            return u
        return None
    except Exception:
        return None
    finally:
        con.close()


def atualizar_perfil_usuario(
    usuario_id: int,
    nome: str,
    celular: str | None = None,
    cpf: str | None = None,
    cep: str | None = None,
    logradouro: str | None = None,
    numero: str | None = None,
    bairro: str | None = None,
    cidade: str | None = None,
    estado: str | None = None,
    escolaridade: str | None = None,
    faculdade: str | None = None,
    curso: str | None = None,
    motivos: list[str] | None = None,
    concursos_foco: list[str] | None = None
) -> dict:
    """Atualiza os dados de perfil e acadêmicos do usuário."""
    con = pegar_conexao()
    cur = con.cursor()
    cpf_formatado = formatar_cpf(cpf) if cpf else None
    try:
        cur.execute("""
            UPDATE usuarios SET
                nome = ?,
                celular = ?,
                cpf = ?,
                cep = ?,
                logradouro = ?,
                numero = ?,
                bairro = ?,
                cidade = ?,
                estado = ?,
                escolaridade = ?,
                faculdade = ?,
                curso = ?,
                motivos = ?,
                concursos_foco = ?
            WHERE id = ?
        """, (
            nome.strip(),
            celular.strip() if celular else None,
            cpf_formatado,
            cep.strip() if cep else None,
            logradouro.strip() if logradouro else None,
            numero.strip() if numero else None,
            bairro.strip() if bairro else None,
            cidade.strip() if cidade else None,
            estado.strip().upper() if estado else None,
            escolaridade.strip() if escolaridade else None,
            faculdade.strip() if faculdade else None,
            curso.strip() if curso else None,
            json.dumps(motivos or [], ensure_ascii=False),
            json.dumps(concursos_foco or [], ensure_ascii=False),
            usuario_id
        ))
        con.commit()
        return {"ok": True}
    except Exception as e:
        return {"ok": False, "erro": str(e)}
    finally:
        con.close()


def criar_sessao_lembrada(usuario_id: int) -> str:
    """Gera um token criptográfico seguro de sessão e salva no SQLite (validade de 30 dias)."""
    con = pegar_conexao()
    try:
        cur = con.cursor()
        token = secrets.token_urlsafe(32)
        expira_em = datetime.now() + timedelta(days=30)
        cur.execute("""
            INSERT INTO sessoes_lembradas (token, usuario_id, expira_em)
            VALUES (?, ?, ?)
        """, (token, usuario_id, expira_em))
        con.commit()
        return token
    finally:
        con.close()


def verificar_token_sessao(token: str) -> dict | None:
    """Valida um token de sessão do cliente e retorna os dados do usuário."""
    if not token or not isinstance(token, str):
        return None
    con = pegar_conexao()
    try:
        cur = con.cursor()
        # Remove tokens expirados
        cur.execute("DELETE FROM sessoes_lembradas WHERE expira_em < ?", (datetime.now(),))
        con.commit()

        cur.execute("""
            SELECT u.id, u.nome, u.email, u.cpf, u.idade, u.celular, u.cep, u.logradouro,
                   u.numero, u.bairro, u.cidade, u.estado, u.escolaridade, u.faculdade,
                   u.curso, u.motivos, u.concursos_foco, u.verificado
            FROM sessoes_lembradas s
            JOIN usuarios u ON u.id = s.usuario_id
            WHERE s.token = ? AND u.verificado = 1
        """, (token.strip(),))
        row = cur.fetchone()
        if row:
            u = dict(row)
            u["motivos"] = json.loads(u.get("motivos") or "[]")
            u["concursos_foco"] = json.loads(u.get("concursos_foco") or "[]")
            return u
        return None
    except Exception:
        return None
    finally:
        con.close()



def encerrar_sessao_por_token(token: str):
    """Invalida o token de sessão específico do cliente ao fazer logout."""
    if not token or not isinstance(token, str):
        return
    con = pegar_conexao()
    try:
        cur = con.cursor()
        cur.execute("DELETE FROM sessoes_lembradas WHERE token = ?", (token.strip(),))
        con.commit()
    except Exception:
        pass
    finally:
        con.close()


# Funções legadas mantidas vazias para evitar vazamento entre usuários
def salvar_sessao_lembrada(usuario: dict):
    pass


def verificar_sessao_lembrada() -> dict | None:
    return None


def encerrar_sessao_lembrada():
    pass

