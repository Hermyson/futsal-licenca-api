"""
<<<<<<< HEAD
API de Licenciamento — Futvôlei Replay
PostgreSQL via psycopg2 — dados persistentes no Render.
"""

import os
import secrets
from datetime import datetime, timezone, timedelta
from contextlib import asynccontextmanager

import psycopg2
import psycopg2.extras
=======
API de Licenciamento — Futsal Replay
Stack: FastAPI + SQLite (sem dependências externas)

Endpoints públicos:
  GET  /licenca?email=...&chave=...   → verifica se licença está ativa

Endpoints admin (requer header X-Admin-Key):
  GET  /admin/clientes                → lista todos os clientes
  POST /admin/cliente                 → cadastra novo cliente
  POST /admin/bloquear                → bloqueia um cliente
  POST /admin/renovar                 → renova por N dias
"""

import os
import sqlite3
import secrets
import hashlib
from datetime import datetime, timezone, timedelta
from contextlib import contextmanager, asynccontextmanager

>>>>>>> 7dae29c1c66bf74e0c4117dcec7c1061ae60bc97
from fastapi import FastAPI, HTTPException, Header, Query
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

<<<<<<< HEAD
ADMIN_KEY    = os.environ.get("ADMIN_KEY", "troque-essa-chave-admin")
DATABASE_URL = os.environ.get("DATABASE_URL", "")
DAYS_DEFAULT = 30


def get_db():
    conn = psycopg2.connect(DATABASE_URL)
    conn.autocommit = False
    return conn


def init_db():
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS clientes (
                    id        SERIAL PRIMARY KEY,
                    email     TEXT UNIQUE NOT NULL,
                    nome      TEXT NOT NULL,
                    chave     TEXT NOT NULL,
                    ativo     BOOLEAN NOT NULL DEFAULT TRUE,
                    expira_em TIMESTAMPTZ NOT NULL,
                    criado_em TIMESTAMPTZ NOT NULL
                )
            """)
        conn.commit()
        print("[DB] Tabela verificada.")
    finally:
        conn.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Futvôlei Replay — Licenças", docs_url=None, redoc_url=None, lifespan=lifespan)

=======
# ── Configurações ──────────────────────────────────────────────────────────────
ADMIN_KEY = os.environ.get("ADMIN_KEY", "troque-essa-chave-admin")
DB_PATH   = os.environ.get("DB_PATH", "licencas.db")
DAYS_DEFAULT = 30

@asynccontextmanager
async def lifespan(app):
    init_db()
    yield

app = FastAPI(title="Futsal Replay — Licenças", docs_url=None, redoc_url=None, lifespan=lifespan)

# ── Banco de dados ─────────────────────────────────────────────────────────────

