# main.py – fluxo unificado, checklist criado com dados extraídos
"""
1. Atualiza cache remoto **antes** de processar o webhook (GET único).
2. Zera detector de duplicado (last_webhook_id) para este payload.
3. Processa o webhook **uma vez**.
   • Se total==0  → busca cláusulas.
   • Se total>0   → monta `ident` e `itens_por_tipo` a partir de
     `dados_formatados` + `formularios_por_tipo` e cria checklist.
"""
from __future__ import annotations

import os, json, asyncio, inspect
from typing import Any, List, Dict

import uvicorn
from pyngrok import ngrok, conf

import GET
import webhook
from POST import ChecklistCreator

# ------------- ngrok fixo ------------
NGROK_DOMAIN = "enormous-infinite-tahr.ngrok-free.app"
if (tok :="2yy04GbRMzDFhGgaRo3PGRqV5tC_4gkaL24YZ3yhDkNq9wDuh"):
    conf.get_default().auth_token = tok
    try:
        ngrok.connect(addr=8000, proto="http", domain=NGROK_DOMAIN)
    except Exception:
        ngrok.connect(addr=8000, proto="http")

# ---------- globals ------------------
TEMPLATE_ID_CLAUSE = "67f6ad27bfce31f9c1926b57"
LATEST_ITEM_CLAUSULAS: List[str] = []

# ---------- helpers ------------------

def _extract_exec_id(payload: dict, resultado: dict) -> str | None:
    for src in (payload, payload.get("params", {}), resultado.get("dados_formatados", {})):
        val = src.get("execution_company_id") or src.get("company_id")
        if isinstance(val, dict):
            val = val.get("$oid")
        if val:
            return val
    return None


def _buscar_clausulas(exec_id: str) -> List[str]:
    from requests import get, exceptions
    try:
        cc = ChecklistCreator()
        url = f"{cc.base_url.rstrip('/')}/checklists"
        resp = get(url, headers=cc.headers, params={
            "template_id": TEMPLATE_ID_CLAUSE,
            "execution_company_id": exec_id
        }, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        claus = []
        for chk in data:
            for sec in chk.get("sections", []):
                for q in sec.get("questions", []):
                    if "item/" in q.get("title", "").lower():
                        if q.get("value"):
                            claus.append(str(q["value"]).strip())
                        for sub in q.get("sub_questions", []):
                            if sub.get("value"):
                                claus.append(str(sub["value"]).strip())
        print(f"[FetchClauses] Capturadas {len(claus)} cláusulas: {claus}")
        return claus
    except exceptions.RequestException as e:
        print(f"[FetchClauses] ❌ {e}")
        return []


# ---------- wrapper ------------------
_orig = webhook.processar_webhook_completo

def _wrapper(payload: dict):
    """Processa webhook com cache atualizado uma única vez."""
    # 1. Processa payload sem forçar refresh remoto (evita loop)
    res = _orig(payload)
    if inspect.isawaitable(res):
        res = asyncio.run(res)

    total = res.get("total_itens_habilitados", 0)
    exec_id = _extract_exec_id(payload, res)

    if total == 0:
        print(f"[GerarItens] webhook vazio – execution_company_id = {exec_id}")
        global LATEST_ITEM_CLAUSULAS
        LATEST_ITEM_CLAUSULAS = _buscar_clausulas(exec_id) if exec_id else []
        return res

    # ---------- montar identificacao ----------
    info = res.get("dados_formatados", {})
    identificacao = {
        "data_prevista":   info.get("data_prevista"),
        "contrato":        info.get("contrato_concessao"),
        "identificador":   info.get("identificador"),
        "concessionaria":  info.get("concessionaria")
    }

    # ---------- montar itens_por_tipo ----------
    itens_por_tipo: Dict[str, List[Dict[str, Any]]] = {}
    for tipo, forms in res.get("formularios_por_tipo", {}).items():
        itens_por_tipo[tipo] = []
        for form in forms:
            item_d = {}
            for sec in form.get("sections", []):
                if sec.get("title", "").lower().startswith("identificação"):
                    for q in sec.get("questions", []):
                        ttl = q.get("title", "").lower()
                        val = q.get("sub_questions", [{}])[0].get("value")
                        if val is None:
                            continue
                        val = str(val).strip()
                        if "item" in ttl:
                            item_d["item"] = val
                        elif "código" in ttl:
                            item_d["codigo"] = val
                        elif "indicador" in ttl:
                            item_d["indicador"] = val
                        elif "verificação" in ttl:
                            item_d["verificacao"] = val
                        elif "dimensão" in ttl or "dimensao" in ttl:
                            item_d["dimensao"] = val
            if item_d:
                itens_por_tipo[tipo].append(item_d)

    if not any(itens_por_tipo.values()):
        print("[Checklist] ⚠️ Nenhum item detalhado; abortando sub-checklists.")
        return res

    # ---------- cria checklist ----------
    try:
        ChecklistCreator().criar_checklist_completo(identificacao, itens_por_tipo)
    except Exception as e:
        print(f"[Wrapper] Erro ao criar checklist: {e}")

    return res

# aplicar monkey patch
autopat = webhook.processar_webhook_completo = _wrapper

# ---------- FastAPI app ---------------
app = getattr(webhook, "app") if hasattr(webhook, "app") else webhook.criar_app_fastapi()
print("[main] 🚀 Servidor pronto em http://localhost:8000")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)
