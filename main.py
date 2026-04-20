"""
API de Licenciamento — Futvôlei Replay
PostgreSQL via psycopg2 — dados persistentes no Render.
"""

import os
import secrets
from datetime import datetime, timezone, timedelta
from contextlib import asynccontextmanager

import psycopg2
import psycopg2.extras
from fastapi import FastAPI, HTTPException, Header, Query
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

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


def verificar_admin(x_admin_key: str = Header(...)):
    if not secrets.compare_digest(x_admin_key, ADMIN_KEY):
        raise HTTPException(status_code=401, detail="Chave admin inválida.")


class NovoCliente(BaseModel):
    email: str
    nome:  str
    dias:  int = DAYS_DEFAULT


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

    if agora > expira:
        return {"valido": False, "mensagem": "Licença expirada. Entre em contato para renovar."}

    dias_restantes = (expira - agora).days
    return {
        "valido":         True,
        "mensagem":       f"Licença válida. {dias_restantes} dia(s) restante(s).",
        "dias_restantes": dias_restantes,
        "nome":           row["nome"],
    }


# ── Endpoints admin ───────────────────────────────────────────────────────────

@app.get("/admin/clientes")
def listar_clientes(x_admin_key: str = Header(...)):
    verificar_admin(x_admin_key)
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
<html lang="pt-br">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
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
  </div>
</div>

<div class="card">
  <h2>Clientes cadastrados</h2>
  <button class="btn-gray" onclick="listar()" style="width:auto;margin-bottom:16px;padding:6px 16px">↻ Atualizar lista</button>
  <table id="tabela">
    <tr><th>Nome</th><th>E-mail</th><th>Chave</th><th>Status</th><th>Expira em</th></tr>
  </table>
</div>

<script>
const key = () => document.getElementById('admin-key').value;

function msg(text, ok=true) {
  const el = document.getElementById('msg');
  el.textContent = text;
  el.className = ok ? 'ok' : 'err';
  el.style.display = 'block';
  setTimeout(() => el.style.display = 'none', 5000);
}

async function req(method, path, body=null) {
  const opts = {method, headers:{'X-Admin-Key':key(),'Content-Type':'application/json'}};
  if (body) opts.body = JSON.stringify(body);
  const r = await fetch(path, opts);
  return [r.ok, await r.json()];
}

async function cadastrar() {
  const nome  = document.getElementById('novo-nome').value;
  const email = document.getElementById('novo-email').value;
  const dias  = parseInt(document.getElementById('novo-dias').value);
  if (!nome || !email) return msg('Preencha nome e e-mail.', false);
  const [ok, data] = await req('POST', '/admin/cliente', {nome, email, dias});
  if (ok) { msg(`✓ ${data.mensagem} | Chave: ${data.chave} | Expira: ${data.expira_em}`); listar(); }
  else msg(data.detail || 'Erro.', false);
}

async function bloquear() {
  const email = document.getElementById('acao-email').value;
  if (!email) return msg('Informe o e-mail.', false);
  const [ok, data] = await req('POST', '/admin/bloquear', {email});
  if (ok) { msg(`✓ ${data.mensagem}`); listar(); }
  else msg(data.detail || 'Erro.', false);
}

async function renovar() {
  const email = document.getElementById('acao-email').value;
  const dias  = parseInt(document.getElementById('acao-dias').value);
  if (!email) return msg('Informe o e-mail.', false);
  const [ok, data] = await req('POST', '/admin/renovar', {email, dias});
  if (ok) { msg(`✓ ${data.mensagem}`); listar(); }
  else msg(data.detail || 'Erro.', false);
}

async function excluir() {
  const email = document.getElementById('acao-email').value;
  if (!email) return msg('Informe o e-mail.', false);
  if (!confirm(`Excluir permanentemente ${email}?`)) return;
  const [ok, data] = await req('DELETE', '/admin/cliente', {email});
  if (ok) { msg(`✓ ${data.mensagem}`); listar(); }
  else msg(data.detail || 'Erro.', false);
}

async function listar() {
  const [ok, data] = await req('GET', '/admin/clientes');
  if (!ok) return msg('Erro ao listar. Verifique a chave admin.', false);
  const tab = document.getElementById('tabela');
  tab.innerHTML = '<tr><th>Nome</th><th>E-mail</th><th>Chave</th><th>Status</th><th>Expira em</th></tr>';
  data.forEach(c => {
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
  });
}
</script>
</body>
</html>"""
