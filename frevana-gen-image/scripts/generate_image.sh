#!/usr/bin/env bash

set -euo pipefail

API_URL="https://api-report.frevana.com/report/generate-image"
CONNECT_TIMEOUT="10"
MAX_TIME="600"

json_escape() {
  local s="$1"
  s=${s//\\/\\\\}
  s=${s//\"/\\\"}
  s=${s//$'\n'/\\n}
  s=${s//$'\r'/\\r}
  s=${s//$'\t'/\\t}
  s=${s//$'\f'/\\f}
  s=${s//$'\b'/\\b}
  printf '%s' "$s"
}

usage() {
  cat <<'EOF'
Usage:
  generate_image.sh --prompt "image prompt" --provider <openai|gemini> --model <model> [--quality <quality>] [--size <size>] [--output /path/to/result.json] [--token "bearer token"]

Options:
  --prompt         Image generation prompt to send
  --provider       Image generation provider: openai or gemini
  --model          Image generation model
  --quality        Optional quality value
  --size           Optional size value
  --output         Optional file path for saving returned JSON
  --token          Optional Bearer token override for this run
  -h, --help       Show this help message
EOF
}

is_allowed_value() {
  local value="$1"
  shift
  local allowed
  for allowed in "$@"; do
    if [[ "$value" == "$allowed" ]]; then
      return 0
    fi
  done
  return 1
}

PROMPT=""
PROVIDER=""
MODEL=""
QUALITY=""
SIZE=""
OUTPUT_PATH=""
TOKEN_OVERRIDE=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --prompt)
      PROMPT="${2:-}"
      shift 2
      ;;
    --provider)
      PROVIDER="${2:-}"
      shift 2
      ;;
    --model)
      MODEL="${2:-}"
      shift 2
      ;;
    --quality)
      QUALITY="${2:-}"
      shift 2
      ;;
    --size)
      SIZE="${2:-}"
      shift 2
      ;;
    --output)
      OUTPUT_PATH="${2:-}"
      shift 2
      ;;
    --token)
      TOKEN_OVERRIDE="${2:-}"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

if [[ -z "$PROMPT" ]]; then
  echo "Missing required argument: --prompt" >&2
  exit 1
fi

if [[ -z "$PROVIDER" ]]; then
  echo "Missing required argument: --provider" >&2
  exit 1
fi

if [[ -z "$MODEL" ]]; then
  echo "Missing required argument: --model" >&2
  exit 1
fi

if ! is_allowed_value "$PROVIDER" "openai" "gemini"; then
  echo "Invalid provider: $PROVIDER" >&2
  echo "Allowed providers: openai, gemini" >&2
  exit 1
fi

OPENAI_MODELS=("gpt-image-1.5" "gpt-image-2")
GEMINI_MODELS=("gemini-3-pro-image-preview" "gemini-3.1-flash-image-preview")
ALLOWED_QUALITIES=("standard" "hd" "low" "medium" "high" "auto")
ALLOWED_SIZES=("auto" "1024x1024" "1536x1024" "1024x1536" "256x256" "512x512" "1792x1024" "1024x1792")

if [[ "$PROVIDER" == "openai" ]]; then
  if ! is_allowed_value "$MODEL" "${OPENAI_MODELS[@]}"; then
    echo "Invalid model for provider openai: $MODEL" >&2
    echo "Allowed models: ${OPENAI_MODELS[*]}" >&2
    exit 1
  fi
else
  if ! is_allowed_value "$MODEL" "${GEMINI_MODELS[@]}"; then
    echo "Invalid model for provider gemini: $MODEL" >&2
    echo "Allowed models: ${GEMINI_MODELS[*]}" >&2
    exit 1
  fi
fi

if [[ -n "$QUALITY" ]] && ! is_allowed_value "$QUALITY" "${ALLOWED_QUALITIES[@]}"; then
  echo "Invalid quality: $QUALITY" >&2
  echo "Allowed qualities: ${ALLOWED_QUALITIES[*]}" >&2
  exit 1
fi

if [[ -n "$SIZE" ]] && ! is_allowed_value "$SIZE" "${ALLOWED_SIZES[@]}"; then
  echo "Invalid size: $SIZE" >&2
  echo "Allowed sizes: ${ALLOWED_SIZES[*]}" >&2
  exit 1
fi

if ! command -v curl >/dev/null 2>&1; then
  echo "curl is required but was not found in PATH." >&2
  exit 1
fi

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 is required but was not found in PATH." >&2
  exit 1
fi

