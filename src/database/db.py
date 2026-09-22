"""
Gerenciador de Banco de Dados SQLite do MathAI.
Fase 0 (V0) - Fundação de Dados
"""

# Escreva aqui a sua conexão com o SQLite, inicialização do schema e funções de query!

import sqlite3
from pathlib import Path
import json

BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Caminho absoluto do arquivo de banco de dados na raiz do projeto

DB_PATH = BASE_DIR / "data" / "mathai.db"

#Lugar onde está as instruções de como montar o banco de dados
SCHEMA_PATH = BASE_DIR / "src" / "database" / "schema.sql"


import os

def _obter_credenciais_turso():
    """Tenta obter URL e token do Turso via os.environ, .env ou st.secrets."""
    url = os.environ.get("TURSO_DATABASE_URL")
    token = os.environ.get("TURSO_AUTH_TOKEN")

    if not url or not token:
        env_file = BASE_DIR / ".env"
        if env_file.exists():
            for line in env_file.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if "=" in line and not line.startswith("#"):
                    k, v = line.split("=", 1)
                    k, v = k.strip(), v.strip().strip("\"'")
                    if k in ("TURSO_DATABASE_URL", "DATABASE_URL"):
                        url = v
                    elif k in ("TURSO_AUTH_TOKEN", "AUTH_TOKEN"):
                        token = v

    if not url or not token:
        try:
            import streamlit as st
            # Busca direta nas chaves do st.secrets
            for k in ("TURSO_DATABASE_URL", "turso_database_url", "DATABASE_URL", "database_url"):
                if k in st.secrets:
                    url = str(st.secrets[k]).strip().strip("\"'")
                    break

            for k in ("TURSO_AUTH_TOKEN", "turso_auth_token", "AUTH_TOKEN", "auth_token"):
                if k in st.secrets:
                    token = str(st.secrets[k]).strip().strip("\"'")
                    break

            # Se o usuário configurou dentro de uma seção [turso] no TOML:
            if "turso" in st.secrets:
                sec = st.secrets["turso"]
                if not url:
                    for k in ("TURSO_DATABASE_URL", "DATABASE_URL", "url", "database_url"):
                        if k in sec:
                            url = str(sec[k]).strip().strip("\"'")
                            break
                if not token:
                    for k in ("TURSO_AUTH_TOKEN", "AUTH_TOKEN", "token", "auth_token"):
                        if k in sec:
                            token = str(sec[k]).strip().strip("\"'")
                            break
        except Exception:
            pass

    return url, token


import base64
from typing import Any, List, Optional, Tuple


def _to_hrana_val(val: Any) -> dict:
    if val is None:
        return {"type": "null"}
    elif isinstance(val, bool):
        return {"type": "integer", "value": "1" if val else "0"}
    elif isinstance(val, int):
        return {"type": "integer", "value": str(val)}
    elif isinstance(val, float):
        return {"type": "float", "value": val}
    elif isinstance(val, (bytes, bytearray)):
        return {"type": "blob", "base64": base64.b64encode(val).decode("ascii")}
    else:
        return {"type": "text", "value": str(val)}


def _from_hrana_val(val_dict: dict) -> Any:
    vtype = val_dict.get("type")
    if vtype == "null":
        return None
    elif vtype == "integer":
        return int(val_dict.get("value", 0))
    elif vtype == "float":
        return float(val_dict.get("value", 0.0))
    elif vtype == "blob":
        return base64.b64decode(val_dict.get("base64", ""))
    else:
        return val_dict.get("value", "")


class TursoRow(dict):
    """Emula sqlite3.Row para compatibilidade total com o código do MathAI."""
    def __init__(self, cols: List[str], values: List[Any]):
        super().__init__(zip(cols, values))
        self._cols = list(cols)
        self._values = list(values)

    def __getitem__(self, item):
        if isinstance(item, int):
            return self._values[item]
        return super().__getitem__(item)

    def keys(self) -> List[str]:
        return list(self._cols)

    def __len__(self):
        return len(self._values)

    def __repr__(self):
        return f"TursoRow({dict(self)})"


