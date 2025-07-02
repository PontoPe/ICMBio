import time

import requests
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
import uuid


class ChecklistCreator:
    def __init__(self):
        self.base_url = "https://app.way-v.com/api/integration"
        self.token = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJjb21wYW55X2lkIjoiNjYzZDMxYTFlOWRhYzNmNWY0ZDNjZjJlIiwiY3VycmVudF90aW1lIjoxNzQ4OTUzODcyNjgzLCJleHAiOjIwNjQ0ODY2NzJ9.j6zOrJMDKNcCcMMcO99SudriP7KqEDLMJDE2FBlQ6ok'
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }

        # IDs fixos do template de execução
        self.template_id = "67f6bfe0aa27d85466bdbb87"  # Template de execução
        self.execution_company_id = "663d31a1e9dac3f5f4d3cf2e"

        # IDs das perguntas principais para adicionar itens
        self.question_ids = {
            'FA': '934f80ddd425479b969227c01a5c2eda',
            'FT': '9ef230b33c3c435fbe83298d41acc30a',
            'FO': '8c517d351f15462aa62b4c9ac7e6b43e',
            'GC': '6e6de895e4604ba78f18e154072be80e',
            'VC': '438dc9b0b7394a72b6ff5008d7574824'
        }

        # Mapeamento dos IDs das sub-perguntas para cada tipo
        self.sub_question_mapping = {
            'FA': {
                'item': '3396430e77c74faebb2ebbfefac98b37',
                'codigo': '5a507221009d479a87fe3ac2de9b1919',
                'instrumento': 'b97d97f46fc04c15a2c301949d1b8861',
                'dimensao': '3c12a83a05b7482193cbf32d511c864e',
                'verificacao': 'e758f7b11b2e4d4f99eea9520711a8b1',
                'resposta': '9e3dc6b89ba24d899b20a30a00eefea6',
                'av': '25022d88d8d342c7bb81e77896378032',
                'peso': 'fd2cc26145c64297b55f002f5552fb8d',
                'avp': '1a13b936644f4eaf8f65033b24fb2daf',
                'indicador': '68015fa3daf29bba925f3db7'
            },
            'FT': {
                'item': 'b3f6d94b422a426a90f38ce833f1d8e5',
                'codigo': '61a996bc1fc34a79a057337493e40b82',
                'instrumento': 'b2a7a4c6f8e147f4a05ec7078f8fa701',
                'dimensao': '340e1d43c30f44c688feb46a2a67804e',
                'verificacao': 'af52a22123a64a5c90cea2d9879ecc8a',
                'indicador': 'a2a45ba1f55f47a5919371ad569afc15',
                'resposta': '02b1be56056e4e6d9fb92535738c1ec2',
                'av': '5b424d95b0564b8e8d7c5794b4339ef5',
                'peso': '3f6a015c3b2a4c9fa34b9e243d55f54d',
                'avp': '755a8a013f834a47b1e38616ca4cb940'
            },
            'FO': {
                'item': '24039db27aa8414cb886c60f379c311e',
                'codigo': '683f4b1dc4a5538b711b0f01',
                'instrumento': '18d14859aacf40f8a1ef25e42444c969',
                'dimensao': '83a2870b2f7845aaab120084d5337ac7',
                'verificacao': '5904a66402a44734b20404dd51d2f95c',
                'indicador': '4435bc77d6234f0d85cf73ea2ac3992b',
                'resposta': '3319075725da42e99a3adf15b9267c9f',
                'av': '4dbab1cc69714abba9c7d71a334a7681',
                'peso': 'a750de10487c4a0a9483992b9062456f',
                'avp': '8dad2e71fbf94e1ab1249756a8ff96eb'
            },
            'GC': {
                'item': 'a55b817719214888a93b2f388d372263',
                'instrumento': '1a40fe0f826841da8b43ffeba3c1eeae',
                'codigo': '683f4f9f6019b1f3b94bbeff',
                'dimensao': '597dcedfa3a9431d997dfca22f19dd1d',
                'verificacao': 'e4b50d1f4165477fa7902d033700dd88',
                'indicador': '57e1268b630149998a83e568372b3453',
                'resposta': '142585450e314b5992bcf9913f092647',
                'av': '16094d6622e547b18655731a5b2d4078',
                'peso': 'ca2286fe3f784b568deb19c85e3242b3',
                'avp': '1d9c6ac747de4b6d96c9e7ed02b3a350'
            },
            'VC': {
                'item': 'bdb01f91a9774e51ac61cc3cb1d73920',
                'instrumento': '5a1e10805d00494eaa8b8f84b321e4d0',
                'codigo': '683f51034c5aa9678b216f1e',
                'dimensao': '954901ca7d034cb7ae6695ba36497cdc',
                'verificacao': 'c81768535b3f4ded9ca03b6302d1fbe1',
                'indicador': '4466ffcbe37b4506b42922a9e6743fc8',
                'resposta': 'a1808fca95e14ffa9f673857500f708e',
                'av': '388a99bb2c8d47ce8abd5d1e7f4a2ca1',
                'peso': '3396de2bc98447b1b339a937056bfc30',
                'avp': '175178e731144088b56897910ffd3531'
            }
        }

        # IDs das perguntas de identificação
        self.identification_questions = {
            'data_prevista': '8113d0edd61c4cf6bf65ec10bdf68cda',
            'contrato': '11caa9daefcd41bcade0fb221886758b',
            'identificador': 'ed1c45973cfd47cbbd13fb26ff448e16|1',
            'concessionaria': '8838d1ca06bb4e0ba842b0e1adc5d949'
        }

    def criar_checklist_principal(self, identificacao: Dict[str, str],
                                  assignee_id: str = None,
                                  creator_id: str = None):
        checklist_data = {
            "checklist": {
                "template_id": self.template_id,
                "execution_company_id": self.execution_company_id,
                "assignee_id": assignee_id,
                "creator_id": creator_id,
                "status_info": {
                    "new_execution_status": "in_progress"
                },
                "questions": []
            }
        }

        # Perguntas de identificação
        for campo, question_id in self.identification_questions.items():
            if campo in identificacao:
                checklist_data["checklist"]["questions"].append({
                    "id": question_id,
                    "sub_questions": [{
                        "id": "1",
                        "value": identificacao[campo]
                    }]
                })

        # Placeholder para cada tipo
        for tipo in self.question_ids.keys():
            checklist_data["checklist"]["questions"].append({
                "id": self.question_ids[tipo],
                "sub_questions": []
            })

        print(f"📝 Criando checklist principal ...")
        response = requests.post(
            f"{self.base_url}/checklists",
            headers=self.headers,
            json=checklist_data
        )

        if response.status_code not in [200, 201]:
            print(f"❌ Erro ao criar checklist: {response.status_code}")
            print(response.text)
            return None
        else:
            checklist_id = response.json()["_id"]["$oid"]
            print(f"✅ Checklist criado com id: {checklist_id}")
            return checklist_id

    def adicionar_subchecklists(self, checklist_id: str, tipo: str, itens: List[Dict[str, Any]]):
        if not itens:
            print(f"ℹ️ Nenhum item para {tipo}")
            return

        print(f"📋 Adicionando {len(itens)} subchecklists para {tipo}...")

        sub_checklists = []
        question_mapping = self.sub_question_mapping[tipo]

        for item_data in itens:
            sub_checklist_questions = []

            # CORREÇÃO: Usar question_mapping[campo] em vez de self.question_template_id
            for campo, question_id in question_mapping.items():
                if campo in item_data:
                    valor = str(item_data[campo])

                    # Calcular AV*P se for o campo avp
                    if campo == 'avp' and 'av' in item_data and 'peso' in item_data:
                        valor = str(item_data['av'] * item_data['peso'])

                    sub_checklist_questions.append({
                        "question_id": question_id,  # Usar question_id corretamente
                        "value": valor
                    })

            sub_checklists.append({
                "id": self.question_ids[tipo],
                "sub_checklist_questions": sub_checklist_questions
            })

        payload = {
            "checklist_id": checklist_id,
            "sub_checklists": sub_checklists
        }

        print(f"📤 Enviando payload com {len(sub_checklists)} subchecklists...")
        response = requests.post(
            f"{self.base_url}/subchecklists",
            headers=self.headers,
            json=payload
        )

        if response.status_code in [200, 201]:
            print(f"✅ {len(itens)} subchecklists adicionados para {tipo}")
        else:
            print(f"❌ Erro ao adicionar subchecklists para {tipo}: {response.status_code}")
            print(response.text)

    def criar_checklist_completo(self, identificacao: Dict[str, str],
                                 itens_por_tipo: Dict[str, List[Dict]] = None,
                                 assignee_id: str = None,
                                 creator_id: str = None):
        checklist_id = self.criar_checklist_principal(
            identificacao=identificacao,
            assignee_id=assignee_id,
            creator_id=creator_id
        )

        if not checklist_id:
            print("❌ Falha ao criar checklist principal")
            return None

        if not itens_por_tipo:
            print("ℹ️ Nenhum item para adicionar")
            return checklist_id

        print("⏳ Aguardando 10 segundos antes de adicionar subchecklists...")
        time.sleep(10)

        for tipo, itens in itens_por_tipo.items():
            if tipo in self.question_ids and itens:
                self.adicionar_subchecklists(checklist_id, tipo, itens)

        return checklist_id

    def _gerar_subchecklist_id(self):
        """Gera um ID único para subchecklist"""
        return str(uuid.uuid4()).replace('-', '')[:32]  # Limitar a 32 caracteres


