# webhook.py - Apenas funcionalidades do webhook (sem execução)

import json
from datetime import datetime
from typing import List, Dict
from fastapi import FastAPI, Request
import GET

# Lista para armazenar apenas os itens habilitados do último webhook
itens_habilitados_ultimo = []
last_webhook_id = None  # Variável global para armazenar o ID do último webhook processado


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
        "itens_vc": []
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


def formatar_saida(informacoes):
    """
    Formata as informações para saída legível
    """
    output = []
    output.append("=== INFORMAÇÕES DO PLANEJAMENTO ===")
    output.append(f"Identificador: {informacoes['identificador']}")
    output.append(f"Data Prevista: {informacoes['data_prevista']}")
    output.append(f"Contrato de Concessão: {informacoes['contrato_concessao']}")
    output.append(f"Concessionária: {informacoes['concessionaria']}")

    # FT
    output.append("\n=== ITENS DE FISCALIZAÇÃO TÉCNICA (FT) ===")
    if informacoes['itens_ft']:
        for item in informacoes['itens_ft']:
            status = "✅ HABILITADO" if item['habilitado'] else "❌ DESABILITADO"
            output.append(f"  - Item {item['item']}: {status}")
    else:
        output.append("  Nenhum item FT selecionado")

    # FA
    output.append("\n=== ITENS DE FISCALIZAÇÃO ADMINISTRATIVA (FA) ===")
    if informacoes['itens_fa']:
        for item in informacoes['itens_fa']:
            status = "✅ HABILITADO" if item['habilitado'] else "❌ DESABILITADO"
            output.append(f"  - Item {item['item']}: {status}")
    else:
        output.append("  Nenhum item FA selecionado")

    # FO
    output.append("\n=== ITENS DE FISCALIZAÇÃO DE OBRAS (FO) ===")
    if informacoes['itens_fo']:
        for item in informacoes['itens_fo']:
            status = "✅ HABILITADO" if item['habilitado'] else "❌ DESABILITADO"
            output.append(f"  - Item {item['item']}: {status}")
    else:
        output.append("  Nenhum item FO selecionado")

    # GC
    output.append("\n=== ITENS DE GESTÃO DO CONTRATO (GC) ===")
    if informacoes['itens_gc']:
        for item in informacoes['itens_gc']:
            status = "✅ HABILITADO" if item['habilitado'] else "❌ DESABILITADO"
            output.append(f"  - Item {item['item']}: {status}")
    else:
        output.append("  Nenhum item GC selecionado")

    # VC
    output.append("\n=== ITENS DE VERIFICADOR DE CONFORMIDADE (VC) ===")
    if informacoes['itens_vc']:
        for item in informacoes['itens_vc']:
            status = "✅ HABILITADO" if item['habilitado'] else "❌ DESABILITADO"
            output.append(f"  - Item {item['item']}: {status}")
    else:
        output.append("  Nenhum item VC selecionado")

    return "\n".join(output)


def atualizar_cache_formularios():
    """
    Sempre atualiza o cache de formulários a cada ativação do webhook
    """
    print("🔄 Atualizando cache de formulários...")
    sucesso = GET.carregar_formularios(forcar_nova_requisicao=True)

    if sucesso:
        print("✅ Cache de formulários atualizado com sucesso!")
        return True
    else:
        print("❌ Falha ao atualizar cache de formulários.")
        return False


def processar_itens_habilitados(informacoes):
    """
    Processa todos os itens habilitados de forma otimizada
    """
    # O cache já foi garantido no endpoint do webhook

    # Coletar todos os itens habilitados por tipo
    tipos_itens = {
        'FT': [item['item'] for item in informacoes['itens_ft'] if item['habilitado']],
        'FA': [item['item'] for item in informacoes['itens_fa'] if item['habilitado']],
        'FO': [item['item'] for item in informacoes['itens_fo'] if item['habilitado']],
        'GC': [item['item'] for item in informacoes['itens_gc'] if item['habilitado']],
        'VC': [item['item'] for item in informacoes['itens_vc'] if item['habilitado']]
    }

    print("\n" + "=" * 60)
    print("🔍 PROCESSANDO ITENS HABILITADOS COM CACHE OTIMIZADO")
    print("=" * 60)

    # Processar cada tipo de item
    resultados_processamento = {}

    for tipo, itens_habilitados in tipos_itens.items():
        if not itens_habilitados:
            print(f"\n🔶 {tipo}: Nenhum item habilitado.")
            resultados_processamento[tipo] = []
            continue

        print(f"\n🔍 {tipo}: Processando {len(itens_habilitados)} itens habilitados: {itens_habilitados}")
        print("-" * 40)

        try:
            # Usar a busca no cache (muito mais rápida)
            formularios_encontrados = GET.buscar_clausulas(itens_habilitados, mostrar_detalhes=True)

            print(f"✅ {tipo}: {len(formularios_encontrados)} formulários encontrados para os itens habilitados.")

            resultados_processamento[tipo] = formularios_encontrados

        except Exception as e:
            print(f"❌ Erro ao processar itens {tipo}: {e}")
            resultados_processamento[tipo] = []

    return resultados_processamento


