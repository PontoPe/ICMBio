# main.py – Apenas inicializador do servidor.
from __future__ import annotations

import uvicorn
from pyngrok import ngrok, conf
import webhook

# ------------- ngrok fixo ------------
NGROK_DOMAIN = "enormous-infinite-tahr.ngrok-free.app"
# Substitua pelo seu token do ngrok, se necessário
if (tok := "2yy04GbRMzDFhGgaRo3PGRqV5tC_4gkaL24YZ3yhDkNq9wDuh"):
    conf.get_default().auth_token = tok
    try:
        ngrok.connect(addr=8000, proto="http", domain=NGROK_DOMAIN)
        print(f"Ngrok conectado em: https://{NGROK_DOMAIN}")
    except Exception as e:
        print(f"Não foi possível conectar ao domínio ngrok fixo. Erro: {e}")
        try:
            # Tenta conectar sem domínio fixo como alternativa
            http_tunnel = ngrok.connect(addr=8000, proto="http")
            print(f"Ngrok conectado em: {http_tunnel.public_url}")
        except Exception as tunnel_e:
            print(f"Falha ao conectar o ngrok: {tunnel_e}")

# ---------- FastAPI app ---------------
# A aplicação agora é criada e configurada inteiramente dentro do webhook.py
app = webhook.criar_app_fastapi()

print("[main] 🚀 Servidor pronto em http://localhost:8000")

if __name__ == "__main__":
    # reload=False é recomendado para produção para evitar reinícios inesperados
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)
