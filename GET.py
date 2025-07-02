import requests
import json
import sys
import os
from datetime import datetime, timedelta


class FormulariosBuscador:
    def __init__(self, arquivo_cache='cache_formularios.json'):
        self.url = "https://app.way-v.com/api/integration/checklists"
        self.token = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJjb21wYW55X2lkIjoiNjYzZDMxYTFlOWRhYzNmNWY0ZDNjZjJlIiwiY3VycmVudF90aW1lIjoxNzQ4OTUzODcyNjgzLCJleHAiOjIwNjQ0ODY2NzJ9.j6zOrJMDKNcCcMMcO99SudriP7KqEDLMJDE2FBlQ6ok'
        self.params = {
            "execution_company_id": '663d31a1e9dac3f5f4d3cf2e',
            "template_id": '67f6ae4d6ba4f07ba32a1ea8'
        }
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        self.arquivo_cache = arquivo_cache

    def carregar_e_salvar_formularios(self, forcar_nova_requisicao=False):
        """
        Método 1: Faz a requisição GET e salva todos os dados em arquivo temporário

        Args:
            forcar_nova_requisicao (bool): Se True, força uma nova requisição mesmo se o cache existe

        Returns:
            bool: True se bem-sucedido, False caso contrário
        """
        # Verificar se o cache existe e é recente (menos de 1 hora)
        if not forcar_nova_requisicao and os.path.exists(self.arquivo_cache):
            try:
                # Verificar idade do arquivo
                tempo_arquivo = datetime.fromtimestamp(os.path.getmtime(self.arquivo_cache))
                tempo_atual = datetime.now()

                if tempo_atual - tempo_arquivo < timedelta(hours=1):
                    print(
                        f"📋 Cache válido encontrado em '{self.arquivo_cache}' (criado há {tempo_atual - tempo_arquivo})")
                    return True
                else:
                    print(f"⏰ Cache expirado (criado há {tempo_atual - tempo_arquivo}). Fazendo nova requisição...")
            except Exception as e:
                print(f"⚠️ Erro ao verificar cache: {e}. Fazendo nova requisição...")

        try:
            print("🌐 Fazendo requisição GET para buscar todos os formulários...")
            print(f"🔗 URL: {self.url}")
            print(f"📋 Params: {self.params}")

            response = requests.get(self.url, headers=self.headers, params=self.params)

            print(f"📡 Status Code: {response.status_code}")

            if response.status_code != 200:
                print(f"❌ Erro {response.status_code}")
                print(f"📄 Response text: {response.text}")
                return False

            dados_json = response.json()
            print(f"📊 Tipo de dados recebidos: {type(dados_json)}")

            # Processar diferentes formatos de resposta
            dados_formularios = None

            if isinstance(dados_json, list):
                dados_formularios = dados_json
                print(f"✅ Lista direta recebida! {len(dados_formularios)} formulários.")
            elif isinstance(dados_json, dict):
                print(f"📝 Objeto recebido. Chaves disponíveis: {list(dados_json.keys())}")
                # Tentar encontrar a lista de formulários
                if 'data' in dados_json:
                    dados_formularios = dados_json['data']
                elif 'results' in dados_json:
                    dados_formularios = dados_json['results']
                elif 'items' in dados_json:
                    dados_formularios = dados_json['items']
                else:
                    print("❌ Não foi possível encontrar a lista de formulários no JSON retornado")
                    return False
                print(f"✅ Formulários extraídos! {len(dados_formularios)} formulários encontrados.")
            else:
                print(f"❌ Formato de dados inesperado: {type(dados_json)}")
                return False

            # Criar estrutura de cache com metadados
            cache_data = {
                "timestamp": datetime.now().isoformat(),
                "total_formularios": len(dados_formularios),
                "dados": dados_formularios
            }

            # Salvar no arquivo de cache
            with open(self.arquivo_cache, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)

            print(f"💾 Dados salvos no cache '{self.arquivo_cache}'")
            print(f"✅ Total de formulários salvos: {len(dados_formularios)}")

            return True

        except requests.exceptions.RequestException as e:
            print(f"❌ Erro na requisição: {e}")
            return False
        except json.JSONDecodeError as e:
            print(f"❌ Erro ao decodificar JSON: {e}")
            if 'response' in locals():
                print(f"📄 Response text: {response.text[:500]}...")
            return False
        except Exception as e:
            print(f"❌ Erro inesperado: {e}")
            return False

    def buscar_por_clausulas_no_cache(self, clausulas_desejadas):
        """
        Método 2: Busca formulários por cláusulas usando o arquivo de cache

        Args:
            clausulas_desejadas (list): Lista de strings com os números das cláusulas

        Returns:
            list: Lista de formulários filtrados
        """
        # Verificar se o arquivo de cache existe
        if not os.path.exists(self.arquivo_cache):
            print(f"❌ Arquivo de cache '{self.arquivo_cache}' não encontrado.")
            print("💡 Execute primeiro carregar_e_salvar_formularios() para criar o cache.")
            return []

        try:
            # Carregar dados do cache
            print(f"📂 Carregando dados do cache '{self.arquivo_cache}'...")
            with open(self.arquivo_cache, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)

            # Verificar estrutura do cache
            if 'dados' not in cache_data:
                print("❌ Estrutura de cache inválida. Campo 'dados' não encontrado.")
                return []

            dados_formularios = cache_data['dados']
            timestamp_cache = cache_data.get('timestamp', 'Desconhecido')
            total_formularios = cache_data.get('total_formularios', len(dados_formularios))

            print(f"✅ Cache carregado com sucesso!")
            print(f"   📅 Criado em: {timestamp_cache}")
            print(f"   📊 Total de formulários: {total_formularios}")

            # Filtrar formulários
            formularios_filtrados = []
            clausulas_encontradas = set()

            print(f"🔍 Buscando por cláusulas: {clausulas_desejadas}")

            for formulario in dados_formularios:
                # Procurar pela seção 'Identificação' e questão 'item/Cláusula'
                for secao in formulario.get('sections', []):
                    if secao.get('title') == 'Identificação':
                        for questao in secao.get('questions', []):
                            if questao.get('title') == 'item/Cláusula':
                                # Verificar se o valor da cláusula está na lista desejada
                                for sub_questao in questao.get('sub_questions', []):
                                    clausula_valor = sub_questao.get('value')
                                    if clausula_valor in clausulas_desejadas:
                                        formularios_filtrados.append(formulario)
                                        clausulas_encontradas.add(clausula_valor)
                                        break
                        break

            # Mostrar resultado da busca
            print(f"\n📊 Resultado da busca:")
            for clausula in clausulas_desejadas:
                if clausula in clausulas_encontradas:
                    print(f"✅ Encontrada cláusula: {clausula}")
                else:
                    print(f"❌ Cláusula não encontrada: {clausula}")

            print(f"📋 Total de formulários encontrados: {len(formularios_filtrados)}")

            return formularios_filtrados

        except json.JSONDecodeError as e:
            print(f"❌ Erro ao ler arquivo de cache: {e}")
            return []
        except Exception as e:
            print(f"❌ Erro inesperado ao buscar no cache: {e}")
            return []

    def extrair_informacoes_formulario(self, formulario):
        """
        Extrai as principais informações de um formulário

        Args:
            formulario (dict): Dicionário com dados do formulário

        Returns:
            dict: Dicionário com informações estruturadas
        """
        info = {
            'id': formulario.get('id'),
            'template_name': formulario.get('template', {}).get('name'),
            'created_at': formulario.get('created_at'),
            'assignee': f"{formulario.get('assignee', {}).get('first_name', '')} {formulario.get('assignee', {}).get('last_name', '')}".strip()
        }

        # Extrair informações da seção Identificação
        for secao in formulario.get('sections', []):
            if secao.get('title') == 'Identificação':
                for questao in secao.get('questions', []):
                    titulo = questao.get('title')
                    valor = questao.get('sub_questions', [{}])[0].get('value') if questao.get('sub_questions') else None
                    info[titulo.lower().replace('/', '_').replace(' ', '_')] = valor

        return info

    def limpar_cache(self):
        """
        Remove o arquivo de cache
        """
        if os.path.exists(self.arquivo_cache):
            os.remove(self.arquivo_cache)
            print(f"🗑️ Cache '{self.arquivo_cache}' removido.")
        else:
            print(f"ℹ️ Cache '{self.arquivo_cache}' não existe.")


