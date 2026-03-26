#!/usr/bin/env bash
set -euo pipefail

MAX_SECONDS="${CANARY_MAX_RESPONSE_SECONDS:-2.5}"
LOGIN_URL="${CANARY_LOGIN_URL:-http://127.0.0.1:8000/accounts/login/}"
ENROLLMENT_URL="${CANARY_ENROLLMENT_URL:-http://127.0.0.1:8000/enrollments/}"

echo "[canary] Basladi"
echo "[canary] Login URL: ${LOGIN_URL}"
echo "[canary] Enrollment URL: ${ENROLLMENT_URL}"
echo "[canary] Max response seconds: ${MAX_SECONDS}"

check_endpoint() {
  local name="$1"
  local url="$2"
  local tmp_file
  tmp_file="$(mktemp)"

  local result
  result="$(curl -sS -o "${tmp_file}" -w "%{http_code} %{time_total}" --max-time 15 "${url}")"
  local status
  status="$(echo "${result}" | awk '{print $1}')"
  local duration
  duration="$(echo "${result}" | awk '{print $2}')"

  echo "[canary] ${name} status=${status} duration=${duration}s"

  if [[ "${status}" -ge 500 || "${status}" -lt 200 ]]; then
    echo "[canary] HATA: ${name} endpoint hata dondu (status=${status})"
    rm -f "${tmp_file}"
    return 1
  fi

  awk -v d="${duration}" -v m="${MAX_SECONDS}" 'BEGIN { exit (d <= m) ? 0 : 1 }' || {
    echo "[canary] HATA: ${name} response time asimi (${duration}s > ${MAX_SECONDS}s)"
    rm -f "${tmp_file}"
    return 1
  }

  rm -f "${tmp_file}"
  return 0
}

check_endpoint "login" "${LOGIN_URL}"
check_endpoint "enrollment" "${ENROLLMENT_URL}"

echo "[canary] BASARILI"
