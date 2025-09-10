import time
import requests
import json
from typing import Dict, List, Any
import math
import GET
import os


# A linha "from concurrent.futures import ThreadPoolExecutor, as_completed" deve ser removida

class ChecklistCreator:
    def __init__(self):
        self.base_url = "https://app.way-v.com/api/integration"
        self.token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJjb21wYW55X2lkIjoiNjYzZDMxYTFlOWRhYzNmNWY0ZDNjZjJlIiwiY3VycmVudF90aW1lIjoxNzQ4OTUzODcyNjgzLCJleHAiOjIwNjQ0ODY2NzJ9.j6zOrJMDKNcCcMMcO99SudriP7KqEDLMJDE2FBlQ6ok"
        self.headers = {"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"}

        self.template_id_fiscalizacao = "67f6bfe0aa27d85466bdbb87"
        self.question_ids_fiscalizacao = {
            'FA': '934f80ddd425479b969227c01a5c2eda', 'FT': '9ef230b33c3c435fbe83298d41acc30a',
            'FO': '8c517d351f15462aa62b4c9ac7e6b43e', 'GC': '6e6de895e4604ba78f18e154072be80e',
            'VC': '438dc9b0b7394a72b6ff5008d7574824'
        }
        self.sub_question_mapping_fiscalizacao = {
            'FA': {'item': '3396430e77c74faebb2ebbfefac98b37', 'codigo': '5a507221009d479a87fe3ac2de9b1919',
                   'instrumento': 'b97d97f46fc04c15a2c301949d1b8861', 'dimensao': '3c12a83a05b7482193cbf32d511c864e',
                   'verificacao': 'e758f7b11b2e4d4f99eea9520711a8b1', 'av': '25022d88d8d342c7bb81e77896378032',
                   'peso': 'fd2cc26145c64297b55f002f5552fb8d', 'indicador': '68015fa3daf29bba925f3db7'},
            'FT': {'item': 'b3f6d94b422a426a90f38ce833f1d8e5', 'codigo': '61a996bc1fc34a79a057337493e40b82',
                   'instrumento': 'b2a7a4c6f8e147f4a05ec7078f8fa701', 'dimensao': '340e1d43c30f44c688feb46a2a67804e',
                   'verificacao': 'af52a22123a64a5c90cea2d9879ecc8a', 'indicador': 'a2a45ba1f55f47a5919371ad569afc15',
                   'av': '5b424d95b0564b8e8d7c5794b4339ef5', 'peso': '3f6a015c3b2a4c9fa34b9e243d55f54d'},
            'FO': {'item': '24039db27aa8414cb886c60f379c311e', 'codigo': '683f4b1dc4a5538b711b0f01',
                   'instrumento': '18d14859aacf40f8a1ef25e42444c969', 'dimensao': '83a2870b2f7845aaab120084d5337ac7',
                   'verificacao': '5904a66402a44734b20404dd51d2f95c', 'indicador': '4435bc77d6234f0d85cf73ea2ac3992b',
                   'av': '4dbab1cc69714abba9c7d71a334a7681', 'peso': 'a750de10487c4a0a9483992b9062456f'},
            'GC': {'item': 'a55b817719214888a93b2f388d372263', 'instrumento': '1a40fe0f826841da8b43ffeba3c1eeae',
                   'codigo': '683f4f9f6019b1f3b94bbeff', 'dimensao': '597dcedfa3a9431d997dfca22f19dd1d',
                   'verificacao': 'e4b50d1f4165477fa7902d033700dd88', 'indicador': '57e1268b630149998a83e568372b3453',
                   'av': '16094d6622e547b18655731a5b2d4078', 'peso': 'ca2286fe3f784b568deb19c85e3242b3'},
            'VC': {'item': 'bdb01f91a9774e51ac61cc3cb1d73920', 'instrumento': '5a1e10805d00494eaa8b8f84b321e4d0',
                   'codigo': '683f51034c5aa9678b216f1e', 'dimensao': '954901ca7d034cb7ae6695ba36497cdc',
                   'verificacao': 'c81768535b3f4ded9ca03b6302d1fbe1', 'indicador': '4466ffcbe37b4506b42922a9e6743fc8',
                   'av': '388a99bb2c8d47ce8abd5d1e7f4a2ca1', 'peso': '3396de2bc98447b1b339a937056bfc30'}
        }
        self.identification_questions = {
            'data_prevista': '8113d0edd61c4cf6bf65ec10bdf68cda',
            'contrato_concessao': '11caa9daefcd41bcade0fb221886758b',
            'identificador': '9c51272c7c774224b4dd2783b5fe62d4', 'concessionaria': '8838d1ca06bb4e0ba842b0e1adc5d949'
        }

        self.question_id_subform_itens = "5a3c6db29f4c4968af9cb67001570e7b"
        self.sub_question_id_item_col = "686840cf8bb23d7cf663bbb8"

    def _send_request(self, payload: Dict, batch_num: int) -> bool:
        try:
            response = requests.post(f"{self.base_url}/subchecklists", headers=self.headers, json=payload, timeout=90)
            if response.status_code not in [200, 201]:
                print(f"❌ ERRO no lote {batch_num}: Status {response.status_code}\n{response.text}")
                return False
            else:
                print(f"✅ Lote {batch_num} enviado com sucesso.")
                return True
        except requests.exceptions.RequestException as e:
            print(f"❌ ERRO DE CONEXÃO no lote {batch_num}: {e}")
            return False

    # --- MÉTDO MODIFICADO ---
        # --- MÉTDO MODIFICADO ---
    def popular_formulario_planejamento(self, form_id: str, clausulas: List[str]):
        if not clausulas:
            print("ℹ️ Nenhuma cláusula de cadastro encontrada para popular.")
            return

        print(f"📋 Preparando para popular o formulário ID: {form_id} com {len(clausulas)} cláusulas...")

        # Nova etapa: separar cláusulas por instrumento
        print("🔍 Separando cláusulas por instrumento...")

        # Inicializar as listas por instrumento
        itens_contrato = []
        itens_caderno_encargos = []
        itens_projeto_basico = []
        itens_evef = []
        itens_edital = []
        itens_aditivo = []

        # Carregar dados do cache para análise
        if not os.path.exists('cache_formularios.json'):
            print("❌ Arquivo de cache 'cache_formularios.json' não encontrado para separação por instrumento.")
            return

        try:
            with open('cache_formularios.json', 'r', encoding='utf-8') as f:
                cache_data = json.load(f)

            dados_formularios = cache_data.get('dados', [])

            # Mapear instrumento para lista correspondente
            instrumento_para_lista = {
                "Contrato": itens_contrato,
                "Caderno de encargos": itens_caderno_encargos,
                "Projeto Básico": itens_projeto_basico,
                "EVEF": itens_evef,
                "Edital": itens_edital,
                "Aditivo": itens_aditivo
            }

            # Percorrer todos os formulários para encontrar as cláusulas e seus instrumentos
            clausulas_set = {str(c).strip() for c in clausulas}
            clausulas_processadas = set()

            for formulario in dados_formularios:
                for secao in formulario.get('sections', []):
                    if secao.get('title') == 'Identificação':
                        item_clausula = None
                        instrumento = None

                        # Extrair item/cláusula e instrumento
                        for questao in secao.get('questions', []):
                            if questao.get('title') == 'item/Cláusula':
                                item_clausula = str(questao.get('sub_questions', [{}])[0].get('value', '')).strip()
                            elif questao.get('title') == 'Instrumento':
                                instrumento = str(questao.get('sub_questions', [{}])[0].get('value', '')).strip()

                        # Se encontrou tanto o item quanto o instrumento, e o item está na lista de cláusulas
                        if item_clausula and instrumento and item_clausula in clausulas_set:
                            if instrumento in instrumento_para_lista:
                                instrumento_para_lista[instrumento].append(item_clausula)
                                clausulas_processadas.add(item_clausula)
                                print(f"  ✓ Item {item_clausula} → {instrumento}")
                            else:
                                print(f"  ⚠️ Instrumento desconhecido para item {item_clausula}: '{instrumento}'")

                        break  # Sair do loop de seções após processar 'Identificação'

            # Relatório da separação
            print(f"\n📊 Relatório da separação por instrumento:")
            print(f"  • Contrato: {len(itens_contrato)} itens")
            print(f"  • Caderno de encargos: {len(itens_caderno_encargos)} itens")
            print(f"  • Projeto Básico: {len(itens_projeto_basico)} itens")
            print(f"  • EVEF: {len(itens_evef)} itens")
            print(f"  • Edital: {len(itens_edital)} itens")
            print(f"  • Aditivo: {len(itens_aditivo)} itens")
            print(f"  • Total processado: {len(clausulas_processadas)}/{len(clausulas)}")

            # Verificar se há cláusulas não processadas
            clausulas_nao_processadas = clausulas_set - clausulas_processadas
            if clausulas_nao_processadas:
                print(f"  ⚠️ Cláusulas não encontradas no cache: {sorted(list(clausulas_nao_processadas))}")

        except Exception as e:
            print(f"❌ Erro ao separar cláusulas por instrumento: {e}")
            return

        # ✅ **CORREÇÃO 1**: Simplificado o dicionário para remover as chaves não utilizadas
        subformularios_config = {
            "Contrato": {
                "sub_entry_id": "e59b5582f2a2421eb475a0ab1c4d26b3",
                "item_question_id": "689639faaf3d80cb1aeb30e5",
                "itens": itens_contrato
            },
            "Caderno de encargos": {
                "sub_entry_id": "2affd4a2ab4f483ba50e496270d8e06c",
                "item_question_id": "68963d5e65bd3707b0e10824",
                "itens": itens_caderno_encargos
            },
            "Projeto Básico": {
                "sub_entry_id": "aba4c44acf9842739a0fff4f0bd9a744",
                "item_question_id": "689641be1b29d3b972fbba97",
                "itens": itens_projeto_basico
            },
            "EVEF": {
                "sub_entry_id": "9c8c2b54fdcb428282692281029ac74a",
                "item_question_id": "689648186d5df9d26cdaee10",
                "itens": itens_evef
            },
            "Edital": {
                "sub_entry_id": "c7b33e1bb7d34b62b6d45b5895e5ad90",
                "item_question_id": "689649471d38401fdefa5ca6",
                "itens": itens_edital
            },
            "Aditivo": {
                "sub_entry_id": "94aca9b0582b466d9cdb972798f4aa8c",
                "item_question_id": "689649f51b29d3b972fbca6f",
                "itens": itens_aditivo
            }
        }

        # Preparar todos os sub_checklists para envio
        todos_sub_checklists = []

        for instrumento, config in subformularios_config.items():
            itens_do_instrumento = config["itens"]

            if not itens_do_instrumento:
                print(f"📝 Nenhum item encontrado para {instrumento}, pulando...")
                continue

            print(f"📝 Preparando {len(itens_do_instrumento)} itens para subformulário: {instrumento}")

            for item in itens_do_instrumento:
                # ✅ **CORREÇÃO 2**: Simplificado o payload para enviar apenas o campo "item"
                sub_checklist = {
                    "id": config["sub_entry_id"],
                    "sub_checklist_questions": [
                        {
                            "question_id": config["item_question_id"],
                            "value": str(item)
                        }
                    ]
                }
                todos_sub_checklists.append(sub_checklist)

        if not todos_sub_checklists:
            print("⚠️ Nenhum subchecklist foi preparado.")
            return

        # Envio em lotes
        batch_size = 150
        payloads = [
            {"checklist_id": form_id, "sub_checklists": todos_sub_checklists[i:i + batch_size]}
            for i in range(0, len(todos_sub_checklists), batch_size)
        ]

        total_lotes = len(payloads)
        print(f"📦 Total de {len(todos_sub_checklists)} itens a serem enviados em {total_lotes} lotes sequenciais.")

        success_count = 0
        for i, payload in enumerate(payloads):
            batch_num = i + 1
            print(f"➡️ Enviando lote {batch_num}/{total_lotes}...")

            # Chama o envio para o lote atual e aguarda o resultado
            success = self._send_request(payload, batch_num)

            # Se o envio falhar, interrompe o processo
            if success:
                success_count += 1
            else:
                print(f"🛑 Envio interrompido devido a erro no lote {batch_num}.")
                break

        if success_count == total_lotes:
            print("🎉 Formulário populado com sucesso! Todos os lotes foram enviados.")
        else:
            print(
                f"⚠️ Processo de população concluído com falhas. {success_count} de {total_lotes} lotes enviados com sucesso.")

    def criar_checklist_principal(self, identificacao: Dict[str, str], execution_company_id: str,
                                  assignee_id: str = None, creator_id: str = None):
        checklist_data = {
            "checklist": {
                "template_id": self.template_id_fiscalizacao,
                "execution_company_id": execution_company_id,
                "assignee_id": assignee_id,
                "creator_id": creator_id,
                "status_info": {
                    "new_execution_status": "pending"
                },
                "questions": []
            }
        }
        for campo, question_id in self.identification_questions.items():
            valor = identificacao.get(campo)
            if valor:
                checklist_data["checklist"]["questions"].append(
                    {"id": question_id, "sub_questions": [{"id": "1", "value": valor}]})
        for tipo in self.question_ids_fiscalizacao.keys():
            checklist_data["checklist"]["questions"].append(
                {"id": self.question_ids_fiscalizacao[tipo], "sub_questions": []})

        print(f"📝 Criando checklist principal para a empresa {execution_company_id} com status 'pending'...")
        response = requests.post(f"{self.base_url}/checklists", headers=self.headers, json=checklist_data)
        if response.status_code not in [200, 201]:
            print(f"❌ Erro ao criar checklist: {response.status_code}\n{response.text}")
            return None
        else:
            checklist_id = response.json()["_id"]["$oid"]
            print(f"✅ Checklist criado com id: {checklist_id}")
            return checklist_id

    def adicionar_subchecklists_fiscalizacao(self, checklist_id: str, tipo: str, itens: List[Dict[str, Any]]):
        if not itens: return
        print(f"📋 Adicionando {len(itens)} itens de fiscalização para a categoria {tipo}...")
        sub_checklists = []
        question_mapping = self.sub_question_mapping_fiscalizacao[tipo]
        for item_data in itens:
            sub_checklist_questions = []
            for campo, question_id in question_mapping.items():
                if campo in item_data and item_data[campo] is not None:
                    sub_checklist_questions.append({"question_id": question_id, "value": str(item_data[campo])})
            sub_checklists.append(
                {"id": self.question_ids_fiscalizacao[tipo], "sub_checklist_questions": sub_checklist_questions})
        payload = {"checklist_id": checklist_id, "sub_checklists": sub_checklists}
        response = requests.post(f"{self.base_url}/subchecklists", headers=self.headers, json=payload, timeout=90)
        if response.status_code not in [200, 201]:
            print(f"❌ Erro ao adicionar itens para {tipo}: {response.status_code}\n{response.text}")

    def criar_checklist_completo(self, identificacao: Dict[str, str], execution_company_id: str,
                                 itens_por_tipo: Dict[str, List[Dict]] = None,
                                 assignee_id: str = None, creator_id: str = None):
        checklist_id = self.criar_checklist_principal(identificacao=identificacao,
                                                      execution_company_id=execution_company_id,
                                                      assignee_id=assignee_id, creator_id=creator_id)
        if not checklist_id: return None
        if not itens_por_tipo: return None
        print("⏳ Aguardando 2 segundos antes de adicionar subchecklists...")
        time.sleep(2)
        for tipo, itens in itens_por_tipo.items():
            if tipo in self.question_ids_fiscalizacao and itens:
                self.adicionar_subchecklists_fiscalizacao(checklist_id, tipo, itens)
        return checklist_id