def init_db():
    with get_db() as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS clientes (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                email      TEXT    UNIQUE NOT NULL,
                nome       TEXT    NOT NULL,
                chave      TEXT    NOT NULL,
                ativo      INTEGER NOT NULL DEFAULT 1,
                expira_em  TEXT    NOT NULL,
                criado_em  TEXT    NOT NULL
            )
        """)
        db.commit()

@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def gerar_chave() -> str:
    """Gera uma chave única de 16 caracteres para o cliente."""
    return secrets.token_hex(8).upper()
>>>>>>> 7dae29c1c66bf74e0c4117dcec7c1061ae60bc97

def verificar_admin(x_admin_key: str = Header(...)):
    if not secrets.compare_digest(x_admin_key, ADMIN_KEY):
        raise HTTPException(status_code=401, detail="Chave admin inválida.")

<<<<<<< HEAD
=======
# ── Modelos ────────────────────────────────────────────────────────────────────
>>>>>>> 7dae29c1c66bf74e0c4117dcec7c1061ae60bc97

class NovoCliente(BaseModel):
    email: str
    nome:  str
    dias:  int = DAYS_DEFAULT

<<<<<<< HEAD

class AcaoCliente(BaseModel):
    email: str
    dias:  int = DAYS_DEFAULT


# ── Endpoints públicos ────────────────────────────────────────────────────────

@app.get("/licenca")
def verificar_licenca(
    email: str = Query(...),
    chave: str = Query(...),
):
    conn = get_db()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                "SELECT * FROM clientes WHERE email = %s AND chave = %s",
                (email.lower().strip(), chave.upper().strip())
            )
            row = cur.fetchone()
    finally:
        conn.close()

    if not row:
        return {"valido": False, "mensagem": "Licença não encontrada."}
    if not row["ativo"]:
        return {"valido": False, "mensagem": "Licença bloqueada. Entre em contato para renovar."}

    agora  = datetime.now(timezone.utc)
    expira = row["expira_em"]
    if hasattr(expira, 'tzinfo') and expira.tzinfo is None:
        expira = expira.replace(tzinfo=timezone.utc)
=======
class AcaoCliente(BaseModel):
    email: str
    dias:  int = DAYS_DEFAULT   # usado só no renovar

# ── Endpoints públicos ─────────────────────────────────────────────────────────


@app.get("/licenca")
def verificar_licenca(
    email: str = Query(..., description="E-mail do cliente"),
    chave: str = Query(..., description="Chave de acesso do cliente"),
):
    """
    Chamado pelo software a cada abertura.
    Retorna {"valido": true/false, "mensagem": "..."}
    """
    with get_db() as db:
        row = db.execute(
            "SELECT * FROM clientes WHERE email = ? AND chave = ?",
            (email.lower().strip(), chave.upper().strip())
        ).fetchone()

    if not row:
        return {"valido": False, "mensagem": "Licença não encontrada."}

    if not row["ativo"]:
        return {"valido": False, "mensagem": "Licença bloqueada. Entre em contato para renovar."}

    expira = datetime.fromisoformat(row["expira_em"])
    agora  = datetime.now(timezone.utc)
>>>>>>> 7dae29c1c66bf74e0c4117dcec7c1061ae60bc97

    if agora > expira:
        return {"valido": False, "mensagem": "Licença expirada. Entre em contato para renovar."}

    dias_restantes = (expira - agora).days
    return {
        "valido":         True,
        "mensagem":       f"Licença válida. {dias_restantes} dia(s) restante(s).",
        "dias_restantes": dias_restantes,
        "nome":           row["nome"],
    }

<<<<<<< HEAD

# ── Endpoints admin ───────────────────────────────────────────────────────────
=======
# ── Endpoints admin ────────────────────────────────────────────────────────────
>>>>>>> 7dae29c1c66bf74e0c4117dcec7c1061ae60bc97

@app.get("/admin/clientes")
def listar_clientes(x_admin_key: str = Header(...)):
    verificar_admin(x_admin_key)
<<<<<<< HEAD
    conn = get_db()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT * FROM clientes ORDER BY criado_em DESC")
            rows = cur.fetchall()
    finally:
        conn.close()
    return [dict(r) for r in rows]


@app.post("/admin/cliente", status_code=201)
def cadastrar_cliente(dados: NovoCliente, x_admin_key: str = Header(...)):
    verificar_admin(x_admin_key)
    chave     = secrets.token_hex(8).upper()
    agora     = datetime.now(timezone.utc)
    expira_em = agora + timedelta(days=dados.dias)

    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO clientes (email, nome, chave, ativo, expira_em, criado_em) VALUES (%s,%s,%s,TRUE,%s,%s)",
                (dados.email.lower().strip(), dados.nome, chave, expira_em, agora)
            )
        conn.commit()
    except psycopg2.errors.UniqueViolation:
        conn.rollback()
        raise HTTPException(status_code=400, detail="E-mail já cadastrado.")
    finally:
        conn.close()

    return {
        "mensagem":  f"Cliente '{dados.nome}' cadastrado.",
        "email":     dados.email.lower().strip(),
        "chave":     chave,
        "expira_em": expira_em.strftime("%d/%m/%Y"),
    }


@app.post("/admin/bloquear")
def bloquear_cliente(dados: AcaoCliente, x_admin_key: str = Header(...)):
    verificar_admin(x_admin_key)
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("UPDATE clientes SET ativo = FALSE WHERE email = %s",
                        (dados.email.lower().strip(),))
            if cur.rowcount == 0:
                raise HTTPException(status_code=404, detail="Cliente não encontrado.")
        conn.commit()
    finally:
        conn.close()
    return {"mensagem": f"Cliente '{dados.email}' bloqueado."}


@app.post("/admin/renovar")
def renovar_cliente(dados: AcaoCliente, x_admin_key: str = Header(...)):
    verificar_admin(x_admin_key)
    nova = datetime.now(timezone.utc) + timedelta(days=dados.dias)
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE clientes SET ativo = TRUE, expira_em = %s WHERE email = %s",
                (nova, dados.email.lower().strip())
            )
            if cur.rowcount == 0:
                raise HTTPException(status_code=404, detail="Cliente não encontrado.")
        conn.commit()
    finally:
        conn.close()
    return {"mensagem": f"Cliente '{dados.email}' renovado por {dados.dias} dias."}


@app.delete("/admin/cliente")
def excluir_cliente(dados: AcaoCliente, x_admin_key: str = Header(...)):
    verificar_admin(x_admin_key)
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM clientes WHERE email = %s",
                        (dados.email.lower().strip(),))
            if cur.rowcount == 0:
                raise HTTPException(status_code=404, detail="Cliente não encontrado.")
        conn.commit()
    finally:
        conn.close()
    return {"mensagem": f"Cliente '{dados.email}' excluído."}


# ── Painel admin ──────────────────────────────────────────────────────────────

@app.get("/admin", response_class=HTMLResponse)
def painel_admin():
    return """<!DOCTYPE html>
