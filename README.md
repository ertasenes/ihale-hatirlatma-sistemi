# 🔔 İhale Hatırlatma Sistemi

Excel tabanlı ihale takviminden otomatik hatırlatma mailleri gönderen, Claude Code subagents yapısı ile çalışan akıllı bir sistemdir.

## 📋 Özellikler

- ✅ **Otomatik Mail Gönderimi**: 60, 30 ve 1 gün öncesinden hatırlatma
- ✅ **Outlook/Office 365 Entegrasyonu**: SMTP ile güvenli mail gönderimi
- ✅ **Dinamik İhale Yönetimi**: Excel dosyasından otomatik okuma ve güncelleme
- ✅ **Akıllı Zamanlama**: Günlük otomatik kontrol ve gönderim
- ✅ **Detaylı Raporlama**: Excel formatında gönderim raporu
- ✅ **GitHub Actions**: Cloud üzerinde otomatik çalıştırma
- ✅ **Subagents Yapısı**: Modüler ve genişletilebilir mimari

## 🏗️ Sistem Mimarisi

Sistem 4 ana agent üzerinden çalışır:

### 1. **File Agent** (`src/file_handler.py`)
- İhale takvim dosyasını okur
- Veri validasyonu yapar
- Hatırlatma durumlarını günceller

### 2. **Scheduler Agent** (`src/scheduler.py`)
- Bugün hangi hatırlatmaların gönderileceğini hesaplar
- 60/30/1 gün kontrollerini yapar
- Önceliklendirme yapar

### 3. **Email Agent** (`src/email_sender.py`)
- Outlook SMTP üzerinden mail gönderir
- HTML şablonlu mailler oluşturur
- Retry mekanizması ile hata yönetimi

### 4. **Report Agent** (`src/report_manager.py`)
- Gönderilen mailleri Excel'e kaydeder
- Günlük/haftalık/aylık istatistikler
- Başarılı/başarısız gönderim takibi

### 5. **Main Orchestrator** (`src/main.py`)
- Tüm agentları koordine eder
- İş akışını yönetir
- Loglama ve hata yönetimi

## 📁 Proje Yapısı

```
ihale-hatirlatma-sistemi/
├── .github/
│   └── workflows/
│       └── daily_reminder.yml      # GitHub Actions otomatik çalıştırma
├── agents/
│   ├── file_agent.md               # File Agent prompt & dokümantasyon
│   ├── scheduler_agent.md          # Scheduler Agent prompt & dokümantasyon
│   ├── email_agent.md              # Email Agent prompt & dokümantasyon
│   └── report_agent.md             # Report Agent prompt & dokümantasyon
├── config/
│   └── email_template.html         # HTML mail şablonu
├── data/
│   ├── Merkezi_Takvimi.xlsx        # İhale takvim dosyası
│   ├── mail_raporu.xlsx            # Gönderim rapor dosyası
│   └── backups/                    # Otomatik yedekler
├── logs/
│   └── system.log                  # Sistem logları
├── src/
│   ├── main.py                     # Ana orchestrator
│   ├── file_handler.py             # File Agent implementasyonu
│   ├── scheduler.py                # Scheduler Agent implementasyonu
│   ├── email_sender.py             # Email Agent implementasyonu
│   └── report_manager.py           # Report Agent implementasyonu
├── .env.example                    # Environment variables örneği
├── .gitignore                      # Git ignore kuralları
├── requirements.txt                # Python bağımlılıkları
└── README.md                       # Bu dosya
```

## 🚀 Kurulum

### 1. Repository'yi Klonlayın

```bash
git clone https://github.com/kullanici-adiniz/ihale-hatirlatma-sistemi.git
cd ihale-hatirlatma-sistemi
```

### 2. Python Bağımlılıklarını Yükleyin

```bash
pip install -r requirements.txt
```

### 3. Environment Variables Ayarlayın