TOKEN="${TOKEN_OVERRIDE:-${FREVANA_TOKEN:-}}"
if [[ -z "$TOKEN" ]]; then
  if [[ -t 0 ]]; then
    read -r -s -p "FREVANA_TOKEN not found. Please enter your Frevana Bearer token: " TOKEN
    echo >&2
  else
    echo "FREVANA_TOKEN is not set. In non-interactive runs, set FREVANA_TOKEN or pass --token explicitly." >&2
    exit 1
  fi
fi

if [[ -z "$TOKEN" ]]; then
  echo "Bearer token is required." >&2
  exit 1
fi

PAYLOAD_FILE="$(mktemp)"
RESPONSE_FILE="$(mktemp)"
RESULT_FILE="$(mktemp)"
cleanup() {
  rm -f "$PAYLOAD_FILE" "$RESPONSE_FILE" "$RESULT_FILE"
}
trap cleanup EXIT

printf '{"prompt":"%s","provider":"%s","model":"%s"' \
  "$(json_escape "$PROMPT")" \
  "$(json_escape "$PROVIDER")" \
  "$(json_escape "$MODEL")" \
  > "$PAYLOAD_FILE"

if [[ -n "$QUALITY" ]]; then
  printf ',"quality":"%s"' "$(json_escape "$QUALITY")" >> "$PAYLOAD_FILE"
fi

if [[ -n "$SIZE" ]]; then
  printf ',"size":"%s"' "$(json_escape "$SIZE")" >> "$PAYLOAD_FILE"
fi

printf '}' >> "$PAYLOAD_FILE"

HTTP_CODE="$(
  curl -sS \
    --connect-timeout "$CONNECT_TIMEOUT" \
    --max-time "$MAX_TIME" \
    -o "$RESPONSE_FILE" \
    -w "%{http_code}" \
    -X POST "$API_URL" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $TOKEN" \
    --data @"$PAYLOAD_FILE"
)"

if [[ "$HTTP_CODE" -lt 200 || "$HTTP_CODE" -ge 300 ]]; then
  echo "Frevana API request failed with HTTP $HTTP_CODE" >&2
  cat "$RESPONSE_FILE" >&2
  exit 1
fi

if [[ ! -s "$RESPONSE_FILE" ]]; then
  echo "Frevana API returned an empty response body." >&2
  exit 1
fi

python3 - "$RESPONSE_FILE" "$RESULT_FILE" <<'PY'
import json
import sys
from pathlib import Path

response_path = Path(sys.argv[1])
result_path = Path(sys.argv[2])
raw = response_path.read_text(encoding="utf-8")

try:
    payload = json.loads(raw)
except json.JSONDecodeError as exc:
    print(f"Frevana API returned non-JSON response: {exc}", file=sys.stderr)
    print(raw, file=sys.stderr)
    sys.exit(1)

if not isinstance(payload, dict):
    print("Frevana API returned JSON, but not an object.", file=sys.stderr)
    print(raw, file=sys.stderr)
    sys.exit(1)

required_fields = ("image_url", "provider", "model", "credits_consumed")
for field in required_fields:
    if field not in payload:
        print(f"Frevana API response JSON is missing the '{field}' field.", file=sys.stderr)
        print(raw, file=sys.stderr)
        sys.exit(1)

image_url = payload["image_url"]
provider = payload["provider"]
model = payload["model"]
credits_consumed = payload["credits_consumed"]

if not isinstance(image_url, str) or not image_url:
    print("Frevana API response field 'image_url' must be a non-empty string.", file=sys.stderr)
    print(raw, file=sys.stderr)
    sys.exit(1)

if not isinstance(provider, str) or not provider:
    print("Frevana API response field 'provider' must be a non-empty string.", file=sys.stderr)
    print(raw, file=sys.stderr)
    sys.exit(1)

if not isinstance(model, str) or not model:
    print("Frevana API response field 'model' must be a non-empty string.", file=sys.stderr)
    print(raw, file=sys.stderr)
    sys.exit(1)

if not isinstance(credits_consumed, (int, float)):
    print("Frevana API response field 'credits_consumed' must be numeric.", file=sys.stderr)
    print(raw, file=sys.stderr)
    sys.exit(1)

normalized = {
    "image_url": image_url,
    "provider": provider,
    "model": model,
    "credits_consumed": credits_consumed,
}
result_path.write_text(json.dumps(normalized, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
PY

if [[ -n "$OUTPUT_PATH" ]]; then
  mkdir -p "$(dirname "$OUTPUT_PATH")"
  cp "$RESULT_FILE" "$OUTPUT_PATH"
fi

cat "$RESULT_FILE"
