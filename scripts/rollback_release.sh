#!/usr/bin/env bash
set -euo pipefail

DRY_RUN="false"
IMAGE=""
TAG=""
ROLLED_BACK_IMAGE=""

usage() {
  cat <<EOF
Kullanim:
  ./scripts/rollback_release.sh --image <image-repo> --tag <stable-tag> [--dry-run]

Ornek:
  ./scripts/rollback_release.sh --image ghcr.io/org/repo --tag v1.2.3 --dry-run
EOF
}

log() {
  echo "[rollback] $*"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --image)
      IMAGE="$2"
      shift 2
      ;;
    --tag)
      TAG="$2"
      shift 2
      ;;
    --dry-run)
      DRY_RUN="true"
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      log "HATA: Bilinmeyen arguman: $1"
      usage
      exit 1
      ;;
  esac
done

if [[ -z "${IMAGE}" || -z "${TAG}" ]]; then
  log "HATA: --image ve --tag zorunlu."
  usage
  exit 1
fi

ROLLED_BACK_IMAGE="${IMAGE}:${TAG}"
log "Hedef rollback image: ${ROLLED_BACK_IMAGE}"
log "Dry-run: ${DRY_RUN}"

DEPLOY_CMD_TEMPLATE="${ROLLBACK_COMMAND:-}"

if [[ -z "${DEPLOY_CMD_TEMPLATE}" ]]; then
  DEPLOY_CMD_TEMPLATE='echo "TODO: set ROLLBACK_COMMAND secret. Example: kubectl set image deployment/app app=${IMAGE} -n prod"'
fi

CMD="${DEPLOY_CMD_TEMPLATE//\$\{IMAGE\}/${ROLLED_BACK_IMAGE}}"
CMD="${CMD//\{image\}/${ROLLED_BACK_IMAGE}}"

if [[ "${DRY_RUN}" == "true" ]]; then
  log "DRY-RUN komut:"
  echo "${CMD}"
  log "DRY-RUN tamamlandi."
  exit 0
fi

log "Rollback komutu calistiriliyor..."
set +e
bash -c "${CMD}"
exit_code=$?
set -e

if [[ ${exit_code} -ne 0 ]]; then
  log "HATA: Rollback basarisiz (exit=${exit_code})."
  exit "${exit_code}"
fi

log "Rollback basarili: ${ROLLED_BACK_IMAGE}"
