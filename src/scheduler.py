"""
Scheduler Module
Hangi ihalelere bugün hatırlatma gönderilmesi gerektiğini hesaplar.
"""

from datetime import datetime, timedelta
import pytz
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Scheduler:
    """Hatırlatma zamanlama sınıfı"""
    
    def __init__(self, timezone: str = "Europe/Istanbul"):
        self.timezone = pytz.timezone(timezone)
        self.today = datetime.now(self.timezone).date()
        
    def calculate_reminders(self, ihale_list: list) -> dict:
        """
        Bugün gönderilmesi gereken hatırlatmaları hesapla
        
        Args:
            ihale_list: FileHandler'dan gelen ihale listesi
            
        Returns:
            dict: Gönderilecek hatırlatmalar ve istatistikler
        """
        try:
            reminders_to_send = []
            statistics = {
                "bugun_tarihi": self.today,
                "toplam_ihale": len(ihale_list),
                "gonderilecek_hatirlatma": 0,
                "60_gun_hatirlatma": 0,
                "30_gun_hatirlatma": 0,
                "1_gun_hatirlatma": 0,
                "gecmis_tarihli_ihale": 0
            }
            warnings = []
            
            logger.info(f"📅 Bugünün tarihi: {self.today}")
            logger.info(f"🔍 {len(ihale_list)} ihale kontrol ediliyor...")
            
            for ihale in ihale_list:
                ihale_no = ihale["ihale_no"]
                ihale_adi = ihale["ihale_adi"]
                baslangic_tarihi = ihale["baslangic_tarihi"].date()
                hatirlatma_durumu = ihale["hatirlatma_durumu"]
                
                # Kalan gün hesapla
                kalan_gun = (baslangic_tarihi - self.today).days
                
                # Geçmiş tarih kontrolü
                if kalan_gun < 0:
                    statistics["gecmis_tarihli_ihale"] += 1
                    warnings.append(f"İhale {ihale_no} ({ihale_adi}): Başlangıç tarihi geçmişte ({baslangic_tarihi})")
                    continue
                
                # Bugün başlangıç tarihi ise acil hatırlatma
                if kalan_gun == 0:
                    warnings.append(f"İhale {ihale_no} ({ihale_adi}): Bugün başlangıç tarihi!")
                    continue
                
                # Hatırlatma kontrollerini yap
                reminders = self._check_reminder_dates(
                    ihale, 
                    baslangic_tarihi, 
                    kalan_gun, 
                    hatirlatma_durumu
                )
                
                # Her bir hatırlatmayı ekle
                for reminder in reminders:
                    reminders_to_send.append(reminder)
                    
                    # İstatistikleri güncelle
                    reminder_type = reminder["hatirlatma_tipi"]
                    if reminder_type == "60_gun":
                        statistics["60_gun_hatirlatma"] += 1
                    elif reminder_type == "30_gun":
                        statistics["30_gun_hatirlatma"] += 1
                    elif reminder_type == "1_gun":
                        statistics["1_gun_hatirlatma"] += 1
            
            # Hatırlatmaları önceliklere göre sırala (1 gün en yüksek öncelik)
            reminders_to_send = self._prioritize_reminders(reminders_to_send)
            
            statistics["gonderilecek_hatirlatma"] = len(reminders_to_send)
            
            # Sonuçları logla
            logger.info(f"\n📊 İstatistikler:")
            logger.info(f"  • Toplam İhale: {statistics['toplam_ihale']}")
            logger.info(f"  • Gönderilecek Hatırlatma: {statistics['gonderilecek_hatirlatma']}")
            logger.info(f"    - 60 gün: {statistics['60_gun_hatirlatma']}")
            logger.info(f"    - 30 gün: {statistics['30_gun_hatirlatma']}")
            logger.info(f"    - 1 gün: {statistics['1_gun_hatirlatma']}")
            if statistics['gecmis_tarihli_ihale'] > 0:
                logger.warning(f"  ⚠️  Geçmiş tarihli: {statistics['gecmis_tarihli_ihale']}")
            
            return {
                "success": True,
                "schedule_date": self.today,
                "reminders_to_send": reminders_to_send,
                "statistics": statistics,
                "warnings": warnings,
                "errors": []
            }
            
        except Exception as e:
            logger.error(f"❌ Zamanlama hatası: {str(e)}")
            return {
                "success": False,
                "schedule_date": self.today,
                "reminders_to_send": [],
                "statistics": {},
                "warnings": [],
                "errors": [f"Zamanlama hatası: {str(e)}"]
            }
    
    def _check_reminder_dates(self, ihale: dict, baslangic_tarihi, kalan_gun: int, hatirlatma_durumu: str) -> list:
        """
        Bir ihale için hangi hatırlatmaların gönderilmesi gerektiğini kontrol et
        
        Returns:
            list: Gönderilecek hatırlatmalar
        """
        reminders = []
        
        # Daha önce gönderilen hatırlatmaları parse et
        sent_reminders = self._parse_hatirlatma_durumu(hatirlatma_durumu)
        
        # 60 gün kontrolü
        if kalan_gun == 60:
            if "60_gun" not in sent_reminders:
                reminders.append(self._create_reminder(ihale, 60, "60_gun", "normal"))
        
        # 30 gün kontrolü
        if kalan_gun == 30:
            if "30_gun" not in sent_reminders:
                reminders.append(self._create_reminder(ihale, 30, "30_gun", "normal"))
        
        # 1 gün kontrolü
        if kalan_gun == 1:
            if "1_gun" not in sent_reminders:
                reminders.append(self._create_reminder(ihale, 1, "1_gun", "acil"))
        
        return reminders
    
    def _parse_hatirlatma_durumu(self, hatirlatma_durumu: str) -> list:
        """
        Hatırlatma durumu string'ini parse et
        
        Örnek: "60gün:2025-11-13, 30gün:2025-12-13"
        Returns: ["60_gun", "30_gun"]
        """
        if not hatirlatma_durumu or hatirlatma_durumu == "None":
            return []
        
        sent_types = []
        try:
            parts = hatirlatma_durumu.split(",")
            for part in parts:
                if ":" in part:
                    reminder_type = part.split(":")[0].strip()
                    # "60gün" -> "60_gun" formatına çevir
                    if "gün" in reminder_type or "gun" in reminder_type:
                        reminder_type = reminder_type.replace("gün", "_gun").replace("gun", "_gun")
                    sent_types.append(reminder_type)
        except:
            pass
        
        return sent_types
    
    def _create_reminder(self, ihale: dict, kalan_gun: int, hatirlatma_tipi: str, oncelik: str) -> dict:
        """Hatırlatma dictionary'si oluştur"""
        return {
            "ihale_no": ihale["ihale_no"],
            "ihale_adi": ihale["ihale_adi"],
            "yonetici": ihale["yonetici"],
            "yonetici_mail": ihale["yonetici_mail"],
            "baslangic_tarihi": ihale["baslangic_tarihi"],
            "kalan_gun": kalan_gun,
            "hatirlatma_tipi": hatirlatma_tipi,
            "oncelik": oncelik
        }
    
    def _prioritize_reminders(self, reminders: list) -> list:
        """Hatırlatmaları önceliklere göre sırala"""
        priority_order = {"1_gun": 1, "30_gun": 2, "60_gun": 3}
        
        return sorted(
            reminders, 
            key=lambda x: priority_order.get(x["hatirlatma_tipi"], 99)
        )


if __name__ == "__main__":
    # Test
    from file_handler import FileHandler
    
    # Dosyayı oku
    file_handler = FileHandler()
    file_result = file_handler.read_ihale_file()
    
    if file_result["success"]:
        # Zamanlamayı hesapla
        scheduler = Scheduler()
        schedule_result = scheduler.calculate_reminders(file_result["data"])
        
        if schedule_result["success"]:
            print("\n🎯 Gönderilecek Hatırlatmalar:\n")
            for reminder in schedule_result["reminders_to_send"]:
                print(f"{'🔴' if reminder['oncelik'] == 'acil' else '🟡'} {reminder['ihale_adi']}")
                print(f"   Yönetici: {reminder['yonetici']}")
                print(f"   Kalan Gün: {reminder['kalan_gun']}")
                print(f"   Tip: {reminder['hatirlatma_tipi']}")
                print("-" * 60)
        
        if schedule_result["warnings"]:
            print("\n⚠️  Uyarılar:")
            for warning in schedule_result["warnings"]:
                print(f"  - {warning}")