`.env.example` dosyasını `.env` olarak kopyalayın ve düzenleyin:

```bash
cp .env.example .env
```

`.env` dosyasını düzenleyin:

```env
SMTP_SERVER=smtp.office365.com
SMTP_PORT=587
SMTP_EMAIL=sizin-mailiniz@sirketiniz.com
SMTP_PASSWORD=sizin-app-passwordunuz
TEST_MODE=False
```

**⚠️ Önemli:** Office 365 için App Password kullanmanız önerilir:
1. https://account.microsoft.com/security adresine gidin
2. "Advanced security options" > "App passwords" seçin
3. Yeni bir app password oluşturun
4. Bu password'ü `.env` dosyasına ekleyin

### 4. İhale Dosyasını Ekleyin

`data/Merkezi_Takvimi.xlsx` dosyasını yerleştirin. Dosya şu sütunları içermelidir:

| Sütun | Açıklama |
|-------|----------|
| S.no | İhale numarası |
| Toplantı Adı | İhale adı |
| D.Serve İlgili Kişi | Yönetici adı |
| D.serve İlgili Kişi Mail | Yönetici mail adresi |
| Toplantı Hazırlıkları Başlangıç Dönemi | Başlangıç tarihi |
| Hatırlatma Durumu | Gönderilen hatırlatmalar (otomatik güncellenir) |

### 5. Test Çalıştırması

Test modunda çalıştırın (gerçek mail göndermez):

```bash
cd src
TEST_MODE=True python main.py
```

Gerçek mail göndermek için:

```bash
cd src
python main.py
```

## ☁️ GitHub Actions ile Cloud Kurulum

### 1. GitHub Repository Oluşturun

GitHub'da yeni bir repository oluşturun (public veya private).

### 2. Kodu Push Edin

```bash
git init
git add .
git commit -m "İlk commit: İhale Hatırlatma Sistemi"
git branch -M main
git remote add origin https://github.com/kullanici-adiniz/ihale-hatirlatma-sistemi.git
git push -u origin main
```

### 3. GitHub Secrets Ekleyin

Repository Settings > Secrets and variables > Actions > New repository secret:

- `SMTP_SERVER`: smtp.office365.com
- `SMTP_PORT`: 587
- `SMTP_EMAIL`: sizin-mailiniz@sirketiniz.com
- `SMTP_PASSWORD`: app-password
- `TEST_MODE`: false

### 4. Workflow'u Aktif Edin

GitHub Actions sekmesinde workflow'u aktif edin. Her gün Türkiye saati 09:00'da otomatik çalışacaktır.

### 5. Manuel Tetikleme

GitHub Actions > "İhale Hatırlatma Sistemi" > "Run workflow" ile manuel olarak da çalıştırabilirsiniz.

## 📧 Mail Şablonu

Mail şablonu `config/email_template.html` dosyasında bulunur. Özelleştirmek için bu dosyayı düzenleyebilirsiniz.

**Mail Özellikleri:**
- 📱 Responsive (mobil uyumlu)
- 🎨 Modern ve profesyonel tasarım
- ⚠️ Acil durumlar için özel uyarı mesajı
- 📊 Detaylı ihale bilgileri

## 📊 Raporlama

### Mail Raporu (`data/mail_raporu.xlsx`)

Tüm gönderilen maillerın kaydı:

| Alan | Açıklama |
|------|----------|
| Gönderim Tarihi | Mail gönderim tarihi |
| Gönderim Saati | Mail gönderim saati |
| İhale No | İhale numarası |
| İhale Adı | İhale adı |
| Yönetici | Yönetici adı |
| Yönetici Mail | Alıcı mail adresi |
| Hatırlatma Tipi | 60_gun, 30_gun veya 1_gun |
| Kalan Gün | Başlangıç tarihine kalan gün |
| Başlangıç Tarihi | İhale başlangıç tarihi |
| Durum | Başarılı / Başarısız |
| Hata Mesajı | Hata varsa mesajı |
| Retry Sayısı | Kaç kez denendiği |

