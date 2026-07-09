#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════════════
  PASSWORD HASH CRACKER v2.0 - Professional Edition
  hashlib orqali MD5/SHA-256 va boshqa algoritmlarni buzish
  
  Baholash: 3 + 3 + 2 + 2 = 10 ball
  • hashlib to'g'ri qo'llash
  • Wordlist bilan ishlash
  • Algoritm aniqlash
  • Tezlik va aniq natija
═══════════════════════════════════════════════════════════════════════════════
"""

import hashlib
import sys
import os
import time
from typing import List, Optional


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


# ─── Hash Algoritm Aniqlash ───────────────────────────────────────────────────
def hash_algoritmlarini_aniqlash(hesh: str) -> List[str]:
    """
    Hash uzunligiga qarab mumkin bo'lgan algoritmlarni aniqlaydi
    
    Args:
        hesh: Hash string (hex format)
        
    Returns:
        Mumkin bo'lgan algoritmlar ro'yxati
    """
    uzunlik = len(hesh)
    
    algoritm_map = {
        32:  ["md5"],
        40:  ["sha1"],
        56:  ["sha224"],
        64:  ["sha256"],
        96:  ["sha384"],
        128: ["sha512"],
    }
    
    return algoritm_map.get(uzunlik, [])


def hash_nomi_va_info(algoritm: str) -> str:
    """Algoritm haqida ma'lumot"""
    info_map = {
        "md5":    "MD5 (32 oktet) - Zaif, eski",
        "sha1":   "SHA-1 (40 oktet) - Zaif",
        "sha224": "SHA-224 (56 oktet) - O'rta",
        "sha256": "SHA-256 (64 oktet) - Kuchli",
        "sha384": "SHA-384 (96 oktet) - Kuchli",
        "sha512": "SHA-512 (128 oktet) - Kuchli",
    }
    return info_map.get(algoritm.lower(), f"{algoritm.upper()}")


# ─── So'zni Hashlab, Solishtirish ─────────────────────────────────────────────
def soz_heshla(soz: str, algoritm: str) -> str:
    """
    Berilgan so'zni belgilangan algoritm bilan heshlaydi
    
    Args:
        soz: Hashlash uchun so'z
        algoritm: Hash algoritmi
        
    Returns:
        Hesh (hex format)
    """
    try:
        h = hashlib.new(algoritm)
        h.update(soz.encode("utf-8"))
        return h.hexdigest()
    except ValueError:
        return ""


# ─── Hash Validatsiya ─────────────────────────────────────────────────────────
def hash_validatsiya(hesh: str) -> bool:
    """
    Hash formatini tekshiradi (faqat hex belgilar, to'g'ri uzunlik)
    
    Args:
        hesh: Tekshiriladigan hash
        
    Returns:
        True agar valid
    """
    try:
        int(hesh, 16)
        return len(hesh) in [32, 40, 56, 64, 96, 128]
    except ValueError:
        return False


# ─── Fayl Tekshirish ──────────────────────────────────────────────────────────
def fayl_tekshirish(yol: str) -> bool:
    """Fayl mavjudligi va o'qish mumkinligini tekshiradi"""
    if not os.path.isfile(yol):
        log_error(f"Fayl topilmadi: '{yol}'")
        return False
    
    if not os.access(yol, os.R_OK):
        log_error(f"Faylni o'qish uchun ruxsat yo'q: '{yol}'")
        return False
    
    return True


# ─── Asosiy Buzish Funksiyasi ─────────────────────────────────────────────────
def hash_buzish(hesh: str, wordlist_yol: str, algoritm: str) -> bool:
    """
    Wordlist orqali hashni buzishga harakat qiladi
    
    Args:
        hesh: Buzish uchun hash
        wordlist_yol: Wordlist fayli yo'li
        algoritm: Hash algoritmi
        
    Returns:
        True agar parol topilgan
    """
    
    print(f"\n{Rang.QALIN}{'═'*70}{Rang.RESET}")
    log_info(f"Algoritm   : {Rang.YASHIL}{hash_nomi_va_info(algoritm)}{Rang.RESET}")
    log_info(f"Wordlist   : {Rang.YASHIL}{wordlist_yol}{Rang.RESET}")
    log_info(f"Target Hash: {Rang.OQROQ}{hesh[:32]}...{Rang.RESET}")
    print(f"{Rang.QALIN}{'─'*70}{Rang.RESET}\n")
    
    sinab_korilgan = 0
    start_time = time.time()
    last_log_time = start_time
    
    try:
        with open(wordlist_yol, "r", encoding="utf-8", errors="ignore") as f:
            for qator in f:
                soz = qator.strip()
                
                # Bo'sh qatorlarni o'tkazish
                if not soz:
                    continue
                
                sinab_korilgan += 1
                
                # Progress har 500 da bir
                hozir = time.time()
                if hozir - last_log_time >= 0.5 or sinab_korilgan == 1:
                    ketgan = hozir - start_time
                    tezlik = sinab_korilgan / ketgan if ketgan > 0 else 0
                    
                    print(f"\r{Rang.SARIQ}[~]{Rang.RESET} "
                          f"{sinab_korilgan:>6} ta sinandi | "
                          f"{tezlik:>8.0f} parol/s | "
                          f"{ketgan:>6.1f}s",
                          end="", flush=True)
                    last_log_time = hozir
                
                # Hash solishtirish
                hisoblangan = soz_heshla(soz, algoritm)
                
                if hisoblangan and hisoblangan.lower() == hesh.lower():
                    # TOPILDI!
                    print()  # Yangi qatorga o'tish
                    ketgan = time.time() - start_time
                    
                    print(f"\n{Rang.QALIN}{'═'*70}{Rang.RESET}")
                    print(f"{Rang.YASHIL}{Rang.QALIN}  ✓ PAROL TOPILDI!{Rang.RESET}")
                    print(f"{Rang.QALIN}{'═'*70}{Rang.RESET}\n")
                    print(f"  {Rang.YASHIL}{Rang.QALIN}Parol: {soz}{Rang.RESET}\n")
                    print(f"{Rang.QALIN}{'─'*70}{Rang.RESET}")
                    print(f"  Sinab ko'rilgan : {sinab_korilgan:,} ta")
                    print(f"  Vaqt            : {ketgan:.2f} soniya")
                    print(f"  O'rtacha tezlik : {sinab_korilgan/ketgan:.0f} parol/s")
                    print(f"{Rang.QALIN}{'─'*70}{Rang.RESET}\n")
                    
                    return True
    
    except FileNotFoundError:
        log_error(f"Wordlist topilmadi: '{wordlist_yol}'")
        return False
    except PermissionError:
        log_error("Faylni o'qish uchun ruxsat yo'q")
        return False
    except Exception as e:
        log_error(f"Xatolik: {e}")
        return False
    
    # Topilmadi
    print()
    ketgan = time.time() - start_time
    
    print(f"\n{Rang.QALIN}{'═'*70}{Rang.RESET}")
    log_error("Parol topilmadi")
    print(f"{Rang.QALIN}{'═'*70}{Rang.RESET}\n")
    print(f"  Sinab ko'rilgan : {sinab_korilgan:,} ta parol")
    print(f"  Vaqt            : {ketgan:.2f} soniya")
    print(f"  O'rtacha tezlik : {sinab_korilgan/ketgan:.0f} parol/s")
    print()
    
    return False


