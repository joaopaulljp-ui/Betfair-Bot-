import os
import requests
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

def enviar_mensagem_teste():
    """Envia uma mensagem de teste no Telegram"""
    
    print("🔍 Testando Telegram...")
    print(f"Token: {TELEGRAM_TOKEN[:20]}..." if TELEGRAM_TOKEN else "❌ Token não configurado")
    print(f"Chat ID: {TELEGRAM_CHAT_ID}")
    
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("❌ Token ou Chat ID não configurados!")
        return False
    
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": """
🤖 TESTE DE TELEGRAM FUNCIONANDO!

✅ O bot conseguiu se conectar!

📊 Informações:
- Token: Configurado ✓
- Chat ID: Configurado ✓
- Conexão: OK ✓

🚨 Agora você receberá alertas de arbitragem aqui!
            """
        }
        
        print(f"\n📤 Enviando mensagem para Telegram...")
        print(f"URL: {url}")
        
        response = requests.post(url, json=payload, timeout=10)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ SUCESSO! Mensagem enviada no Telegram!")
            return True
        else:
            print("❌ ERRO! Verifique Token e Chat ID")
            return False
    
    except Exception as e:
        print(f"❌ ERRO AO ENVIAR: {e}")
        return False

if __name__ == "__main__":
    resultado = enviar_mensagem_teste()
    if resultado:
        print("\n🎉 Telegram está funcionando corretamente!")
    else:
        print("\n⚠️ Há um problema com a configuração do Telegram")