# Exemplo de uso
if __name__ == "__main__":
    creator = ChecklistCreator()

    # Dados de identificação
    identificacao = {
        "data_prevista": "26/06/2025",
        "contrato": "01/2021",
        "identificador": "TESTE-2025",
        "concessionaria": "Empresa XYZ"
    }

    todos_itens = {
        'FA': [
            {
                #'item': '12.1',
                'codigo': '03.04.01.03',
                'instrumento': 'Contrato',
                'dimensao': 'SÓCIO-AMBIENTAL',
                'verificacao': 'O Concessionário implantou Programa Interpretativo?',
                'av': 4,
                'peso': 3,
                'indicador': 'IERI'
            }
        ],
        'FT': [
            {
                #'item': '12.1',
                'codigo': '03.04.05.03',
                'instrumento': 'Contrato',
                'dimensao': 'FINANCEIRA',
                'verificacao': 'O Concessionário vem aplicando os descontos?',
                'indicador': 'IECOMPR',
                'av': 3,
                'peso': 2
            }
        ],
        'FO': [
            {
                #'item': '12.1',
                'codigo': '03.04.01.01',
                'instrumento': 'Contrato',
                'dimensao': 'SÓCIO-AMBIENTAL',
                'verificacao': 'A Concessionário vem aplicando recursos nos Macrotemas?',
                'indicador': 'IECA',
                'av': 1,
                'peso': 3
            }
        ]
    }

    resultado = creator.criar_checklist_completo(
        identificacao=identificacao,
        itens_por_tipo=todos_itens,
        assignee_id="6478f2c883e4a9312d68da0b",
        creator_id="6478f2c883e4a9312d68da0b"
    )

    if resultado:
        print(f"\n🎉 Processo concluído! Checklist ID: {resultado}")
    else:
        print("\n❌ Falha no processo de criação")