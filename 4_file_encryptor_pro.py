#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════════════
  FILE ENCRYPTOR/DECRYPTOR v2.0 - Professional Edition
  Fernet simmetrik shifrlash orqali fayllarni shifrlash/deshifrlash
  
  ⚠️  FAQAT TA'LIM MAQSADLARI UCHUN - TEST PAPKASIDA ISHLATING!
  
  Baholash: 3 + 4 + 2 + 1 = 10 ball
  • os.walk orqali rekursiv fayl qidirish
  • cryptography.fernet shifrlash/deshifrlash
  • Kalit boshqaruvi
  • Ogohlantirish va tasdiqlash
═══════════════════════════════════════════════════════════════════════════════
"""

import sys
import os
import time
from pathlib import Path
from typing import List, Optional

try:
    from cryptography.fernet import Fernet, InvalidToken
except ImportError:
    print("[!] 'cryptography' o'rnatilmagan: pip install cryptography")
    sys.exit(1)


class Rang:
    """Terminal ranglar"""
    YASHIL = "\033[92m"
    QIZIL  = "\033[91m"
    SARIQ  = "\033[93m"
    MOVIY  = "\033[94m"
    OQROQ  = "\033[96m"
    QALIN  = "\033[1m"
    RESET  = "\033[0m"


def log_info(matn: str) -> None:
    print(f"{Rang.MOVIY}[*]{Rang.RESET} {matn}")


def log_success(matn: str) -> None:
    print(f"{Rang.YASHIL}[+]{Rang.RESET} {matn}")


def log_error(matn: str) -> None:
    print(f"{Rang.QIZIL}[-]{Rang.RESET} {matn}")


def log_warning(matn: str) -> None:
    print(f"{Rang.SARIQ}[!]{Rang.RESET} {matn}")


# ─── Konstantalar ─────────────────────────────────────────────────────────────
KALIT_FAYLI = "encryption.key"
SHIFRLASH_SUFFIX = ".encrypted"
MAQSAD_KENGAYTMALAR = {".txt", ".pdf", ".docx", ".xlsx", ".csv", ".json", ".log", ".xml"}


# ─── Ogohlantirish ────────────────────────────────────────────────────────────
def ogohlantirish_korsatish() -> bool:
    """
    Foydalanuvchiga muhim ogohlantirish ko'rsatadi
    
    Returns:
        True agar tasdiqlangan, False agar bekor qilgan
    """
    print(f"""
{Rang.QIZIL}{Rang.QALIN}
╔═══════════════════════════════════════════════════════════════════╗
║                  ⚠️  MUHIM OGOHLANTIRISH!  ⚠️                       ║
╠═══════════════════════════════════════════════════════════════════╣
║                                                                   ║
║  Bu dastur FAQAT TA'LIM MAQSADLARI uchun mo'ljallangan!           ║
║                                                                   ║
║  ⚠️  QAYD: Kalit yo'qotilsa → Fayllarni Qaytarib Bo'lmaydi!        ║
║                                                                   ║
║  Xavfsizlik bo'yicha tavsiyalar:                                  ║
║  ✓ Faqat TEST papkasida ishlating                                 ║
║  ✓ {KALIT_FAYLI} ni xavfsiz saqlang                               ║
║  ✓ Muhim fayllarning zaxirasini oling                             ║
║  ✓ Amaliy saytda ISHLATMANG                                       ║
║                                                                   ║
╚═══════════════════════════════════════════════════════════════════╝
{Rang.RESET}
""")
    
    tasdiqlash = input(
        f"{Rang.SARIQ}[?]{Rang.RESET} Davom etish uchun 'HA' yozing: "
    ).strip().upper()
    
    return tasdiqlash == "HA"


# ─── Kalit Boshqaruvi ─────────────────────────────────────────────────────────
def kalit_yaratish() -> bytes:
    """
    Yangi Fernet kalitini yaratadi va saqlaydi
    
    Returns:
        Yaratilgan kalit (bytes)
    """
    kalit = Fernet.generate_key()
    
    try:
        with open(KALIT_FAYLI, "wb") as f:
            f.write(kalit)
        log_success(f"Yangi kalit yaratildi va '{KALIT_FAYLI}' ga saqlandi")
        print(f"  Kalit (backup): {kalit.decode()}\n")
    except IOError as e:
        log_error(f"Kalit saqlash xatosi: {e}")
        return None
    
    return kalit


def kalit_yuklash() -> Optional[bytes]:
    """
    Mavjud kalitni fayldan o'qiydi
    
    Returns:
        Kalit (bytes) yoki None
    """
    if not os.path.isfile(KALIT_FAYLI):
        log_error(f"Kalit fayli topilmadi: '{KALIT_FAYLI}'")
        return None
    
    try:
        with open(KALIT_FAYLI, "rb") as f:
            return f.read()
    except IOError as e:
        log_error(f"Kalit o'qish xatosi: {e}")
        return None


def kalit_olinishi(papka: str) -> Optional[bytes]:
    """
    Kalitni olish (yaratish yoki yuklash)
    
    Args:
        papka: Ish papkasi
        
    Returns:
        Kalit (bytes) yoki None
    """
    
    kalit = kalit_yuklash()
    if kalit:
        return kalit
    
    # Kalit yo'q - yaratishmi?
    print()
    yaratish = input(
        f"{Rang.SARIQ}[?]{Rang.RESET} Kalit fayli yo'q. Yangi kalit yaratilaymi? "
        f"(HA/YO'Q): "
    ).strip().upper()
    
    if yaratish == "HA":
        return kalit_yaratish()
    
    log_warning("Kalit mavjud emas")
    return None


# ─── Fayllarni Topish ─────────────────────────────────────────────────────────
def shifrlash_uchun_fayllar_topish(papka: str) -> List[str]:
    """
    os.walk orqali shifrlash uchun fayllarni topadi
    
    Args:
        papka: Ish papkasi
        
    Returns:
        Fayl yo'llari ro'yxati
    """
    fayllar = []
    
    for ildiz, _, fayl_nomlari in os.walk(papka):
        for fayl_nomi in fayl_nomlari:
            # Allaqachon shifrlangan yoki kalit fayli?
            if fayl_nomi.endswith(SHIFRLASH_SUFFIX) or fayl_nomi == KALIT_FAYLI:
                continue
            
            # Kengaytma tekshirish
            _, keng = os.path.splitext(fayl_nomi)
            if keng.lower() not in MAQSAD_KENGAYTMALAR:
                continue
            
            fayl_yol = os.path.join(ildiz, fayl_nomi)
            fayllar.append(fayl_yol)
    
    return fayllar


# ─── Papkani Shifrlash ────────────────────────────────────────────────────────
def papkani_shifrlash(papka: str, fernet: Fernet) -> None:
    """
    Papkadagi barcha maqsad fayllarni shifrlaydi
    
    Args:
        papka: Shifrlash uchun papka
        fernet: Fernet cipher
    """
    
    fayllar = shifrlash_uchun_fayllar_topish(papka)
    
    if not fayllar:
        log_warning("Shifrlash uchun fayl topilmadi")
        return
    
    print(f"\n{Rang.QALIN}{'═'*70}{Rang.RESET}")
    log_info(f"Shifrlash boshlandi: {Rang.QALIN}{papka}{Rang.RESET}")
    log_info(f"Fayllar: {len(fayllar)} ta")
    print(f"{Rang.QALIN}{'─'*70}{Rang.RESET}\n")
    
    shifrlangan = 0
    xato = 0
    start_time = time.time()
    
    for i, fayl_yol in enumerate(fayllar, 1):
        fayl_nomi = os.path.basename(fayl_yol)
        
        # Progress
        print(f"\r{Rang.MOVIY}[~]{Rang.RESET} [{i}/{len(fayllar)}] "
              f"{fayl_nomi[:50]:<50}",
              end="", flush=True)
        
        try:
            # Faylni o'qish
            with open(fayl_yol, "rb") as f:
                asl_mazmun = f.read()
            
            # Shifrlash
            shifrlangan_mazmun = fernet.encrypt(asl_mazmun)
            
            # Shifrlangan faylni yozish
            with open(fayl_yol, "wb") as f:
                f.write(shifrlangan_mazmun)
            
            # .encrypted kengaytma qo'shish
            yangi_yol = fayl_yol + SHIFRLASH_SUFFIX
            os.rename(fayl_yol, yangi_yol)
            
            print()
            log_success(f"{fayl_nomi} → {fayl_nomi}{SHIFRLASH_SUFFIX}")
            shifrlangan += 1
        
        except (IOError, OSError) as e:
            print()
            log_error(f"{fayl_nomi}: {e}")
            xato += 1
    
    ketgan = time.time() - start_time
    
    print(f"\n{Rang.QALIN}{'─'*70}{Rang.RESET}")
    log_success(f"Jami shifrlandi: {shifrlangan} ta fayl")
    if xato:
        log_warning(f"Xatolar: {xato} ta")
    log_info(f"Vaqt: {ketgan:.2f}s")
    print(f"{Rang.QALIN}{'═'*70}{Rang.RESET}\n")


# ─── Papkani Deshifrlash ──────────────────────────────────────────────────────
def papkani_deshifrlash(papka: str, fernet: Fernet) -> None:
    """
    Papkadagi barcha .encrypted fayllarni deshifrlaydi
    
    Args:
        papka: Deshifrlash uchun papka
        fernet: Fernet cipher
    """
    
    # .encrypted fayllarni topish
    shifrlangan_fayllar = []
    for ildiz, _, fayl_nomlari in os.walk(papka):
        for fayl_nomi in fayl_nomlari:
            if fayl_nomi.endswith(SHIFRLASH_SUFFIX):
                fayl_yol = os.path.join(ildiz, fayl_nomi)
                shifrlangan_fayllar.append(fayl_yol)
    
    if not shifrlangan_fayllar:
        log_warning("Deshifrlash uchun fayl topilmadi")
        return
    
    print(f"\n{Rang.QALIN}{'═'*70}{Rang.RESET}")
    log_info(f"Deshifrlash boshlandi: {Rang.QALIN}{papka}{Rang.RESET}")
    log_info(f"Fayllar: {len(shifrlangan_fayllar)} ta")
    print(f"{Rang.QALIN}{'─'*70}{Rang.RESET}\n")
    
    deshifrlangan = 0
    xato = 0
    start_time = time.time()
    
    for i, fayl_yol in enumerate(shifrlangan_fayllar, 1):
        fayl_nomi = os.path.basename(fayl_yol)
        
        print(f"\r{Rang.MOVIY}[~]{Rang.RESET} [{i}/{len(shifrlangan_fayllar)}] "
              f"{fayl_nomi[:50]:<50}",
              end="", flush=True)
        
        try:
            # Shifrlangan faylni o'qish
            with open(fayl_yol, "rb") as f:
                shifrlangan_mazmun = f.read()
            
            # Deshifrlash
            asl_mazmun = fernet.decrypt(shifrlangan_mazmun)
            
            # Asl nomga qaytarish
            asl_yol = fayl_yol[:-len(SHIFRLASH_SUFFIX)]
            with open(asl_yol, "wb") as f:
                f.write(asl_mazmun)
            
            # Shifrlangan faylni o'chirish
            os.remove(fayl_yol)
            
            print()
            log_success(f"{fayl_nomi} → {os.path.basename(asl_yol)}")
            deshifrlangan += 1
        
        except InvalidToken:
            print()
            log_error(f"{fayl_nomi}: Noto'g'ri kalit!")
            xato += 1
        except (IOError, OSError) as e:
            print()
            log_error(f"{fayl_nomi}: {e}")
            xato += 1
    
    ketgan = time.time() - start_time
    
    print(f"\n{Rang.QALIN}{'─'*70}{Rang.RESET}")
    log_success(f"Jami deshifrlandi: {deshifrlangan} ta fayl")
    if xato:
        log_warning(f"Xatolar: {xato} ta")
    log_info(f"Vaqt: {ketgan:.2f}s")
    print(f"{Rang.QALIN}{'═'*70}{Rang.RESET}\n")


# ─── Main ─────────────────────────────────────────────────────────────────────
def main() -> None:
    """Asosiy dastur"""
    print(f"""
{Rang.MOVIY}{Rang.QALIN}
╔═══════════════════════════════════════════════════════════════╗
║                FILE ENCRYPTOR/DECRYPTOR v2.0                  ║
║                     Fernet Shifrlash                          ║
╚═══════════════════════════════════════════════════════════════╝
{Rang.RESET}
""")
    
    # Ogohlantirish
    if not ogohlantirish_korsatish():
        log_warning("Bekor qilindi")
        sys.exit(0)
    
    # Menyu
    print(f"""
{Rang.QALIN}Amallar:{Rang.RESET}
  1. Yangi kalit yaratish
  2. Papkani shifrlash
  3. Papkani deshifrlash
  0. Chiqish