# ─── Input Olimlari ───────────────────────────────────────────────────────────
def hash_kiritish() -> str:
    """Hash kiritish"""
    while True:
        hesh = input(f"\n{Rang.SARIQ}[?]{Rang.RESET} Hash kiriting "
                    f"(MD5/SHA1/SHA256/...): ").strip()
        
        if not hesh:
            log_warning("Hash bo'sh bo'lishi mumkin emas")
            continue
        
        if not hash_validatsiya(hesh):
            log_error("Noto'g'ri hash formati")
            print(f"  Faqat hex belgilar va to'g'ri uzunlik: 32, 40, 56, 64, 96, 128")
            continue
        
        return hesh


def algoritm_tanlash(mumkin_turlar: List[str]) -> str:
    """Algoritm tanlash"""
    if len(mumkin_turlar) == 1:
        log_success(f"Algoritm avtomatik aniqlandi: {Rang.YASHIL}{mumkin_turlar[0].upper()}{Rang.RESET}")
        return mumkin_turlar[0]
    
    print(f"\n{Rang.SARIQ}Mumkin bo'lgan algoritmlar:{Rang.RESET}")
    for i, alg in enumerate(mumkin_turlar, 1):
        print(f"  {i}. {hash_nomi_va_info(alg)}")
    
    while True:
        tanlash = input(f"\n{Rang.SARIQ}[?]{Rang.RESET} Algoritmni tanlang "
                       f"(1-{len(mumkin_turlar)}): ").strip()
        
        try:
            idx = int(tanlash) - 1
            if 0 <= idx < len(mumkin_turlar):
                return mumkin_turlar[idx]
            log_error(f"Noto'g'ri tanlov")
        except ValueError:
            log_error("Raqam kiriting")


def wordlist_kiritish() -> str:
    """Wordlist fayli kiritish"""
    while True:
        wl = input(f"{Rang.SARIQ}[?]{Rang.RESET} Wordlist fayl yo'li: ").strip()
        
        if not wl:
            log_warning("Yo'l bo'sh bo'lishi mumkin emas")
            continue
        
        if fayl_tekshirish(wl):
            return wl


# ─── Main ─────────────────────────────────────────────────────────────────────
def main() -> None:
    """Asosiy dastur"""
    print(f"""
{Rang.QIZIL}{Rang.QALIN}
╔═══════════════════════════════════════════════════════════════╗
║             PASSWORD HASH CRACKER v2.0                       ║
║      MD5 / SHA-256 va boshqa Heshlarni Buzish                ║
╚═══════════════════════════════════════════════════════════════╝
{Rang.RESET}
""")
    
    # Hash kiritish
    hesh = hash_kiritish()
    
    # Algoritm aniqlash
    mumkin_turlar = hash_algoritmlarini_aniqlash(hesh)
    if not mumkin_turlar:
        log_error("Hash uzunligi noma'lum algoritm uchun")
        sys.exit(1)
    
    algoritm = algoritm_tanlash(mumkin_turlar)
    
    # Wordlist kiritish
    wordlist = wordlist_kiritish()
    
    # Buzish
    topildi = hash_buzish(hesh, wordlist, algoritm)
    
    sys.exit(0 if topildi else 1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Rang.SARIQ}[!]{Rang.RESET} Dastur to'xtatildi.")
        sys.exit(0)
    except Exception as e:
        log_error(f"Kutilmagan xatolik: {e}")
        sys.exit(1)
