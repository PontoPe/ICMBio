import json
import inspect
import hashlib
from datetime import datetime
from typing import List, Dict, Any

from fastapi import FastAPI, Request
from requests import get, exceptions

import GET
from POST import ChecklistCreator

# ==================================
#    CONFIGURAÇÃO E VARIÁVEIS GLOBAIS
# ==================================

last_webhook_id = None
TEMPLATE_ID_CLAUSE = "67f6ad27bfce31f9c1926b57"


# ==================================
#         FUNÇÕES AUXILIARES
# ==================================

def GerarItens(exec_id: str) -> List[str]:
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

def _extract_exec_id(payload: dict) -> str | None:
    """Extrai o ID da empresa de execução do payload."""
    if payload and isinstance(payload.get("execution_company_id"), dict):
        return payload.get("execution_company_id", {}).get("$oid")
    return None

def _buscar_clausulas_padrao(exec_id: str) -> List[str]:
    """Busca as cláusulas padrão de um checklist de referência."""
    try:
        cc = ChecklistCreator()
        url = f"{cc.base_url.rstrip('/')}/checklists"
        resp = get(url, headers=cc.headers, params={
            "template_id": TEMPLATE_ID_CLAUSE,
            "execution_company_id": exec_id
        }, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        claus = [
            str(sub.get("value")).strip()
            for chk in data
            for sec in chk.get("sections", [])
            for q in sec.get("questions", [])
            if "item/" in q.get("title", "").lower()
            for sub in q.get("sub_questions", [])
            if sub.get("value")
        ]
        print(f"[FetchClauses] Capturadas {len(claus)} cláusulas padrão: {claus}")
        return claus
    except exceptions.RequestException as e:
        print(f"[FetchClauses] ❌ {e}")
        return []

def processar_item_checklist(checklist, tipo):
    """
    Processa um item do checklist (FT, FA, FO, GC, VC)
    """
    item_info = {
        "item": None,
        "habilitado": False,
        "tipo": tipo
    }

    for question in checklist.get("sub_checklist_questions", []):
        if question.get("question") == f"Item ({tipo})":
            item_info["item"] = question.get("value")
        elif question.get("question") == f"Enviar para execução ({tipo})":
            item_info["habilitado"] = question.get("value") == "true"

    return item_info if item_info["item"] else None


def extrair_informacoes_planejamento(data):
    """
    Extrai e formata as informações relevantes do webhook de planejamento
    """
    informacoes = {
        "identificador": None,
        "data_prevista": None,
        "contrato_concessao": None,
        "concessionaria": None,
        "itens_ft": [],
        "itens_fa": [],
        "itens_fo": [],
        "itens_gc": [],
        "itens_vc": [],
        "total_itens": 0
    }

    # Extrair informações das questões do template
    for question in data.get("template_questions", []):
        if question.get("question") == "Identificador":
            informacoes["identificador"] = question.get("value")
        elif question.get("question") == "Data prevista para a realização do checklist":
            informacoes["data_prevista"] = question.get("value")
        elif question.get("question") == "Contrato de concessão":
            informacoes["contrato_concessao"] = question.get("value")
        elif question.get("question") == "Concessionária":
            informacoes["concessionaria"] = question.get("value")
        elif question.get("question") == "Gerar checklist":
            informacoes["gerar_checklist_manual"] = question.get("value") == "true"
        elif question.get("question") == "Adicionar itens - Fiscalização Técnica":
            # Processar itens FT
            for checklist in question.get("sub_checklists", []):
                item_info = processar_item_checklist(checklist, "FT")
                if item_info:
                    informacoes["itens_ft"].append(item_info)
        elif question.get("question") == "Adicionar itens - Fiscalização Administrativa":
            # Processar itens FA
            for checklist in question.get("sub_checklists", []):
                item_info = processar_item_checklist(checklist, "FA")
                if item_info:
                    informacoes["itens_fa"].append(item_info)
        elif question.get("question") == "Adicionar itens - Fiscalização de Obras (COPEA)":
            # Processar itens FO
            for checklist in question.get("sub_checklists", []):
                item_info = processar_item_checklist(checklist, "FO")
                if item_info:
                    informacoes["itens_fo"].append(item_info)
        elif question.get("question") == "Adicionar itens - Gestão do Contrato":
            # Processar itens GC
            for checklist in question.get("sub_checklists", []):
                item_info = processar_item_checklist(checklist, "GC")
                if item_info:
                    informacoes["itens_gc"].append(item_info)
        elif question.get("question") == "Adicionar itens - Verificador de Conformidade":
            # Processar itens VC
            for checklist in question.get("sub_checklists", []):
                item_info = processar_item_checklist(checklist, "VC")
                if item_info:
                    informacoes["itens_vc"].append(item_info)


    return informacoes

def get_total_itens(info: dict):
    """Calcula o total de itens habilitados."""
    itens_habilitados = []
    itens_habilitados_dict = {"total": [], "FA": [], "FT": [], "FO": [], "GC": [], "VC": []}
    total = 0
    for tipo in ['itens_ft', 'itens_fa', 'itens_fo', 'itens_gc', 'itens_vc']:
        for item in info[tipo]:
            if item['habilitado']:
                itens_habilitados.append({
                    "item": item['item'],
                    "tipo": item['tipo']
                })
                itens_habilitados_dict[item['tipo']].append(item['item'])
                itens_habilitados_dict["total"].append(item['item'])
                print(f"Item habilitado: {item['item']} ({item['tipo']})")
                total += 1
    print(f"{itens_habilitados_dict}")
    return itens_habilitados_dict



# ==================================
#     LÓGICA DOS ENDPOINTS
# ==================================

async def handle_webhook(payload: dict):
    """Lógica para o endpoint /webhook (geração manual)."""
    info = extrair_informacoes_planejamento(payload)
    total_itens = len(get_total_itens(info)["total"])
    print(f"Total de itens habilitados: {total_itens}")
    print("\n--- PROCESSANDO ENDPOINT /webhook (MANUAL) ---")
    print(f"Itens manuais selecionados: {total_itens}")
    print(f"Flag 'Gerar checklist' encontrada: {info.get('gerar_checklist_manual')}")
    form_id = payload.get('_id', {}).get('$oid')
    print(f"✅ ID do Formulário do webhook_itens capturado: {form_id}")
    if not info.get('gerar_checklist_manual') and total_itens > 0:
        print(f"ID do Formulário: {form_id}")
        print("Itens selecionados, mas flag 'Gerar checklist' não marcada. Fazendo.... nada.")
    elif info.get('gerar_checklist_manual') and total_itens > 0:
        print("✅ Condições atendidas para /webhook. Iniciando criação do checklist.")
        itens_para_api = {}
        buscador = GET.FormulariosBuscador()
        buscador.carregar_e_salvar_formularios()

        for tipo_key in ['itens_ft', 'itens_fa', 'itens_fo', 'itens_gc', 'itens_vc']:
            tipo_abbr = tipo_key.replace('itens_', '').upper()
            clausulas = [item['item'] for item in info[tipo_key]]
            if clausulas:
                formularios = GET.buscar_clausulas(clausulas, mostrar_detalhes=False)
                itens_para_api[tipo_abbr] = []
                for form in formularios:
                    detalhes = buscador.extrair_informacoes_formulario(form)
                    item_d = {
                            "item": detalhes.get("item", ""),
                            "codigo": detalhes.get("codigo", ""),
                            "instrumento": detalhes.get("instrumento", ""),
                            "dimensao": detalhes.get("dimensao", ""),
                            "verificacao": detalhes.get("verificacao", ""),
                            "av": detalhes.get("av", ""),
                            "peso": detalhes.get("peso", ""),
                            "indicador": detalhes.get("indicador", "")
                            }
                    itens_para_api[tipo_abbr].append(item_d)
        
        identificacao = {k: info.get(k) for k in ["data_prevista", "contrato_concessao", "identificador", "concessionaria"]}
        
        creator = ChecklistCreator()
        user_id = payload.get("user_id", {}).get("$oid")
        print(f"Itens para API: \n{itens_para_api}")
        checklist_id = creator.criar_checklist_completo(
            identificacao=identificacao,
            itens_por_tipo=itens_para_api,
            assignee_id=user_id,
            creator_id=user_id
        )
        if checklist_id:
            return {"status": "sucesso", "endpoint": "/webhook", "checklist_id": checklist_id}
        else:
            return {"status": "falha", "endpoint": "/webhook", "motivo": "Erro na criação do checklist via API."}
    elif total_itens == 0:
        #usar ChecklistCreator.adicionar_subchecklists para gerar subchecklists, usando o ID do formulário
        print("✅ Condições atendidas para /webhook, mas nenhum item selecionado. Iniciando geração de subchecklists.")
        comp_id = _extract_exec_id(payload)
        clausulas = GET._buscar_clausulas(comp_id)
        cc = ChecklistCreator()
        if not clausulas:
            print("❌ Nenhuma cláusula encontrada para gerar subchecklists.")
            return {"status": "falha", "endpoint": "/webhook", "motivo": "Nenhuma cláusula encontrada."}
        else:
            cc.adicionar_subchecklists_itens(form_id, clausulas)

        #cc.adicionar_subchecklists(form_id, "FA", )
    else:
        print("❌ Condições para /webhook não atendidas. Encerrando.")
        return {"status": "ignorado", "endpoint": "/webhook", "motivo": "Condições não atendidas."}


async def handle_webhook_itens(payload: dict):
    """Lógica para o endpoint /webhook_itens (geração automática)."""
    # NOVO: Armazena o ID do formulário em uma variável
    form_id = payload.get('_id', {}).get('$oid')
    print(f"✅ ID do Formulário do webhook_itens capturado: {form_id}")

    info = extrair_informacoes_planejamento(payload)
    total_itens = get_total_itens(info)
    exec_id = _extract_exec_id(payload)

    print("\n--- PROCESSANDO ENDPOINT /webhook_itens (AUTOMÁTICO) ---")
    print(f"Itens manuais selecionados: {total_itens}")
    print(f"Flag 'Gerar Itens' encontrada: {info.get('gerar_itens_auto')}")

    if info.get('gerar_itens_auto') and total_itens == 0:
        print("✅ Condições atendidas para /webhook_itens. Iniciando busca de cláusulas padrão.")
        
        clausulas_padrao = _buscar_clausulas_padrao(exec_id)
        if not clausulas_padrao:
            return {"status": "falha", "endpoint": "/webhook_itens", "motivo": "Flag de geração automática marcada, mas nenhuma cláusula padrão foi encontrada."}
        
        print("*"*50)
        print(">>> AÇÃO: CHAMAR O SEGUNDO POST (A SER CRIADO) <<<")
        print(f"Cláusulas para o novo POST: {clausulas_padrao}")
        print(f"ID do Formulário original a ser usado: {form_id}") # NOVO: Mostra o ID
        print("*"*50)
        
        # ALTERADO: Inclui o ID do formulário na resposta
        return {
            "status": "sucesso_placeholder",
            "endpoint": "/webhook_itens",
            "form_id_processado": form_id, 
            "clausulas_encontradas": len(clausulas_padrao)
        }

    else:
        print("❌ Condições para /webhook_itens não atendidas. Encerrando.")
        return {"status": "ignorado", "endpoint": "/webhook_itens", "motivo": "Condições não atendidas."}


# ==================================
#         APLICAÇÃO FASTAPI
# ==================================

def criar_app_fastapi():
    """Cria e configura a aplicação FastAPI com todos os endpoints."""
    app = FastAPI()

    async def processar_payload(request: Request, handler):
        """Função genérica para pré-processar webhooks."""
        global last_webhook_id
        try:
            body = await request.json()
        except json.JSONDecodeError:
            return {"status": "erro", "motivo": "Payload inválido, não é um JSON."}
        
        #print("\n" + "="*20 + " INÍCIO DO WEBHOOK RAW " + "="*20)
        #print(f">>> WEBHOOK RECEBIDO EM: {request.url.path}")
        #print(json.dumps(body, indent=2, ensure_ascii=False))
        #print("="*22 + " FIM DO WEBHOOK RAW " + "="*23 + "\n")

        webhook_content = json.dumps(body, sort_keys=True)
        current_id = hashlib.md5(webhook_content.encode()).hexdigest()
        if current_id == last_webhook_id:
            print("🔄 Webhook duplicado detectado - ignorando")
            return {"status": "ignorado", "reason": "duplicate_request"}
        
        last_webhook_id = current_id
        print(f"🚀 Processando novo webhook (ID: {current_id[:8]}...).")
        
        if inspect.iscoroutinefunction(handler):
            return await handler(body)
        else:
            return handler(body)

    @app.post("/webhook")
    async def webhook_endpoint(request: Request):
        return await processar_payload(request, handle_webhook)

    @app.post("/webhook_itens")
    async def webhook_itens_endpoint(request: Request):
        return await processar_payload(request, handle_webhook_itens)

    return app