def atualizar_itens_habilitados_global(informacoes):
    """
    Atualiza a lista global de itens habilitados
    """
    global itens_habilitados_ultimo

    # Limpar lista anterior e adicionar apenas itens habilitados
    itens_habilitados_ultimo = []

    # Adicionar todos os itens habilitados à lista global
    for tipo in ['itens_ft', 'itens_fa', 'itens_fo', 'itens_gc', 'itens_vc']:
        for item in informacoes[tipo]:
            if item['habilitado']:
                itens_habilitados_ultimo.append({
                    "item": item['item'],
                    "tipo": item['tipo']
                })


def salvar_dados_webhook(body, informacoes):
    """
    Salva dados do webhook para debug
    """
    with open("ultimo_webhook.json", "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "original": body,
            "formatado": informacoes,
            "itens_habilitados": itens_habilitados_ultimo
        }, f, ensure_ascii=False, indent=2)


def processar_webhook_completo(body):
    """
    Função principal que processa todo o webhook

    Args:
        body: Dados JSON recebidos pelo webhook

    Returns:
        dict: Resposta formatada do processamento
    """
    global last_webhook_id

    # Generate a unique ID from the webhook content
    import hashlib
    webhook_content = json.dumps(body, sort_keys=True)
    current_id = hashlib.md5(webhook_content.encode()).hexdigest()

    # Check if this is a duplicate
    if current_id == last_webhook_id:
        print("🔄 Duplicate webhook detected - ignoring")
        return {"status": "ignored", "reason": "duplicate_request"}

    # Save this ID
    last_webhook_id = current_id
    print("🚀 Webhook recebido!")

    # SEMPRE ATUALIZA O CACHE A CADA ATIVAÇÃO
    print("📡 Iniciando atualização do cache de formulários...")
    if not atualizar_cache_formularios():
        return {
            "status": "erro",
            "message": "Falha ao atualizar cache de formulários",
            "timestamp": datetime.now().isoformat()
        }

    # Extrair informações formatadas
    informacoes = extrair_informacoes_planejamento(body)

    # Atualizar lista global de itens habilitados
    atualizar_itens_habilitados_global(informacoes)

    # Exibir informações formatadas
    print("\n" + formatar_saida(informacoes))

    # Mostrar lista de itens habilitados
    print("\n=== LISTA DE ITENS HABILITADOS ===")
    if itens_habilitados_ultimo:
        for item in itens_habilitados_ultimo:
            print(f"  - {item['tipo']}: {item['item']}")
    else:
        print("  Nenhum item habilitado")

    # Salvar dados do webhook para debug
    salvar_dados_webhook(body, informacoes)

    # Processar todos os itens habilitados de forma otimizada
    resultados = processar_itens_habilitados(informacoes)

    # MODIFICAÇÃO: Adicionar os formulários encontrados ao response
    formularios_por_tipo = {}
    for tipo, formularios in resultados.items():
        if formularios:
            formularios_por_tipo[tipo] = formularios

    # Retornar resposta com formulários
    response = {
        "status": "sucesso",
        "dados_formatados": informacoes,
        "itens_habilitados": itens_habilitados_ultimo,
        "total_itens_habilitados": len(itens_habilitados_ultimo),
        "resultados_processamento": {tipo: len(resultado) for tipo, resultado in resultados.items()},
        "formularios_por_tipo": formularios_por_tipo  # NOVO: Adicionar formulários
    }

    return response


def obter_itens_habilitados():
    """
    Retorna os itens habilitados do último webhook
    """
    return {
        "total": len(itens_habilitados_ultimo),
        "itens": itens_habilitados_ultimo
    }


def criar_app_fastapi():
    """
    Cria e configura a aplicação FastAPI com todos os endpoints
    """
    app = FastAPI()

    @app.post("/webhook_itens")
    async def webhook_itens_endpoint(request: Request):
        body = await request.json()
        return processar_webhook_completo(body)

    @app.post("/webhook")
    async def webhook_endpoint(request: Request):
        body = await request.json()
        return processar_webhook_completo(body)

    @app.get("/itens-habilitados")
    async def listar_itens_habilitados():
        """
        Endpoint para consultar os itens habilitados do último webhook
        """
        return obter_itens_habilitados()

    @app.get("/recarregar-cache")
    async def recarregar_cache():
        """
        Endpoint para forçar recarregamento do cache de formulários
        """
        print("🔄 Forçando recarregamento do cache...")

        sucesso = GET.carregar_formularios(forcar_nova_requisicao=True)

        if sucesso:
            return {"status": "sucesso", "message": "Cache recarregado com sucesso"}
        else:
            return {"status": "erro", "message": "Falha ao recarregar cache"}

    @app.get("/status-cache")
    async def status_cache():
        """
        Endpoint para verificar status do cache
        """
        import os

        cache_existe = os.path.exists('cache_formularios.json')

        status = {
            "arquivo_cache_existe": cache_existe,
            "cache_atualizado_a_cada_webhook": True
        }

        if cache_existe:
            try:
                timestamp_arquivo = datetime.fromtimestamp(os.path.getmtime('cache_formularios.json'))
                with open('cache_formularios.json', 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)

                status.update({
                    "timestamp_ultimo_cache": timestamp_arquivo.isoformat(),
                    "total_formularios": cache_data.get('total_formularios', 0),
                    "idade_cache_horas": (datetime.now() - timestamp_arquivo).total_seconds() / 3600
                })
            except Exception as e:
                status["erro_cache"] = str(e)

        return status

    return app