# Funções de conveniência para uso direto
def carregar_formularios(forcar_nova_requisicao=False):
    """
    Função de conveniência para carregar formulários
    """
    buscador = FormulariosBuscador()
    return buscador.carregar_e_salvar_formularios(forcar_nova_requisicao)


def buscar_clausulas(clausulas_desejadas, mostrar_detalhes=True):
    """
    Função de conveniência para buscar cláusulas no cache

    Args:
        clausulas_desejadas (list): Lista de cláusulas para buscar
        mostrar_detalhes (bool): Se deve mostrar detalhes dos formulários encontrados

    Returns:
        list: Lista de formulários encontrados
    """
    buscador = FormulariosBuscador()
    formularios = buscador.buscar_por_clausulas_no_cache(clausulas_desejadas)

    if mostrar_detalhes and formularios:
        print(f"\n📋 DETALHES DOS FORMULÁRIOS ENCONTRADOS:")
        print("-" * 60)

        for i, formulario in enumerate(formularios, 1):
            info = buscador.extrair_informacoes_formulario(formulario)
            print(f"\n📄 Formulário {i}:")
            print(f"   ID: {info['id']}")
            print(f"   Código: {info.get('código', 'N/A')}")
            print(f"   Item/Cláusula: {info.get('item_cláusula', 'N/A')}")
            print(f"   Indicador: {info.get('indicador', 'N/A')}")
            print(f"   Dimensão: {info.get('dimensão', 'N/A')}")
            print(f"   Verificação: {info.get('verificação', 'N/A')}")
            print(f"   Responsável: {info['assignee']}")
            print(f"   Criado em: {info['created_at']}")

    return formularios


def procurarCadastroPorItem(item_desejado=None):
    """
    Função principal - mantida para compatibilidade
    """
    if item_desejado is None or item_desejado == []:
        print("❌ Cláusulas desejadas não foram fornecidas.")
        return []

    if not isinstance(item_desejado, list):
        print("❌ Erro: As cláusulas desejadas devem ser fornecidas como uma lista.")
        return []

    return buscar_clausulas(item_desejado)


if __name__ == "__main__":
    # Este arquivo contém apenas funções para serem importadas
    # A execução deve ser feita através do main.py
    print("⚠️  Este arquivo contém apenas funções.")
    print("💡 Execute o main.py para usar o sistema completo.")