#!/bin/bash

echo "=================================================="
echo "İhale Hatırlatma Sistemi - Hızlı Test"
echo "=================================================="

# Klasörleri oluştur
echo ""
echo "📁 Klasörler oluşturuluyor..."
mkdir -p data logs data/backups

# İhale dosyası kontrolü
if [ ! -f "data/Merkezi_Takvimi.xlsx" ]; then
    echo "❌ HATA: data/Merkezi_Takvimi.xlsx dosyası bulunamadı!"
    echo "Lütfen ihale dosyasını data/ klasörüne ekleyin."
    exit 1
fi

echo "✅ İhale dosyası bulundu"

# .env dosyası kontrolü
if [ ! -f ".env" ]; then
    echo ""
    echo "⚠️  .env dosyası bulunamadı!"
    echo "📝 .env.example'dan kopyalanıyor..."
    cp .env.example .env
    echo ""
    echo "⚠️  ÖNEMLI: .env dosyasını düzenleyip SMTP bilgilerinizi ekleyin!"
    echo ""
fi

# Python bağımlılıkları
echo ""
echo "📦 Python bağımlılıkları kontrol ediliyor..."
pip3 install -r requirements.txt -q

# Test modunda çalıştır
echo ""
echo "🧪 Test modunda çalıştırılıyor..."
echo "=================================================="
cd src
TEST_MODE=True python3 main.py

echo ""
echo "=================================================="
echo "✅ Test tamamlandı!"
echo ""
echo "📝 Sonraki adımlar:"
echo "1. .env dosyasını düzenleyin ve gerçek SMTP bilgilerinizi ekleyin"
echo "2. Gerçek mail göndermek için: cd src && python3 main.py"
echo "3. GitHub'a push edin ve Actions'u kurun"
echo ""
echo "=================================================="