**Raporlar otomatik olarak:**
- ✅ Başarılı gönderimler yeşil renkte
- ❌ Başarısız gönderimler kırmızı renkte
- 📈 Günlük istatistikler loglarda

## 🔧 Bakım ve Güncelleme

### İhale Ekleme/Çıkarma

`data/Merkezi_Takvimi.xlsx` dosyasına yeni satırlar ekleyebilir veya mevcut satırları silebilirsiniz. Sistem otomatik olarak güncel dosyayı okuyacaktır.

### Yönetici ve Tarih Değişiklikleri

Excel dosyasında istediğiniz değişiklikleri yapın. Sistem her çalıştırmada güncel dosyayı okur.

### Mail Şablonu Değiştirme

`config/email_template.html` dosyasını düzenleyin. HTML ve CSS kullanarak tamamen özelleştirebilirsiniz.

### Zamanlama Değiştirme

`.github/workflows/daily_reminder.yml` dosyasında cron expression'ı değiştirin:

```yaml
schedule:
  - cron: '0 6 * * *'  # Her gün UTC 06:00 (TR 09:00)
```

## 🧪 Test

### Bütün Sistem Testi

```bash
cd src
python main.py
```

### Modül Testleri

Her modül bağımsız test edilebilir:

```bash
# File Handler testi
python file_handler.py

# Scheduler testi
python scheduler.py

# Email Sender testi
python email_sender.py

# Report Manager testi
python report_manager.py
```

## 📝 Loglar

Sistem logları `logs/system.log` dosyasında tutulur:

```bash
# Son 50 satırı göster
tail -n 50 logs/system.log

# Canlı takip
tail -f logs/system.log

# Hata loglarını filtrele
grep "ERROR" logs/system.log
```

## 🔒 Güvenlik

- ✅ SMTP şifreleri environment variable olarak saklanır
- ✅ `.env` dosyası `.gitignore`'da (GitHub'a pushlenmez)
- ✅ GitHub Secrets kullanılır
- ✅ TLS/SSL ile güvenli bağlantı
- ✅ App Password kullanımı önerilir

## 🐛 Sorun Giderme

### "SMTP Authentication Failed" Hatası

1. Email ve password'ü kontrol edin
2. Office 365 için App Password kullanın
3. 2FA aktifse normal password çalışmaz

### "Connection Timeout" Hatası

1. İnternet bağlantınızı kontrol edin
2. Firewall ayarlarını kontrol edin
3. SMTP server ve port doğru mu kontrol edin

### "File Not Found" Hatası

1. `data/Merkezi_Takvimi.xlsx` dosyasının var olduğundan emin olun
2. Dosya yolunu kontrol edin
3. Dosya izinlerini kontrol edin

### GitHub Actions Çalışmıyor

1. Secrets'ların doğru eklendiğinden emin olun
2. Workflow'un aktif olduğunu kontrol edin
3. Actions sekmesinden hata loglarına bakın

## 🤝 Katkıda Bulunma

1. Repository'yi fork edin
2. Feature branch oluşturun (`git checkout -b feature/yeni-ozellik`)
3. Değişikliklerinizi commit edin (`git commit -m 'Yeni özellik eklendi'`)
4. Branch'inizi push edin (`git push origin feature/yeni-ozellik`)
5. Pull Request oluşturun

## 📄 Lisans

Bu proje MIT lisansı altında lisanslanmıştır.

## 📧 İletişim

Sorularınız için:
- GitHub Issues kullanabilirsiniz
- Pull Request gönderebilirsiniz

## 🙏 Teşekkürler

Bu proje Claude Code ve Anthropic Claude AI ile geliştirilmiştir.

---

**Geliştirme:** Claude Code Subagents Architecture
**Versiyon:** 1.0.0
**Son Güncelleme:** Kasım 2025