=======
    with get_db() as db:
        rows = db.execute("SELECT * FROM clientes ORDER BY criado_em DESC").fetchall()
    return [dict(r) for r in rows]

@app.post("/admin/cliente", status_code=201)
def cadastrar_cliente(dados: NovoCliente, x_admin_key: str = Header(...)):
    verificar_admin(x_admin_key)
    chave     = gerar_chave()
    agora     = datetime.now(timezone.utc)
    expira_em = agora + timedelta(days=dados.dias)

    try:
        with get_db() as db:
            db.execute(
                "INSERT INTO clientes (email, nome, chave, ativo, expira_em, criado_em) VALUES (?,?,?,1,?,?)",
                (dados.email.lower().strip(), dados.nome, chave,
                 expira_em.isoformat(), agora.isoformat())
            )
            db.commit()
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="E-mail já cadastrado.")

    return {
        "mensagem": f"Cliente '{dados.nome}' cadastrado com sucesso.",
        "email":    dados.email.lower().strip(),
        "chave":    chave,
        "expira_em": expira_em.strftime("%d/%m/%Y"),
    }

@app.post("/admin/bloquear")
def bloquear_cliente(dados: AcaoCliente, x_admin_key: str = Header(...)):
    verificar_admin(x_admin_key)
    with get_db() as db:
        cur = db.execute("UPDATE clientes SET ativo = 0 WHERE email = ?",
                         (dados.email.lower().strip(),))
        db.commit()
    if cur.rowcount == 0:
        raise HTTPException(status_code=404, detail="Cliente não encontrado.")
    return {"mensagem": f"Cliente '{dados.email}' bloqueado."}

@app.post("/admin/renovar")
def renovar_cliente(dados: AcaoCliente, x_admin_key: str = Header(...)):
    verificar_admin(x_admin_key)
    nova_expiracao = (datetime.now(timezone.utc) + timedelta(days=dados.dias)).isoformat()
    with get_db() as db:
        cur = db.execute(
            "UPDATE clientes SET ativo = 1, expira_em = ? WHERE email = ?",
            (nova_expiracao, dados.email.lower().strip())
        )
        db.commit()
    if cur.rowcount == 0:
        raise HTTPException(status_code=404, detail="Cliente não encontrado.")
    return {"mensagem": f"Cliente '{dados.email}' renovado por {dados.dias} dias."}

# ── Painel admin HTML simples ──────────────────────────────────────────────────