""")
    
    while True:
        tanlov = input(f"{Rang.SARIQ}[?]{Rang.RESET} Amalni tanlang (0-3): ").strip()
        
        if tanlov == "0":
            log_info("Dastur to'xtatildi")
            sys.exit(0)
        
        elif tanlov == "1":
            # Kalit yaratish
            if os.path.isfile(KALIT_FAYLI):
                ogoh_tanlov = input(
                    f"{Rang.SARIQ}[?]{Rang.RESET} '{KALIT_FAYLI}' mavjud. "
                    f"Ustiga yozilsinmi? (HA/YO'Q): "
                ).strip().upper()
                
                if ogoh_tanlov != "HA":
                    log_warning("Yaratilmadi")
                    continue
            
            print()
            kalit = kalit_yaratish()
            if kalit:
                # Parolsiz davom
                tanlov_input = input(
                    f"{Rang.SARIQ}[?]{Rang.RESET} Boshqa amalni tanlaysizmi? (HA/YO'Q): "
                ).strip().upper()
                if tanlov_input != "HA":
                    sys.exit(0)
        
        elif tanlov in ("2", "3"):
            # Papka tanlash
            while True:
                papka = input(
                    f"{Rang.SARIQ}[?]{Rang.RESET} Papka yo'lini kiriting: "
                ).strip()
                
                if not papka:
                    log_warning("Papka bo'sh")
                    continue
                
                if not os.path.isdir(papka):
                    log_error(f"Papka topilmadi: '{papka}'")
                    continue
                
                break
            
            # Kalit
            kalit = kalit_olinishi(papka)
            if not kalit:
                continue
            
            try:
                fernet = Fernet(kalit)
            except Exception as e:
                log_error(f"Kalit xatosi: {e}")
                continue
            
            print()
            
            # Shifrlash yoki deshifrlash
            if tanlov == "2":
                papkani_shifrlash(papka, fernet)
            else:
                papkani_deshifrlash(papka, fernet)
            
            # Davom
            tanlov_input = input(
                f"{Rang.SARIQ}[?]{Rang.RESET} Boshqa amalni tanlaysizmi? (HA/YO'Q): "
            ).strip().upper()
            if tanlov_input != "HA":
                sys.exit(0)
        
        else:
            log_error("Noto'g'ri tanlov")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Rang.SARIQ}[!]{Rang.RESET} Dastur to'xtatildi.")
        sys.exit(0)
    except Exception as e:
        log_error(f"Kutilmagan xatolik: {e}")
        sys.exit(1)
