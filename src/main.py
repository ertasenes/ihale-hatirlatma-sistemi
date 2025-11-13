"""
Main Orchestrator
Tüm agentları koordine ederek ihale hatırlatma sistemini çalıştırır.
"""

import sys
from pathlib import Path
from datetime import datetime
import logging
from dotenv import load_dotenv

# Modülleri import et
from file_handler import FileHandler
from scheduler import Scheduler
from email_sender import EmailSender
from report_manager import ReportManager

# Logging ayarları
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/system.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class IhaleHatirlatmaSistemi:
    """Ana sistem sınıfı - Tüm agentları yönetir"""
    
    def __init__(self):
        logger.info("="*80)
        logger.info("🚀 İhale Hatırlatma Sistemi Başlatılıyor...")
        logger.info("="*80)
        
        # Environment variables'ı yükle
        load_dotenv()
        
        # Agentları başlat
        self.file_handler = FileHandler("data/Merkezi_Takvimi.xlsx")
        self.scheduler = Scheduler()
        self.email_sender = EmailSender()
        self.report_manager = ReportManager("data/mail_raporu.xlsx")
        
        logger.info("✅ Tüm agentlar başlatıldı\n")
    
    def run(self) -> dict:
        """Sistemi çalıştır"""
        try:
            start_time = datetime.now()
            logger.info(f"⏰ Başlangıç Zamanı: {start_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            
            # 1. İhale dosyasını oku (File Agent)
            logger.info("📂 [1/5] İhale Dosyası Okunuyor...")
            logger.info("-" * 80)
            file_result = self.file_handler.read_ihale_file()
            
            if not file_result["success"]:
                logger.error("❌ İhale dosyası okunamadı. İşlem sonlandırılıyor.")
                return {
                    "success": False,
                    "error": "İhale dosyası okunamadı",
                    "details": file_result
                }
            
            logger.info(f"✅ {file_result['valid_count']} ihale başarıyla okundu\n")
            
            # 2. Hatırlatmaları hesapla (Scheduler Agent)
            logger.info("📅 [2/5] Hatırlatmalar Hesaplanıyor...")
            logger.info("-" * 80)
            schedule_result = self.scheduler.calculate_reminders(file_result["data"])
            
            if not schedule_result["success"]:
                logger.error("❌ Hatırlatma hesaplama başarısız. İşlem sonlandırılıyor.")
                return {
                    "success": False,
                    "error": "Hatırlatma hesaplama başarısız",
                    "details": schedule_result
                }
            
            reminders_to_send = schedule_result["reminders_to_send"]
            
            if len(reminders_to_send) == 0:
                logger.info("ℹ️  Bugün gönderilecek hatırlatma yok.\n")
                return {
                    "success": True,
                    "reminders_sent": 0,
                    "message": "Bugün gönderilecek hatırlatma yok"
                }
            
            logger.info(f"✅ {len(reminders_to_send)} hatırlatma gönderilmeye hazır\n")
            
            # 3. SMTP Bağlantısını Test Et
            logger.info("🔌 [3/5] SMTP Bağlantısı Test Ediliyor...")
            logger.info("-" * 80)
            connection_test = self.email_sender.test_connection()
            
            if not connection_test["success"]:
                logger.error(f"❌ {connection_test['message']}")
                logger.error("⚠️  Mailler gönderilemeyecek ama rapor oluşturulacak.\n")
                # Devam et ama test modunda çalış
            else:
                logger.info(f"✅ {connection_test['message']}\n")
            
            # 4. Mailleri Gönder (Email Agent)
            logger.info("📧 [4/5] Mailler Gönderiliyor...")
            logger.info("-" * 80)
            email_results = self.email_sender.send_reminders(reminders_to_send)
            
            logger.info(f"\n✅ Mail gönderimi tamamlandı")
            logger.info(f"  • Başarılı: {email_results['sent_count']}")
            logger.info(f"  • Başarısız: {email_results['failed_count']}\n")
            
            # 5. Raporları Güncelle (Report Agent)
            logger.info("📊 [5/5] Raporlar Güncelleniyor...")
            logger.info("-" * 80)
            
            # Her bir sonucu rapora ekle
            for i, result in enumerate(email_results["results"]):
                reminder = reminders_to_send[i]
                self.report_manager.add_entry(result, reminder)
                
                # İhale dosyasındaki hatırlatma durumunu güncelle
                if result["status"] == "sent":
                    self.file_handler.update_hatirlatma_durumu(
                        ihale_no=result["ihale_no"],
                        hatirlatma_tipi=reminder["hatirlatma_tipi"],
                        tarih=result["timestamp"]
                    )
            
            logger.info("✅ Raporlar güncellendi\n")
            
            # Günlük istatistikleri göster
            daily_stats = self.report_manager.get_daily_statistics()
            logger.info("📈 Bugünkü Özet İstatistikler:")
            logger.info("-" * 80)
            logger.info(f"  • Toplam Gönderim: {daily_stats['toplam_gonderim']}")
            logger.info(f"  • Başarılı: {daily_stats['basarili']}")
            logger.info(f"  • Başarısız: {daily_stats['basarisiz']}")
            logger.info(f"  • 60 Gün: {daily_stats['60_gun']}")
            logger.info(f"  • 30 Gün: {daily_stats['30_gun']}")
            logger.info(f"  • 1 Gün: {daily_stats['1_gun']}")
            logger.info(f"  • Farklı Yönetici: {daily_stats['benzersiz_yonetici']}\n")
            
            # Bitiş zamanı
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            logger.info("="*80)
            logger.info(f"✅ İşlem Başarıyla Tamamlandı!")
            logger.info(f"⏱️  Toplam Süre: {duration:.2f} saniye")
            logger.info(f"🕐 Bitiş Zamanı: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info("="*80)
            
            return {
                "success": True,
                "reminders_sent": email_results['sent_count'],
                "reminders_failed": email_results['failed_count'],
                "duration_seconds": duration,
                "statistics": daily_stats
            }
            
        except Exception as e:
            logger.error(f"\n❌ HATA: {str(e)}")
            logger.exception("Detaylı hata:")
            return {
                "success": False,
                "error": str(e)
            }


def main():
    """Ana fonksiyon"""
    try:
        # Log klasörünü oluştur
        Path("logs").mkdir(exist_ok=True)
        
        # Sistemi başlat ve çalıştır
        sistem = IhaleHatirlatmaSistemi()
        result = sistem.run()
        
        # Sonuç kodunu döndür
        sys.exit(0 if result["success"] else 1)
        
    except Exception as e:
        logger.error(f"Kritik hata: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