class TursoCursor:
    def __init__(self, session, endpoint: str):
        self._session = session
        self._endpoint = endpoint
        self._rows: List[TursoRow] = []
        self._idx = 0
        self._cols: List[str] = []
        self.lastrowid: Optional[int] = None
        self.rowcount: int = 0

    @property
    def description(self) -> Optional[List[Tuple]]:
        if not self._cols:
            return None
        return [(c, None, None, None, None, None, None) for c in self._cols]

    def execute(self, sql: str, params: Any = None):
        stmt: dict = {"sql": sql}
        if params is not None:
            if isinstance(params, (list, tuple)):
                stmt["args"] = [_to_hrana_val(p) for p in params]
            elif isinstance(params, dict):
                stmt["named_args"] = [{"name": k, "value": _to_hrana_val(v)} for k, v in params.items()]
            else:
                stmt["args"] = [_to_hrana_val(params)]

        payload = {"requests": [{"type": "execute", "stmt": stmt}]}
        resp = self._session.post(self._endpoint, json=payload, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        result_wrapper = data["results"][0]
        if result_wrapper.get("type") == "error":
            err = result_wrapper["error"]
            raise RuntimeError(f"Turso Error ({err.get('code', 'UNKNOWN')}): {err.get('message')}")

        res = result_wrapper["response"]["result"]
        self._cols = [c["name"] for c in res.get("cols", [])]
        self._rows = [
            TursoRow(self._cols, [_from_hrana_val(cell) for cell in raw_row])
            for raw_row in res.get("rows", [])
        ]
        self._idx = 0
        self.rowcount = res.get("affected_row_count", 0)
        lid = res.get("last_insert_rowid")
        self.lastrowid = int(lid) if lid is not None else None
        return self

    def executescript(self, script: str):
        reqs = []
        for cmd in script.split(";"):
            cmd = cmd.strip()
            if cmd:
                reqs.append({"type": "execute", "stmt": {"sql": cmd}})
        if not reqs:
            return self
        payload = {"requests": reqs}
        resp = self._session.post(self._endpoint, json=payload, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        for r in data.get("results", []):
            if r.get("type") == "error":
                err = r["error"]
                raise RuntimeError(f"Turso Error ({err.get('code', 'UNKNOWN')}): {err.get('message')}")
        return self

    def fetchall(self) -> List[TursoRow]:
        return self._rows

    def fetchone(self) -> Optional[TursoRow]:
        if self._idx >= len(self._rows):
            return None
        row = self._rows[self._idx]
        self._idx += 1
        return row


class TursoConnection:
    def __init__(self, url: str, token: str):
        import requests
        clean_url = url.replace("libsql://", "https://")
        if not clean_url.startswith("http"):
            clean_url = f"https://{clean_url}"
        self._endpoint = f"{clean_url.rstrip('/')}/v2/pipeline"

        self._session = requests.Session()
        self._session.headers.update({
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        })

    def cursor(self) -> TursoCursor:
        return TursoCursor(self._session, self._endpoint)

    def execute(self, sql: str, params: Any = None) -> TursoCursor:
        cur = self.cursor()
        return cur.execute(sql, params)

    def executescript(self, script: str) -> TursoCursor:
        cur = self.cursor()
        return cur.executescript(script)

    def commit(self):
        pass  # Turso HTTP auto-commits statements

    def close(self):
        try:
            self._session.close()
        except Exception:
            pass


def _garantir_schema_existe(con):
    """Garante que as tabelas básicas do schema.sql existam no SQLite local para evitar OperationalError."""
    try:
        cur = con.cursor()
        cur.execute("SELECT 1 FROM questoes LIMIT 1")
    except Exception:
        try:
            if SCHEMA_PATH.exists():
                with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
                    schema_sql = f.read()
                con.executescript(schema_sql)
                con.commit()
        except Exception as e:
            print(f"Erro ao inicializar schema de fallback: {e}")


def pegar_conexao():
    """
    Retorna conexão com o banco de dados.
    Prioriza o Turso (nuvem 24h) se configurado no .env ou st.secrets.
    Caso contrário, utiliza o SQLite local (data/mathai.db).
    """
    url, token = _obter_credenciais_turso()
    if url and token:
        try:
            return TursoConnection(url, token)
        except Exception as e:
            print(f"⚠️ Falha ao conectar no Turso ({e}). Usando SQLite local como fallback.")

    # Fallback para SQLite local
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    con.execute("PRAGMA foreign_keys = ON;")
    con.row_factory = sqlite3.Row
    _garantir_schema_existe(con)
    return con

def init_db():
    con = pegar_conexao() 
    with open(SCHEMA_PATH,'r',encoding='utf-8') as f:
        schema_sql = f.read()
    con.executescript(schema_sql) 
    con.commit()
    con.close()

def _classificar_tipo(enunciado: str, gabarito: str) -> str:
    """Classifica automaticamente a questão como 'objetiva' ou 'discursiva'."""
    import re
    tem_alternativas = bool(re.search(r'(?m)^\(([A-E])\)\s*(.+)$', enunciado or ""))
    gabarito_e_letra = str(gabarito or "").strip().upper() in ("A", "B", "C", "D", "E")
    return "objetiva" if (tem_alternativas or gabarito_e_letra) else "discursiva"


_mathnet_coluna_verificada = False


def _garantir_coluna_mathnet():
    """Garante que a coluna mathnet_id e a tabela mathnet_ingestao existam no banco."""
    global _mathnet_coluna_verificada
    if _mathnet_coluna_verificada:
        return

    con = pegar_conexao()
    cur = con.cursor()
    try:
        cur.execute("ALTER TABLE questoes ADD COLUMN mathnet_id TEXT")
        con.commit()
    except Exception:
        pass  # Coluna já existe

    cur.execute("""
        CREATE TABLE IF NOT EXISTS mathnet_ingestao (
            mathnet_id TEXT PRIMARY KEY,
            questao_id INTEGER,
            tipo_ingestao TEXT,
            data_importacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (questao_id) REFERENCES questoes (id) ON DELETE CASCADE
        )
    """)
    cur.execute("CREATE INDEX IF NOT EXISTS idx_mathnet_id ON questoes (mathnet_id)")
    con.commit()
    con.close()
    _mathnet_coluna_verificada = True


def inserir_questao(
    materia,
    topico,
    enunciado,
    gabarito,
    subtopico=None,
    dificuldade=None,
    banca=None,
    ano=None,
    estrategias_esperadas=None,
    figura_path=None,
    tipo=None,          # 'objetiva' | 'discursiva' | None (auto-classifica)
    mathnet_id=None,
):
    """Insere uma nova questão no banco de dados e retorna seu ID."""
    _garantir_coluna_mathnet()
    con = pegar_conexao()
    cur = con.cursor()

    # Se estratégias vier como lista (ex: ['Tales', 'Semelhança']), converte para texto JSON:
    if isinstance(estrategias_esperadas, list):
        estrategias_esperadas = json.dumps(estrategias_esperadas, ensure_ascii=False)

    # Auto-classifica se tipo não for informado
    if tipo not in ("objetiva", "discursiva"):
        tipo = _classificar_tipo(enunciado, gabarito)

    sql = """
        INSERT INTO questoes (
            materia,
            topico,
            subtopico,
            dificuldade,
            banca,
            ano,
            enunciado,
            figura_path,
            gabarito,
            estrategias_esperadas,
            tipo,
            mathnet_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """

    cur.execute(sql, (
        materia,
        topico,
        subtopico,
        dificuldade,
        banca,
        ano,
        enunciado,
        figura_path,
        gabarito,
        estrategias_esperadas,
        tipo,
        mathnet_id,
    ))

    novo_id = cur.lastrowid

    if mathnet_id:
        try:
            cur.execute("""
                INSERT OR REPLACE INTO mathnet_ingestao (mathnet_id, questao_id, tipo_ingestao)
                VALUES (?, ?, ?)
            """, (str(mathnet_id), novo_id, tipo or "indefinido"))
        except Exception:
            pass

    con.commit()
    con.close()

    return novo_id


def listar_questoes():
    """Retorna todas as questões cadastradas no banco."""
    con = pegar_conexao()
    cur = con.cursor()
    cur.execute("SELECT * FROM questoes")
    questoes = cur.fetchall()
    con.close()
    return questoes

def buscar_questao_por_id(questao_id):
    """Busca e retorna uma única questão pelo seu ID."""
    con = pegar_conexao()
    cur = con.cursor()
    cur.execute("SELECT * FROM questoes WHERE id = ?", (questao_id,))
    questao = cur.fetchone()
    con.close()
    return questao


def limpar_questoes():
    """Apaga todas as questões e reseta o contador de IDs para 1."""
    con = pegar_conexao()
    con.execute("DELETE FROM questoes;")
    con.execute("DELETE FROM sqlite_sequence WHERE name = 'questoes';")
    con.commit()
    con.close()
    print("Tabela 'questoes' limpa e ID resetado com sucesso!")


def excluir_questao(questao_id, reordenar=True):
    """
    Apaga uma questão específica pelo ID e ajusta o contador do SQLite.
    Se reordenar=True, diminui em 1 os IDs das questões que vinham depois.
    """
    con = pegar_conexao()
    cur = con.cursor()
    
    # 1. Deleta a questão
    cur.execute("DELETE FROM questoes WHERE id = ?", (questao_id,))
    
    # 2. Se for para fechar o 'buraco' na fila de IDs:
    if reordenar:
        cur.execute("UPDATE questoes SET id = id - 1 WHERE id > ?", (questao_id,))
    
    # 3. Sincroniza o contador autoincrement com o maior ID restante
    cur.execute("""
        UPDATE sqlite_sequence 
        SET seq = (SELECT COALESCE(MAX(id), 0) FROM questoes) 
        WHERE name = 'questoes'
    """)
    con.commit()
    con.close()
    print(f"Questão {questao_id} excluída e sequência de IDs recalculada com sucesso!")




def reportar_questao(questao_id: int, motivo: str, descricao: str = "", aluno_id: int | None = None) -> int:
    """
    Registra um reporte de erro ou problema em uma questão (LaTeX quebrado, imagem, gabarito).
    Cria a tabela se não existir e retorna o ID do reporte.
    """
    con = pegar_conexao()
    cur = con.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS questoes_reportadas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            questao_id INTEGER NOT NULL,
            aluno_id INTEGER,
            motivo TEXT NOT NULL,
            descricao TEXT,
            status TEXT DEFAULT 'pendente',
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (questao_id) REFERENCES questoes (id) ON DELETE CASCADE
        )
    """)
    cur.execute("""
        INSERT INTO questoes_reportadas (questao_id, aluno_id, motivo, descricao)
        VALUES (?, ?, ?, ?)
    """, (questao_id, aluno_id, motivo, descricao))
    con.commit()
    report_id = cur.lastrowid or 0
    con.close()
    return report_id
