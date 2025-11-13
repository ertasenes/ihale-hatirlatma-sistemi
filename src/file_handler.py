"""
File Handler Module
İhale takvim dosyasını okuma, validasyon ve güncelleme işlemlerini yapar.
"""

import pandas as pd
from datetime import datetime
from pathlib import Path
import logging
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FileHandler:
    """İhale dosyası yönetim sınıfı"""
    
    def __init__(self, file_path: str = "data/Merkezi_Takvimi.xlsx"):
        self.file_path = Path(file_path)
        self.df = None
        
    def validate_email(self, email: str) -> bool:
        """Email formatını kontrol et"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    def read_ihale_file(self) -> dict:
        """
        İhale dosyasını oku ve validasyon yap
        
        Returns:
            dict: Başarı durumu, ihale listesi, hatalar ve uyarılar
        """
        try:
            # Dosya kontrolü
            if not self.file_path.exists():
                return {
                    "success": False,
                    "data": [],
                    "errors": [f"Dosya bulunamadı: {self.file_path}"],
                    "warnings": [],
                    "total_count": 0,
                    "valid_count": 0
                }
            
            # Excel dosyasını oku
            logger.info(f"İhale dosyası okunuyor: {self.file_path}")
            self.df = pd.read_excel(self.file_path)
            
            # Sütun isimlerini temizle (gereksiz boşlukları ve newline karakterlerini kaldır)
            self.df.columns = self.df.columns.str.strip().str.replace('\n', '').str.replace('  ', ' ')
            
            # Hücrelerdeki boşlukları da temizle
            for col in self.df.select_dtypes(include=['object']).columns:
                if col != 'Hatırlatma Durumu':  # Bu sütun zaten None olabilir
                    self.df[col] = self.df[col].apply(lambda x: x.strip() if isinstance(x, str) else x)
            
            ihale_list = []
            errors = []
            warnings = []
            
            # Her satırı işle
            for idx, row in self.df.iterrows():
                try:
                    # Boş satırları atla
                    if pd.isna(row.get('S.no')):
                        continue
                    
                    ihale_no = int(row['S.no'])
                    ihale_adi = str(row['Toplantı Adı']).strip()
                    yonetici = str(row['D.Serve İlgili Kişi']).strip()
                    yonetici_mail = str(row['D.serve İlgili Kişi Mail']).strip()
                    baslangic_tarihi = row['Toplantı Hazırlıkları Başlangıç Dönemi']
                    hatirlatma_durumu = row.get('Hatırlatma Durumu')
                    
                    # Validasyonlar
                    if not ihale_adi or ihale_adi == 'nan':
                        errors.append(f"Satır {idx+2}: İhale adı boş")
                        continue
                    
                    if not yonetici or yonetici == 'nan':
                        errors.append(f"Satır {idx+2}: Yönetici boş")
                        continue
                    
                    if not self.validate_email(yonetici_mail):
                        errors.append(f"Satır {idx+2}: Geçersiz mail adresi: {yonetici_mail}")
                        continue
                    
                    # Tarih kontrolü
                    if pd.isna(baslangic_tarihi):
                        errors.append(f"Satır {idx+2}: Başlangıç tarihi boş")
                        continue
                    
                    # Tarihi datetime'a çevir
                    if not isinstance(baslangic_tarihi, datetime):
                        try:
                            baslangic_tarihi = pd.to_datetime(baslangic_tarihi)
                        except:
                            errors.append(f"Satır {idx+2}: Geçersiz tarih formatı")
                            continue
                    
                    # Geçmiş tarih kontrolü
                    if baslangic_tarihi.date() < datetime.now().date():
                        warnings.append(f"İhale {ihale_no} ({ihale_adi}): Başlangıç tarihi geçmişte ({baslangic_tarihi.date()})")
                    
                    # İhale dictionary'si oluştur
                    ihale_dict = {
                        "ihale_no": ihale_no,
                        "ihale_adi": ihale_adi,
                        "yonetici": yonetici,
                        "yonetici_mail": yonetici_mail,
                        "baslangic_tarihi": baslangic_tarihi,
                        "hatirlatma_durumu": str(hatirlatma_durumu) if pd.notna(hatirlatma_durumu) else None
                    }
                    
                    ihale_list.append(ihale_dict)
                    
                except Exception as e:
                    errors.append(f"Satır {idx+2}: İşlenirken hata: {str(e)}")
            
            logger.info(f"✅ {len(ihale_list)} ihale başarıyla okundu")
            if errors:
                logger.warning(f"⚠️  {len(errors)} hata bulundu")
            if warnings:
                logger.warning(f"⚠️  {len(warnings)} uyarı bulundu")
            
            return {
                "success": True,
                "data": ihale_list,
                "errors": errors,
                "warnings": warnings,
                "total_count": len(self.df),
                "valid_count": len(ihale_list)
            }
            
        except Exception as e:
            logger.error(f"❌ Dosya okuma hatası: {str(e)}")
            return {
                "success": False,
                "data": [],
                "errors": [f"Dosya okuma hatası: {str(e)}"],
                "warnings": [],
                "total_count": 0,
                "valid_count": 0
            }
    
    def update_hatirlatma_durumu(self, ihale_no: int, hatirlatma_tipi: str, tarih: datetime) -> bool:
        """
        İhalenin hatırlatma durumunu güncelle
        
        Args:
            ihale_no: İhale numarası
            hatirlatma_tipi: 60_gun, 30_gun veya 1_gun
            tarih: Gönderim tarihi
            
        Returns:
            bool: Başarı durumu
        """
        try:
            if self.df is None:
                logger.error("Dosya okunmamış")
                return False
            
            # İhaleyi bul
            mask = self.df['S.no'] == ihale_no
            if not mask.any():
                logger.error(f"İhale {ihale_no} bulunamadı")
                return False
            
            # Mevcut durumu al
            current_status = self.df.loc[mask, 'Hatırlatma Durumu'].iloc[0]
            
            # Yeni durum bilgisi
            new_entry = f"{hatirlatma_tipi}:{tarih.strftime('%Y-%m-%d')}"
            
            if pd.isna(current_status):
                new_status = new_entry
            else:
                new_status = f"{current_status}, {new_entry}"
            
            # Güncelle
            self.df.loc[mask, 'Hatırlatma Durumu'] = new_status
            
            # Dosyayı kaydet
            self.df.to_excel(self.file_path, index=False)
            logger.info(f"✅ İhale {ihale_no} hatırlatma durumu güncellendi: {hatirlatma_tipi}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Güncelleme hatası: {str(e)}")
            return False
    
    def backup_file(self) -> bool:
        """Dosyanın yedeğini al"""
        try:
            backup_dir = Path("data/backups")
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = backup_dir / f"Merkezi_Takvimi_backup_{timestamp}.xlsx"
            
            if self.file_path.exists():
                import shutil
                shutil.copy2(self.file_path, backup_path)
                logger.info(f"✅ Backup oluşturuldu: {backup_path}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Backup hatası: {str(e)}")
            return False


if __name__ == "__main__":
    # Test
    handler = FileHandler()
    result = handler.read_ihale_file()
    
    if result["success"]:
        print(f"\n✅ Toplam {result['valid_count']} ihale okundu\n")
        for ihale in result["data"][:3]:
            print(f"İhale: {ihale['ihale_adi']}")
            print(f"Yönetici: {ihale['yonetici']} ({ihale['yonetici_mail']})")
            print(f"Başlangıç: {ihale['baslangic_tarihi'].date()}")
            print("-" * 50)
    
    if result["errors"]:
        print("\n❌ Hatalar:")
        for error in result["errors"]:
            print(f"  - {error}")
    
    if result["warnings"]:
        print("\n⚠️  Uyarılar:")
        for warning in result["warnings"]:
            print(f"  - {warning}")
