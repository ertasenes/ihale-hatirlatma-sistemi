"""
Email Sender Module
Outlook SMTP üzerinden hatırlatma maillerini gönderir.
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import time
import os
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EmailSender:
    """Email gönderim sınıfı"""
    
    def __init__(self):
        # Environment variables'dan ayarları al
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.office365.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_email = os.getenv("SMTP_EMAIL", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.test_mode = os.getenv("TEST_MODE", "False").lower() == "true"
        
        # Mail şablonunu yükle
        self.email_template = self._load_email_template()
    
    def _load_email_template(self) -> str:
        """HTML mail şablonunu yükle"""
        template_path = Path("config/email_template.html")
        
        if template_path.exists():
            with open(template_path, "r", encoding="utf-8") as f:
                return f.read()
        
        # Varsayılan şablon
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #0078d4; color: white; padding: 20px; text-align: center; }}
                .content {{ background-color: #f9f9f9; padding: 30px; border: 1px solid #ddd; }}
                .info-box {{ background-color: white; padding: 15px; margin: 20px 0; border-left: 4px solid #0078d4; }}
                .info-item {{ margin: 10px 0; }}
                .info-label {{ font-weight: bold; color: #0078d4; }}
                .warning {{ background-color: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 20px 0; }}
                .footer {{ text-align: center; color: #666; font-size: 12px; margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>🔔 İhale Hatırlatması</h2>
                </div>
                <div class="content">
                    <p>Sayın <strong>{yonetici}</strong>,</p>
                    
                    <p><strong>{ihale_adi}</strong> ihalesinin hazırlık sürecine başlangıç dönemine 
                    <strong style="color: #d9534f;">{kalan_gun} gün</strong> kaldığını hatırlatmak isteriz.</p>
                    
                    <div class="info-box">
                        <h3 style="margin-top: 0; color: #0078d4;">📋 İhale Detayları</h3>
                        <div class="info-item">
                            <span class="info-label">İhale Adı:</span> {ihale_adi}
                        </div>
                        <div class="info-item">
                            <span class="info-label">Hazırlık Başlangıç Tarihi:</span> {baslangic_tarihi}
                        </div>
                        <div class="info-item">
                            <span class="info-label">Kalan Gün:</span> <strong>{kalan_gun} gün</strong>
                        </div>
                        <div class="info-item">
                            <span class="info-label">Sorumlu:</span> {yonetici}
                        </div>
                    </div>
                    
                    {aciliyet_mesaji}
                    
                    <p>Lütfen gerekli hazırlıkları zamanında başlatınız.</p>
                    
                    <p>İyi çalışmalar dileriz.</p>
                </div>
                <div class="footer">
                    <p>Bu mail otomatik olarak <strong>İhale Hatırlatma Sistemi</strong> tarafından gönderilmiştir.</p>
                    <p>Gönderim Tarihi: {gonderim_tarihi}</p>
                </div>
            </div>
        </body>
        </html>
        """
    
    def _create_email_body(self, reminder: dict) -> str:
        """Mail içeriğini oluştur"""
        # Aciliyet mesajı (1 gün kaldıysa)
        aciliyet_mesaji = ""
        if reminder["kalan_gun"] == 1:
            aciliyet_mesaji = """
            <div class="warning">
                <strong>⚠️ DİKKAT:</strong> Yarın ihale hazırlık sürecine başlanacaktır. 
                Lütfen acil olarak gerekli hazırlıkları tamamlayınız!
            </div>
            """
        
        # Tarihi formatla
        baslangic_tarihi = reminder["baslangic_tarihi"].strftime("%d.%m.%Y")
        gonderim_tarihi = datetime.now().strftime("%d.%m.%Y %H:%M")
        
        # Şablonu doldur
        body = self.email_template.format(
            yonetici=reminder["yonetici"],
            ihale_adi=reminder["ihale_adi"],
            kalan_gun=reminder["kalan_gun"],
            baslangic_tarihi=baslangic_tarihi,
            aciliyet_mesaji=aciliyet_mesaji,
            gonderim_tarihi=gonderim_tarihi
        )
        
        return body
    
    def test_connection(self) -> dict:
        """SMTP bağlantısını test et"""
        try:
            if not self.smtp_email or not self.smtp_password:
                return {
                    "success": False,
                    "message": "SMTP email veya password ayarlanmamış. .env dosyasını kontrol edin."
                }
            
            logger.info(f"🔌 SMTP bağlantısı test ediliyor: {self.smtp_server}:{self.smtp_port}")
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_email, self.smtp_password)
            
            logger.info("✅ SMTP bağlantısı başarılı")
            return {
                "success": True,
                "message": "SMTP bağlantısı başarılı"
            }
            
        except Exception as e:
            logger.error(f"❌ SMTP bağlantı hatası: {str(e)}")
            return {
                "success": False,
                "message": f"SMTP bağlantı hatası: {str(e)}"
            }
    
    def send_single_email(self, reminder: dict, retry_count: int = 0) -> dict:
        """
        Tek bir mail gönder
        
        Args:
            reminder: Hatırlatma bilgileri
            retry_count: Kaçıncı deneme olduğu
            
        Returns:
            dict: Gönderim sonucu
        """
        try:
            # Test modu kontrolü
            if self.test_mode:
                logger.info(f"[TEST MODE] Mail gönderildi:")
                logger.info(f"  Alıcı: {reminder['yonetici_mail']}")
                logger.info(f"  Konu: 🔔 Hatırlatma - {reminder['ihale_adi']}")
                return {
                    "ihale_no": reminder["ihale_no"],
                    "ihale_adi": reminder["ihale_adi"],
                    "recipient": reminder["yonetici_mail"],
                    "status": "sent",
                    "timestamp": datetime.now(),
                    "error_message": None,
                    "retry_count": retry_count
                }
            
            # Mail içeriğini hazırla
            subject = f"🔔 Hatırlatma - {reminder['ihale_adi']}"
            body = self._create_email_body(reminder)
            
            # MIME mesaj oluştur
            msg = MIMEMultipart('alternative')
            msg['From'] = self.smtp_email
            msg['To'] = reminder["yonetici_mail"]
            msg['Subject'] = subject
            
            # Öncelik ayarla (1 gün kaldıysa yüksek öncelik)
            if reminder["kalan_gun"] == 1:
                msg['X-Priority'] = '1'
                msg['Importance'] = 'high'
            
            # HTML içeriği ekle
            html_part = MIMEText(body, 'html', 'utf-8')
            msg.attach(html_part)
            
            # SMTP üzerinden gönder
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_email, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"✅ Mail gönderildi: {reminder['yonetici']} ({reminder['ihale_adi']})")
            
            return {
                "ihale_no": reminder["ihale_no"],
                "ihale_adi": reminder["ihale_adi"],
                "recipient": reminder["yonetici_mail"],
                "status": "sent",
                "timestamp": datetime.now(),
                "error_message": None,
                "retry_count": retry_count
            }
            
        except Exception as e:
            logger.error(f"❌ Mail gönderim hatası: {str(e)}")
            return {
                "ihale_no": reminder["ihale_no"],
                "ihale_adi": reminder["ihale_adi"],
                "recipient": reminder["yonetici_mail"],
                "status": "failed",
                "timestamp": datetime.now(),
                "error_message": str(e),
                "retry_count": retry_count
            }
    
    def send_reminders(self, reminders_list: list) -> dict:
        """
        Toplu hatırlatma maili gönder
        
        Args:
            reminders_list: Gönderilecek hatırlatmalar listesi
            
        Returns:
            dict: Gönderim sonuçları
        """
        try:
            results = []
            sent_count = 0
            failed_count = 0
            
            logger.info(f"\n📧 {len(reminders_list)} mail gönderilecek...")
            
            for i, reminder in enumerate(reminders_list):
                logger.info(f"\n[{i+1}/{len(reminders_list)}] İşleniyor: {reminder['ihale_adi']}")
                
                # Mail gönder (retry mekanizması ile)
                max_retries = 3
                retry_delays = [5, 10, 30]  # saniye
                
                result = None
                for attempt in range(max_retries):
                    result = self.send_single_email(reminder, retry_count=attempt)
                    
                    if result["status"] == "sent":
                        sent_count += 1
                        break
                    else:
                        # Başarısız, tekrar dene
                        if attempt < max_retries - 1:
                            logger.warning(f"⚠️  Deneme {attempt + 1} başarısız. {retry_delays[attempt]} saniye sonra tekrar denenecek...")
                            time.sleep(retry_delays[attempt])
                        else:
                            failed_count += 1
                
                results.append(result)
                
                # Rate limiting (her mail arasında 2 saniye bekle)
                if i < len(reminders_list) - 1:
                    time.sleep(2)
            
            logger.info(f"\n📊 Gönderim Tamamlandı:")
            logger.info(f"  ✅ Başarılı: {sent_count}")
            logger.info(f"  ❌ Başarısız: {failed_count}")
            
            return {
                "success": True,
                "sent_count": sent_count,
                "failed_count": failed_count,
                "results": results
            }
            
        except Exception as e:
            logger.error(f"❌ Toplu gönderim hatası: {str(e)}")
            return {
                "success": False,
                "sent_count": 0,
                "failed_count": 0,
                "results": [],
                "error": str(e)
            }


if __name__ == "__main__":
    # Test
    from dotenv import load_dotenv
    load_dotenv()
    
    sender = EmailSender()
    
    # Bağlantı testi
    test_result = sender.test_connection()
    print(f"\n{'✅' if test_result['success'] else '❌'} {test_result['message']}")
