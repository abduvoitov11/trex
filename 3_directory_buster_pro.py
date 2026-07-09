#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════════════
  WEB DIRECTORY BUSTER v2.0 - Professional Edition
  requests orqali veb-saytdagi yashirin sahifalarni topish (soft-404 aniqlash)
  
  Baholash: 4 + 3 + 2 + 1 = 10 ball
  • requests to'g'ri qo'llash
  • HTTP status kodlarini tahlil qilish
  • User-Agent boshqarish
  • Formatted output
═══════════════════════════════════════════════════════════════════════════════
"""

import sys
import os
import time
import threading
import uuid
from urllib.parse import urlparse
from collections import deque
from typing import Dict, List, Optional

try:
    import requests
    from requests.exceptions import RequestException, Timeout, ConnectionError as ConnErr
except ImportError:
    print("[!] 'requests' o'rnatilmagan: pip install requests")
    sys.exit(1)


class Rang:
    """Terminal ranglar"""
    YASHIL = "\033[92m"
    QIZIL  = "\033[91m"
    SARIQ  = "\033[93m"
    MOVIY  = "\033[94m"
    OQROQ  = "\033[96m"
    QALIN  = "\033[1m"
    KULRANG= "\033[90m"
    RESET  = "\033[0m"


def log_info(matn: str) -> None:
    print(f"{Rang.MOVIY}[*]{Rang.RESET} {matn}")


def log_success(matn: str) -> None:
    print(f"{Rang.YASHIL}[+]{Rang.RESET} {matn}")


def log_error(matn: str) -> None:
    print(f"{Rang.QIZIL}[-]{Rang.RESET} {matn}")


def log_warning(matn: str) -> None:
    print(f"{Rang.SARIQ}[!]{Rang.RESET} {matn}")


# ─── URL Normallashtirish ─────────────────────────────────────────────────────
def url_normallashtir(url: str) -> Optional[str]:
    """
    URLni tekshiradi va normallashtiradi
    
    Args:
        url: Istalgan format
        
    Returns:
        Normallashtirgan URL yoki None
    """
    if not url.startswith(("http://", "https://")):
        url = "http://" + url
    
    try:
        parsed = urlparse(url)
        if parsed.netloc:
            return url.rstrip("/")
    except Exception:
        pass
    
    return None


# ─── Baseline Hisoblash (Soft-404 Aniqlash) ───────────────────────────────────
def baseline_ol(session: requests.Session, asosiy_url: str, timeout: int) -> Optional[Dict]:
    """
    Soft-404 aniqlash uchun "yo'q sahifa" baseline'ini yaratadi
    
    Args:
        session: Requests session
        asosiy_url: Nishon URL
        timeout: Timeout soniya
        
    Returns:
        Baseline ma'lumoti yoki None
    """
    log_warning("Sayt xususiyatlari aniqlanmoqda (3 ta fake request)...")
    
    baselines = []
    
    for i in range(3):
        fake_path = f"/{uuid.uuid4().hex}/{uuid.uuid4().hex}.php"
        
        try:
            r = session.get(
                asosiy_url + fake_path,
                timeout=timeout,
                allow_redirects=True
            )
            baselines.append({
                "status": r.status_code,
                "size": len(r.text),
                "text": r.text,
            })
            time.sleep(0.2)
        except Exception:
            pass
    
    if not baselines:
        log_error("Baseline ololmadi - sayt javob bermayapti")
        return None
    
    # O'rtacha hajm
    ort_size = sum(b["size"] for b in baselines) / len(baselines)
    asosiy_status = baselines[0]["status"]
    soft_404 = (asosiy_status == 200)
    
    # Title yoki fragment chiqarish
    matn_belgisi = ""
    if baselines[0]["text"]:
        matn = baselines[0]["text"]
        if "<title>" in matn.lower():
            bosh = matn.lower().find("<title>") + 7
            oxir = matn.lower().find("</title>", bosh)
            matn_belgisi = matn[bosh:oxir].strip()[:80] if oxir > bosh else ""
        if not matn_belgisi:
            matn_belgisi = matn[:150].strip()
    
    log_success(f"Baseline: status={asosiy_status}, o'rt.hajm={ort_size:.0f}b, "
               f"soft-404={'HA' if soft_404 else 'YO\'Q'}")
    
    return {
        "status": asosiy_status,
        "ort_size": ort_size,
        "soft_404": soft_404,
        "matn_belgisi": matn_belgisi,
    }


# ─── Sahifa Tekshirish ─────────────────────────────────────────────────────────
def sahifa_tekshir(session: requests.Session, url: str, baseline: Dict,
                   timeout: int) -> Optional[Dict]:
    """
    Bitta URL ni tekshiradi
    
    Args:
        session: Requests session
        url: Tekshiriladigan URL
        baseline: Baseline ma'lumoti
        timeout: Timeout
        
    Returns:
        Natija dict yoki None (yo'q/xato)
    """
    try:
        r = session.get(url, timeout=timeout, allow_redirects=True)
        status = r.status_code
        size = len(r.text)
        
        # — 404 = aniq yo'q
        if status == 404:
            return None
        
        # — Redirect
        if status in (301, 302, 307, 308):
            redirect = r.headers.get("Location", "")
            if not redirect or redirect.rstrip("/") == url.rstrip("/"):
                return None
            return {
                "status": status,
                "size": size,
                "holat": f"REDIRECT"
            }
        
        # — 403/401 = mavjud lekin taqiqlangan
        if status in (401, 403):
            return {
                "status": status,
                "size": size,
                "holat": "TAQIQLANGAN"
            }
        
        # — 500+ server xatosi
        if status >= 500:
            return None
        
        # — 200: Soft-404 tekshiruvi
        if status == 200:
            if baseline["soft_404"]:
                # Hajm farqi
                ort = baseline["ort_size"]
                if ort > 0:
                    farq_nisbat = abs(size - ort) / ort
                    
                    if farq_nisbat < 0.15:
                        # Matn belgisi ni ham tekshir
                        if baseline["matn_belgisi"]:
                            if baseline["matn_belgisi"][:50].lower() in r.text.lower():
                                return None  # Soft-404
                        else:
                            return None
            
            return {
                "status": status,
                "size": size,
                "holat": "MAVJUD"
            }
        
        # Boshqa statuslar
        return {
            "status": status,
            "size": size,
            "holat": f"STATUS {status}"
        }
    
    except (Timeout, ConnErr):
        return None
    except RequestException:
        return None


# ─── Asosiy Skanerlash ────────────────────────────────────────────────────────
def skanerlash(asosiy_url: str, wordlist_yol: str, timeout: int,
               threads: int, kengaytmalar: List[str]) -> None:
    """
    Web directory skanerlashni boshlaydi
    """
    
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Connection": "close",
    }
    
    session = requests.Session()
    session.headers.update(headers)
    
    # Wordlist o'qish
    try:
        with open(wordlist_yol, "r", encoding="utf-8", errors="ignore") as f:
            sozlar = [q.strip() for q in f if q.strip() and not q.startswith("#")]
    except Exception as e:
        log_error(f"Wordlist o'qib bo'lmadi: {e}")
        return
    
    # URL ro'yxati yaratish
    urllar = []
    for soz in sozlar:
        urllar.append(f"{asosiy_url}/{soz}")
        for keng in kengaytmalar:
            if not soz.endswith(keng):
                urllar.append(f"{asosiy_url}/{soz}{keng}")
    
    jami = len(urllar)
    
    # Baseline
    baseline = baseline_ol(session, asosiy_url, timeout)
    if baseline is None:
        return
    
    print(f"\n{Rang.QALIN}{'═'*70}{Rang.RESET}")
    log_info(f"Nishon     : {Rang.QALIN}{asosiy_url}{Rang.RESET}")
    log_info(f"URL lar    : {len(sozlar)} so'z × {1+len(kengaytmalar)} kengaytma = {jami} URL")
    log_info(f"Threadlar  : {threads}, Timeout: {timeout}s")
    print(f"{Rang.QALIN}{'─'*70}{Rang.RESET}\n")
    
    topilganlar = []
    lock = threading.Lock()
    counter = [0]
    queue = deque(urllar)
    start_time = time.time()
    
    def worker():
        while True:
            with lock:
                if not queue:
                    return
                url = queue.popleft()
                counter[0] += 1
                n = counter[0]
            
            natija = sahifa_tekshir(session, url, baseline, timeout)
            
            with lock:
                # Progress
                foiz = (n / jami) * 100
                yo_l = url.replace(asosiy_url, "").replace("//", "/")
zz	                
                print(
                    f"\r{Rang.KULRANG}[~]{Rang.RESET} [{foiz:5.1f}%] {n}/{jami}  "
                    f"{yo_l[:45]:<45}",
                    end="", flush=True
                )
                
                if natija:
                    print()  # yangi qator
                    holat = natija["holat"]
                    status = natija["status"]
                    size = natija["size"]
                    
                    # Rang tanlash
                    if holat == "MAVJUD":
                        rang = Rang.YASHIL
                        belgi = "+"
                    elif holat == "TAQIQLANGAN":
                        rang = Rang.SARIQ
                        belgi = "!"
                    elif holat == "REDIRECT":
                        rang = Rang.MOVIY
                        belgi = ">"
                    else:
                        rang = Rang.OQROQ
                        belgi = "?"
                    
                    log_success(
                        f"{rang}{holat:<14}{Rang.RESET} "
                        f"[{status}] {yo_l} ({size} b)"
                    )
                    topilganlar.append((url, status, holat, size))
    
    # Thread pool
    threadlar = [threading.Thread(target=worker, daemon=True) for _ in range(threads)]
    for t in threadlar:
        t.start()
    for t in threadlar:
        t.join()
    
    # Yakuniy hisobot
    ketgan = time.time() - start_time
    
    print(f"\n\n{Rang.QALIN}{'═'*70}{Rang.RESET}")
    print(f"{Rang.QALIN}  SKANERLASH YAKUNLANDI{Rang.RESET}")
    print(f"{'═'*70}")
    print(f"  Tekshirildi : {counter[0]:,} ta URL")
    print(f"  Topildi     : {len(topilganlar)} ta")
    print(f"  Vaqt        : {ketgan:.1f}s ({counter[0]/ketgan:.0f} URL/s)")
    print(f"{'─'*70}")
    
    if topilganlar:
        # Saralash
        topilganlar.sort(key=lambda x: x[1])
        
        print(f"\n{Rang.QALIN}  TOPILGAN SAHIFALAR:{Rang.RESET}\n")
        print(f"  {'STATUS':<7} {'HAJM':<9} {'HOLAT':<15} YO'L")
        print(f"  {'─'*65}")
        
        for url, st, holat, size in topilganlar:
            yo_l = url.replace(asosiy_url, "").replace("//", "/")
            
            if holat == "MAVJUD":
                rang = Rang.YASHIL
            elif holat == "TAQIQLANGAN":
                rang = Rang.SARIQ
            else:
                rang = Rang.MOVIY
            
            print(f"  {rang}[{st}]{Rang.RESET}  {size:<9} {holat:<15} {yo_l}")
        print()
    else:
        log_warning("Hech qanday sahifa topilmadi")
    
    print(f"{'═'*70}\n")


# ─── Main ─────────────────────────────────────────────────────────────────────
def main() -> None:
    """Asosiy dastur"""
    print(f"""
{Rang.MOVIY}{Rang.QALIN}
╔═══════════════════════════════════════════════════════════════╗
║             WEB DIRECTORY BUSTER v2.0                        ║
║      Soft-404 Aniqlash + Multi-thread + User-Agent           ║
╚═══════════════════════════════════════════════════════════════╝
{Rang.RESET}
""")
    
    # URL
    while True:
        url_in = input(f"{Rang.SARIQ}[?]{Rang.RESET} Nishon URL: ").strip()
        if not url_in:
            log_warning("URL bo'sh")
            continue
        url = url_normallashtir(url_in)
        if url:
            break
        log_error("Noto'g'ri URL")
    
    # Wordlist
    while True:
        wl = input(f"{Rang.SARIQ}[?]{Rang.RESET} Wordlist yo'li: ").strip()
        if not wl:
            log_warning("Yo'l bo'sh")
            continue
        if not os.path.isfile(wl):
            log_error(f"Fayl topilmadi: '{wl}'")
            continue
        break
    
    # Thread
    thr_in = input(f"{Rang.SARIQ}[?]{Rang.RESET} Thread (default 10): ").strip()
    threads = 10
    if thr_in.isdigit() and 1 <= int(thr_in) <= 50:
        threads = int(thr_in)
    
    # Timeout
    to_in = input(f"{Rang.SARIQ}[?]{Rang.RESET} Timeout (default 5): ").strip()
    timeout = 5
    if to_in.isdigit() and 1 <= int(to_in) <= 30:
        timeout = int(to_in)
    
    # Kengaytmalar
    keng_in = input(
        f"{Rang.SARIQ}[?]{Rang.RESET} Kengaytmalar [bo'sh=yo'q]: "
    ).strip()
    kengaytmalar = []
    if keng_in:
        kengaytmalar = [
            (k if k.startswith(".") else "." + k)
            for k in keng_in.split(",")
            if k.strip()
        ]
    
    print()
    skanerlash(url, wl, timeout, threads, kengaytmalar)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Rang.SARIQ}[!]{Rang.RESET} To'xtatildi.")
        sys.exit(0)
    except Exception as e:
        log_error(f"Xatolik: {e}")
        sys.exit(1)
