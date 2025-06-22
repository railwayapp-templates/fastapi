import pytest
from fastapi.testclient import TestClient
from main import app
import json

client = TestClient(app)

def test_root():
    """Testa o endpoint raiz da API"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "greeting" in data
    assert "message" in data
    assert data["greeting"] == "Hello, World!"
    assert data["message"] == "Welcome to FastAPI!"

def test_datas_indisponiveis():
    """Testa o endpoint de datas indisponíveis"""
    response = client.get("/datas-indisponiveis")
    assert response.status_code == 200
    data = response.json()
    
    # Verifica se a resposta contém a chave esperada
    assert "datas_indisponiveis" in data or "error" in data
    
    # Se não há erro, verifica se as datas estão no formato correto
    if "datas_indisponiveis" in data:
        dates = data["datas_indisponiveis"]
        assert isinstance(dates, list)
        
        # Verifica formato das datas (DD/MM/YYYY)
        for date in dates[:5]:  # Testa apenas as primeiras 5 datas
            assert isinstance(date, str)
            # Formato: DD/MM/YYYY
            date_parts = date.split('/')
            assert len(date_parts) == 3
            assert len(date_parts[0]) == 2  # dia
            assert len(date_parts[1]) == 2  # mês
            assert len(date_parts[2]) == 4  # ano

def test_datas_indisponiveis_response_structure():
    """Testa a estrutura da resposta do endpoint de datas indisponíveis"""
    response = client.get("/datas-indisponiveis")
    assert response.status_code == 200
    
    data = response.json()
    
    # A resposta deve ser um JSON válido
    assert isinstance(data, dict)
    
    # Deve conter uma das chaves: datas_indisponiveis ou error
    assert "datas_indisponiveis" in data or "error" in data

if __name__ == "__main__":
    print("Executando testes...")
    
    print("\n1. Testando endpoint raiz...")
    test_root()
    print("✅ Teste do endpoint raiz passou!")
    
    print("\n2. Testando endpoint de datas indisponíveis...")
    test_datas_indisponiveis()
    print("✅ Teste do endpoint de datas indisponíveis passou!")
    
    print("\n3. Testando estrutura da resposta...")
    test_datas_indisponiveis_response_structure()
    print("✅ Teste da estrutura da resposta passou!")
    
    print("\n🎉 Todos os testes passaram com sucesso!") 