@app.get("/admin", response_class=HTMLResponse)
def painel_admin():
    """Página HTML simples para gerenciar clientes pelo navegador."""
    return """
<!DOCTYPE html>
>>>>>>> 7dae29c1c66bf74e0c4117dcec7c1061ae60bc97
<html lang="pt-br">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<<<<<<< HEAD
<title>Futvôlei Replay — Admin</title>
<style>
  *{box-sizing:border-box;margin:0;padding:0}
  body{font-family:system-ui,sans-serif;background:#0a0a0f;color:#e0e0e0;padding:24px}
  h1{color:#fff;margin-bottom:24px;font-size:20px}
  h2{color:#94a3b8;font-size:12px;text-transform:uppercase;letter-spacing:1px;margin-bottom:12px}
  .card{background:#12121a;border:1px solid #2a2a3a;border-radius:12px;padding:20px;margin-bottom:20px}
  input{background:#0a0a0f;border:1px solid #2a2a3a;color:#eee;padding:8px 12px;border-radius:8px;width:100%;margin-bottom:10px;font-size:13px}
  input:focus{outline:none;border-color:#3b82f6}
  button{border:none;padding:9px 18px;border-radius:8px;cursor:pointer;font-size:13px;width:100%;margin-top:4px;font-weight:bold}
  .btn-blue{background:#3b82f6;color:#fff}
  .btn-blue:hover{background:#2563eb}
  .btn-red{background:#ef4444;color:#fff}
  .btn-red:hover{background:#dc2626}
  .btn-green{background:#22c55e;color:#fff}
  .btn-green:hover{background:#16a34a}
  .btn-gray{background:#1e1e2e;color:#94a3b8;border:1px solid #2a2a3a}
  table{width:100%;border-collapse:collapse;font-size:13px}
  th{text-align:left;color:#64748b;padding:8px 10px;border-bottom:1px solid #1e1e2e}
  td{padding:9px 10px;border-bottom:1px solid #1a1a26}
  .badge{display:inline-block;padding:2px 10px;border-radius:20px;font-size:11px;font-weight:bold}
  .ativo{background:#14532d;color:#86efac}
  .inativo{background:#450a0a;color:#fca5a5}
  .expirado{background:#422006;color:#fdba74}
  #msg{padding:10px 14px;border-radius:8px;margin-bottom:16px;display:none;font-size:13px}
  #msg.ok{background:#14532d;color:#86efac}
  #msg.err{background:#450a0a;color:#fca5a5}
  .row2{display:grid;grid-template-columns:1fr 1fr;gap:10px}
  .row3{display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px}
  code{background:#1e1e2e;padding:2px 8px;border-radius:4px;font-family:monospace;font-size:12px;color:#93c5fd}
</style>
</head>
<body>
<h1>🏐 Futvôlei Replay — Painel de Licenças</h1>
=======
<title>Futsal Replay — Admin</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: system-ui, sans-serif; background: #0f0f0f; color: #e0e0e0; padding: 24px; }
  h1 { color: #fff; margin-bottom: 24px; font-size: 20px; }
  h2 { color: #aaa; font-size: 14px; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 12px; }
  .card { background: #1a1a1a; border: 1px solid #2a2a2a; border-radius: 10px; padding: 20px; margin-bottom: 24px; }
  input, select { background: #0f0f0f; border: 1px solid #333; color: #eee; padding: 8px 12px;
    border-radius: 6px; width: 100%; margin-bottom: 10px; font-size: 14px; }
  button { background: #2563eb; color: #fff; border: none; padding: 9px 18px;
    border-radius: 6px; cursor: pointer; font-size: 14px; width: 100%; margin-top: 4px; }
  button.danger  { background: #dc2626; }
  button.success { background: #16a34a; }
  table { width: 100%; border-collapse: collapse; font-size: 13px; }
  th { text-align: left; color: #888; padding: 6px 10px; border-bottom: 1px solid #2a2a2a; }
  td { padding: 8px 10px; border-bottom: 1px solid #1e1e1e; }
  .badge { display:inline-block; padding: 2px 8px; border-radius: 20px; font-size: 11px; }
  .ativo    { background:#14532d; color:#86efac; }
  .inativo  { background:#450a0a; color:#fca5a5; }
  .expirado { background:#422006; color:#fdba74; }
  #msg { padding: 10px 14px; border-radius: 6px; margin-bottom: 16px; display:none; }
  #msg.ok  { background:#14532d; color:#86efac; }
  #msg.err { background:#450a0a; color:#fca5a5; }
  .row2 { display:grid; grid-template-columns:1fr 1fr; gap:12px; }
</style>
</head>
<body>
<h1>⚽ Futsal Replay — Painel de Licenças</h1>
>>>>>>> 7dae29c1c66bf74e0c4117dcec7c1061ae60bc97
<div id="msg"></div>

<div class="card">
  <h2>Chave Admin</h2>
  <input type="password" id="admin-key" placeholder="Sua chave admin (ADMIN_KEY)">
</div>

<div class="card">
  <h2>Cadastrar novo cliente</h2>
  <div class="row2">
    <input type="text"  id="novo-nome"  placeholder="Nome do cliente">
    <input type="email" id="novo-email" placeholder="E-mail do cliente">
  </div>
  <input type="number" id="novo-dias" value="30" min="1" placeholder="Dias de validade">
<<<<<<< HEAD
  <button class="btn-blue" onclick="cadastrar()">Cadastrar</button>
</div>

<div class="card">
  <h2>Gerenciar cliente</h2>
  <input type="email" id="acao-email" placeholder="E-mail do cliente">
  <input type="number" id="acao-dias" value="30" min="1" placeholder="Dias (renovação)">
  <div class="row3">
    <button class="btn-red"   onclick="bloquear()">Bloquear</button>
    <button class="btn-green" onclick="renovar()">Renovar</button>
    <button class="btn-gray"  onclick="excluir()">Excluir</button>
=======
  <button onclick="cadastrar()">Cadastrar</button>
</div>

<div class="card">
  <h2>Bloquear / Renovar cliente</h2>
  <input type="email" id="acao-email" placeholder="E-mail do cliente">
  <input type="number" id="acao-dias" value="30" min="1" placeholder="Dias (renovação)">
  <div class="row2">
    <button class="danger"  onclick="bloquear()">Bloquear</button>
    <button class="success" onclick="renovar()">Renovar</button>
>>>>>>> 7dae29c1c66bf74e0c4117dcec7c1061ae60bc97
  </div>
</div>

<div class="card">
  <h2>Clientes cadastrados</h2>
<<<<<<< HEAD
  <button class="btn-gray" onclick="listar()" style="width:auto;margin-bottom:16px;padding:6px 16px">↻ Atualizar lista</button>
  <table id="tabela">
    <tr><th>Nome</th><th>E-mail</th><th>Chave</th><th>Status</th><th>Expira em</th></tr>
  </table>
=======
  <button onclick="listar()" style="width:auto;margin-bottom:16px">Atualizar lista</button>
  <table id="tabela"><tr><th>Nome</th><th>E-mail</th><th>Chave</th><th>Status</th><th>Expira em</th></tr></table>
>>>>>>> 7dae29c1c66bf74e0c4117dcec7c1061ae60bc97
</div>

<script>
const key = () => document.getElementById('admin-key').value;

function msg(text, ok=true) {
  const el = document.getElementById('msg');
<<<<<<< HEAD
  el.textContent = text;
  el.className = ok ? 'ok' : 'err';
  el.style.display = 'block';
  setTimeout(() => el.style.display = 'none', 5000);
}

async function req(method, path, body=null) {
  const opts = {method, headers:{'X-Admin-Key':key(),'Content-Type':'application/json'}};
=======
  el.textContent = text; el.className = ok ? 'ok' : 'err'; el.style.display = 'block';
  setTimeout(() => el.style.display = 'none', 4000);
}

async function req(method, path, body=null) {
  const opts = { method, headers: { 'X-Admin-Key': key(), 'Content-Type': 'application/json' } };
>>>>>>> 7dae29c1c66bf74e0c4117dcec7c1061ae60bc97
  if (body) opts.body = JSON.stringify(body);
  const r = await fetch(path, opts);
  return [r.ok, await r.json()];
}

async function cadastrar() {
  const nome  = document.getElementById('novo-nome').value;
  const email = document.getElementById('novo-email').value;
  const dias  = parseInt(document.getElementById('novo-dias').value);
  if (!nome || !email) return msg('Preencha nome e e-mail.', false);
<<<<<<< HEAD
  const [ok, data] = await req('POST', '/admin/cliente', {nome, email, dias});
=======
  const [ok, data] = await req('POST', '/admin/cliente', { nome, email, dias });
>>>>>>> 7dae29c1c66bf74e0c4117dcec7c1061ae60bc97
  if (ok) { msg(`✓ ${data.mensagem} | Chave: ${data.chave} | Expira: ${data.expira_em}`); listar(); }
  else msg(data.detail || 'Erro.', false);
}

async function bloquear() {
  const email = document.getElementById('acao-email').value;
  if (!email) return msg('Informe o e-mail.', false);
<<<<<<< HEAD
  const [ok, data] = await req('POST', '/admin/bloquear', {email});
=======
  const [ok, data] = await req('POST', '/admin/bloquear', { email });
>>>>>>> 7dae29c1c66bf74e0c4117dcec7c1061ae60bc97
  if (ok) { msg(`✓ ${data.mensagem}`); listar(); }
  else msg(data.detail || 'Erro.', false);
}

async function renovar() {
  const email = document.getElementById('acao-email').value;
  const dias  = parseInt(document.getElementById('acao-dias').value);
  if (!email) return msg('Informe o e-mail.', false);
<<<<<<< HEAD
  const [ok, data] = await req('POST', '/admin/renovar', {email, dias});
  if (ok) { msg(`✓ ${data.mensagem}`); listar(); }
  else msg(data.detail || 'Erro.', false);
}

async function excluir() {
  const email = document.getElementById('acao-email').value;
  if (!email) return msg('Informe o e-mail.', false);
  if (!confirm(`Excluir permanentemente ${email}?`)) return;
  const [ok, data] = await req('DELETE', '/admin/cliente', {email});
=======
  const [ok, data] = await req('POST', '/admin/renovar', { email, dias });
>>>>>>> 7dae29c1c66bf74e0c4117dcec7c1061ae60bc97
  if (ok) { msg(`✓ ${data.mensagem}`); listar(); }
  else msg(data.detail || 'Erro.', false);
}

async function listar() {
  const [ok, data] = await req('GET', '/admin/clientes');
  if (!ok) return msg('Erro ao listar. Verifique a chave admin.', false);
  const tab = document.getElementById('tabela');
  tab.innerHTML = '<tr><th>Nome</th><th>E-mail</th><th>Chave</th><th>Status</th><th>Expira em</th></tr>';
  data.forEach(c => {
<<<<<<< HEAD
    const exp  = new Date(c.expira_em);
    const hoje = new Date();
    const status = !c.ativo ? '<span class="badge inativo">Bloqueado</span>'
                 : exp < hoje ? '<span class="badge expirado">Expirado</span>'
                 : '<span class="badge ativo">Ativo</span>';
    tab.innerHTML += `<tr>
      <td>${c.nome}</td>
      <td>${c.email}</td>
      <td><code>${c.chave}</code></td>
      <td>${status}</td>
      <td>${exp.toLocaleDateString('pt-BR')}</td>
    </tr>`;
=======
    const exp   = new Date(c.expira_em);
    const hoje  = new Date();
    const status = !c.ativo ? '<span class="badge inativo">Bloqueado</span>'
                 : exp < hoje ? '<span class="badge expirado">Expirado</span>'
                 : '<span class="badge ativo">Ativo</span>';
    const expStr = exp.toLocaleDateString('pt-BR');
    tab.innerHTML += `<tr><td>${c.nome}</td><td>${c.email}</td><td><code>${c.chave}</code></td><td>${status}</td><td>${expStr}</td></tr>`;
>>>>>>> 7dae29c1c66bf74e0c4117dcec7c1061ae60bc97
  });
}
</script>
</body>
<<<<<<< HEAD
</html>"""
=======
</html>
"""
>>>>>>> 7dae29c1c66bf74e0c4117dcec7c1061ae60bc97
