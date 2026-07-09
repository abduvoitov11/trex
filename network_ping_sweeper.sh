#!/bin/bash
#
# ==============================================================
#                  NETWORK PING SWEEPER + PORT SCANNER
#  Vazifa: Berilgan tarmoq prefiksidagi (masalan 192.168.1)
#          barcha hostlarni (1-255) ping qilib, tirik hostlarni
#          aniqlash, so'ngra har bir tirik host uchun eng ko'p
#          ishlatiladigan portlarni avtomatik skanerlash.
#
#  Natijalar:
#    - ishlayotgan_hostlar.txt  -> faqat tirik IP manzillar
#    - port_natijalari.txt      -> har bir host va ochiq portlari
# ==============================================================

GREEN='\033[0;32m'
RED='\033[0;31m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
NC='\033[0m'

HOSTS_FILE="ishlayotgan_hostlar.txt"
PORTS_FILE="port_natijalari.txt"

# ---------- Skanerlanadigan portlar ----------
# Eng ko'p ishlatiladigan (top) portlar ro'yxati. Xohlasangiz,
# skriptga 2-argument sifatida o'zingizning portlaringizni ham
# berishingiz mumkin: masalan  ./script.sh 192.168.1 22,80,443
DEFAULT_PORTS=(21 22 23 25 53 80 110 111 135 139 143 443 445 993 995 1723 3306 3389 5900 8080 8443)

usage() {
    echo -e "${YELLOW}Foydalanish:${NC} $0 <tarmoq_prefiksi> [portlar]"
    echo "Masalan:"
    echo "  $0 192.168.1                -> standart top-portlar bilan"
    echo "  $0 192.168.1 22,80,443      -> faqat shu portlarni tekshiradi"
    echo "  $0 192.168.1 1-1000         -> port oralig'ini tekshiradi"
    exit 1
}

if [ "$#" -lt 1 ] || [ "$#" -gt 2 ]; then
    echo -e "${RED}[XATO]${NC} Argumentlar soni noto'g'ri."
    usage
fi

PREFIX="$1"
PORT_ARG="${2:-}"

