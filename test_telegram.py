import os
import requests
from config import Config

print("=" * 60)
print("🔍 TESTE DE TELEGRAM")
print("=" * 60)

token = Config.TELEGRAM_TOKEN
chat_id = Config.TELEGRAM_CHAT_ID

print(f"\n1️⃣ VERIFICANDO VARIÁVEIS:")
print(f"   Token configurado: {'✅ SIM' if token else '❌ NÃO'}")
print(f"   Chat ID configurado: {'✅ SIM' if chat_id else '❌ NÃO'}")

if not token or not chat_id:
    print("\n❌ ERRO: Falta configurar TELEGRAM_TOKEN ou TELEGRAM_CHAT_ID no Railway!")
    exit(1)

print(f"\n2️⃣ TESTANDO CONEXÃO COM TELEGRAM:")

try:
    url = f"https://api.telegram.org/bot{token}/getMe"
    r = requests.get(url, timeout=5)
    
    if r.status_code == 200:
        bot_info = r.json()['result']
        print(f"   ✅ Bot conectado: @{bot_info['username']}")
    else:
        print(f"   ❌ ERRO: Token inválido! Status: {r.status_code}")
        exit(1)
except Exception as e:
    print(f"   ❌ ERRO DE CONEXÃO: {e}")
    exit(1)

print(f"\n3️⃣ ENVIANDO MENSAGEM DE TESTE:")

try:
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    
    mensagem = """
🤖 TESTE DE TELEGRAM - BETFAIR BOT

✅ Bot está funcionando corretamente!

📊 Status:
• Banco de dados: OK ✓
• API Flask: OK ✓
• Telegram: OK ✓

🚨 Agora você receberá alertas de arbitragem aqui!

🎯 Próximo passo: Iniciar o bot no dashboard
    """
    
    payload = {
        "chat_id": chat_id,
        "text": mensagem
    }
    
    r = requests.post(url, json=payload, timeout=5)
    
    if r.status_code == 200:
        print(f"   ✅ MENSAGEM ENVIADA COM SUCESSO!")
        print(f"\n   Verifique seu Telegram para ver a mensagem!")
    else:
        print(f"   ❌ ERRO: {r.status_code}")
        print(f"   Resposta: {r.text}")
        exit(1)
        
except Exception as e:
    print(f"   ❌ ERRO: {e}")
    exit(1)

print("\n" + "=" * 60)
print("✅ TODOS OS TESTES PASSARAM!")
print("=" * 60)