# ---------- Tarmoq prefiksini tekshirish ----------
if [[ ! "$PREFIX" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo -e "${RED}[XATO]${NC} Noto'g'ri format. Masalan: 192.168.1"
    exit 1
fi

IFS='.' read -ra OCTETS <<< "$PREFIX"
for octet in "${OCTETS[@]}"; do
    if (( octet < 0 || octet > 255 )); then
        echo -e "${RED}[XATO]${NC} '$octet' 0-255 oralig'ida bo'lishi kerak."
        exit 1
    fi
done

# ---------- Port argumentini tekshirish (agar berilgan bo'lsa) ----------
is_valid_port() {
    local p="$1"
    [[ "$p" =~ ^[0-9]+$ ]] && (( p >= 1 && p <= 65535 ))
}

PORTS_TO_SCAN=()

if [ -z "$PORT_ARG" ]; then
    PORTS_TO_SCAN=("${DEFAULT_PORTS[@]}")
elif [[ "$PORT_ARG" =~ ^[0-9]+-[0-9]+$ ]]; then
    START_PORT="${PORT_ARG%-*}"
    END_PORT="${PORT_ARG#*-}"
    if ! is_valid_port "$START_PORT" || ! is_valid_port "$END_PORT" || (( START_PORT > END_PORT )); then
        echo -e "${RED}[XATO]${NC} Port oralig'i noto'g'ri (masalan: 1-1000)."
        exit 1
    fi
    for (( p=START_PORT; p<=END_PORT; p++ )); do
        PORTS_TO_SCAN+=("$p")
    done
elif [[ "$PORT_ARG" =~ ^[0-9]+(,[0-9]+)*$ ]]; then
    IFS=',' read -ra RAW_PORTS <<< "$PORT_ARG"
    for p in "${RAW_PORTS[@]}"; do
        if ! is_valid_port "$p"; then
            echo -e "${RED}[XATO]${NC} '$p' noto'g'ri port raqami."
            exit 1
        fi
        PORTS_TO_SCAN+=("$p")
    done
else
    echo -e "${RED}[XATO]${NC} Port formati noto'g'ri."
    usage
fi

echo -e "${CYAN}==============================================${NC}"
echo -e "${CYAN} Tarmoq:${NC} ${PREFIX}.0/24"
echo -e "${CYAN} Tekshiriladigan portlar soni (har host uchun):${NC} ${#PORTS_TO_SCAN[@]}"
echo -e "${CYAN}==============================================${NC}"
echo -e "${CYAN}[1-BOSQICH]${NC} Tirik hostlar aniqlanmoqda..."

> "$HOSTS_FILE"
> "$PORTS_FILE"

TMP_DIR=$(mktemp -d)
START_TIME=$(date +%s)

# ============================================================
#  1-BOSQICH: PING SWEEP - tirik hostlarni topish
# ============================================================
for i in $(seq 1 254); do
    HOST="${PREFIX}.${i}"
    {
        if ping -c 1 -W 1 "$HOST" &>/dev/null; then
            echo "$HOST"
        fi
    } > "$TMP_DIR/ping_$i.result" &

    if (( i % 50 == 0 )); then
        wait
    fi
done
wait

ALIVE_HOSTS=()
for i in $(seq 1 254); do
    if [ -s "$TMP_DIR/ping_$i.result" ]; then
        ALIVE_HOSTS+=("$(cat "$TMP_DIR/ping_$i.result")")
    fi
done

PING_END_TIME=$(date +%s)
PING_ELAPSED=$((PING_END_TIME - START_TIME))

if [ "${#ALIVE_HOSTS[@]}" -eq 0 ]; then
    echo -e "${YELLOW}Hech qanday tirik host topilmadi.${NC}"
    rm -rf "$TMP_DIR"
    echo -e "${CYAN}Sarflangan vaqt:${NC} ${PING_ELAPSED} soniya"
    exit 0
fi

SORTED_HOSTS=($(printf '%s\n' "${ALIVE_HOSTS[@]}" | sort -t . -k4 -n))
for h in "${SORTED_HOSTS[@]}"; do
    echo "$h" >> "$HOSTS_FILE"
done

echo -e "${GREEN}Topildi:${NC} ${#SORTED_HOSTS[@]} ta tirik host (${PING_ELAPSED}s)"
echo ""
echo -e "${CYAN}[2-BOSQICH]${NC} Har bir host uchun portlar avtomatik skanerlanmoqda..."
echo -e "${CYAN}==============================================${NC}"

# ============================================================
#  2-BOSQICH: har bir tirik host uchun portlarni skanerlash
#
#  MUHIM: har bir port tekshiruvi 1 soniyalik QATTIY TIMEOUT
#  bilan cheklanadi. Timeout bo'lmasa, agar port "filtered"
#  (firewall paketni jimgina tashlab yuboradigan) holatda
#  bo'lsa, bash operatsion tizimning standart TCP-timeoutini
#  kutib qoladi - bu holatlarda 10-60+ soniyagacha cho'zilishi
#  mumkin, HAR BIR port uchun alohida. Aynan shu narsa avvalgi
#  versiyani sekin qilgan asosiy sabab edi.
#
#  Bundan tashqari, endi faqat hostlar emas, balki HAR BIR
#  HOST-PORT JUFTLIGI bitta umumiy navbatga qo'yilib, umumiy
#  parallellik darajasi (MAX_PARALLEL) bilan cheklanadi. Bu
#  hostlar ichidagi portlarni ham parallel qiladi va tezlikni
#  yana bir necha barobar oshiradi.
# ============================================================

CONNECT_TIMEOUT=1      # bitta portni tekshirish uchun maksimal vaqt (soniya)
MAX_PARALLEL=200        # bir vaqtda ishlaydigan umumiy jarayonlar soni

check_port() {
    local host="$1"
    local port="$2"
    local out_file="$3"
    if timeout "$CONNECT_TIMEOUT" bash -c "exec 3<>/dev/tcp/${host}/${port}" 2>/dev/null; then
        echo "$port" >> "$out_file"
    fi
}

# Har bir host uchun natija faylini oldindan tayyorlab qo'yamiz
# (host nomi nuqtali bo'lgani uchun fayl nomida "_" ga almashtiramiz)
declare -A HOST_RESULT_FILE
for host in "${SORTED_HOSTS[@]}"; do
    SAFE_NAME="${host//./_}"
    RESULT_FILE="$TMP_DIR/portscan_${SAFE_NAME}.result"
    : > "$RESULT_FILE"
    HOST_RESULT_FILE["$host"]="$RESULT_FILE"
done

JOB_COUNT=0
TOTAL_CHECKS=$(( ${#SORTED_HOSTS[@]} * ${#PORTS_TO_SCAN[@]} ))
echo -e "${CYAN}Jami tekshiriladigan (host x port) juftliklari:${NC} $TOTAL_CHECKS"

for host in "${SORTED_HOSTS[@]}"; do
    RESULT_FILE="${HOST_RESULT_FILE[$host]}"
    for port in "${PORTS_TO_SCAN[@]}"; do
        check_port "$host" "$port" "$RESULT_FILE" &
        JOB_COUNT=$((JOB_COUNT + 1))

        if (( JOB_COUNT % MAX_PARALLEL == 0 )); then
            wait
        fi
    done
done
wait

TOTAL_END_TIME=$(date +%s)
TOTAL_ELAPSED=$((TOTAL_END_TIME - START_TIME))
PORTSCAN_ELAPSED=$((TOTAL_END_TIME - PING_END_TIME))

# ---------- Natijalarni yig'ish va chiqarish ----------
{
    echo "=============================================="
    echo " PORT SKANERLASH HISOBOTI"
    echo " Sana: $(date '+%Y-%m-%d %H:%M:%S')"
    echo " Tarmoq: ${PREFIX}.0/24"
    echo "=============================================="
} >> "$PORTS_FILE"

TOTAL_OPEN_PORTS=0
for host in "${SORTED_HOSTS[@]}"; do
    RESULT_FILE="${HOST_RESULT_FILE[$host]}"

    if [ -s "$RESULT_FILE" ]; then
        # Portlarni sonli tartibda saralab, bitta qatorga chiqaramiz
        OPEN_PORTS=$(sort -n "$RESULT_FILE" | tr '\n' ' ' | sed 's/ $//')
        PORT_COUNT=$(wc -l < "$RESULT_FILE")
        TOTAL_OPEN_PORTS=$((TOTAL_OPEN_PORTS + PORT_COUNT))
        echo -e "  ${GREEN}[TIRIK]${NC} $host  ${CYAN}->${NC}  ${GREEN}ochiq portlar:${NC} $OPEN_PORTS"
        echo "$host -> ochiq portlar: $OPEN_PORTS" >> "$PORTS_FILE"
    else
        echo -e "  ${YELLOW}[TIRIK]${NC} $host  ${CYAN}->${NC}  ochiq port topilmadi"
        echo "$host -> ochiq port topilmadi" >> "$PORTS_FILE"
    fi
done

rm -rf "$TMP_DIR"

echo -e "${CYAN}==============================================${NC}"
echo -e "${CYAN}Jami tirik hostlar:${NC} ${#SORTED_HOSTS[@]}"
echo -e "${CYAN}Jami topilgan ochiq portlar:${NC} $TOTAL_OPEN_PORTS"
echo -e "${CYAN}Ping bosqichi vaqti:${NC} ${PING_ELAPSED} soniya"
echo -e "${CYAN}Port skan bosqichi vaqti:${NC} ${PORTSCAN_ELAPSED} soniya"
echo -e "${CYAN}Umumiy sarflangan vaqt:${NC} ${TOTAL_ELAPSED} soniya"
echo -e "${CYAN}Hostlar ro'yxati:${NC} $HOSTS_FILE"
echo -e "${CYAN}Port natijalari:${NC} $PORTS_FILE"
echo -e "${CYAN}==============================================${NC}"
