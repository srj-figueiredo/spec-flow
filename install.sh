#!/usr/bin/env bash
# Instala a skill spec-flow.
#   ./install.sh --projeto [PASTA]   só neste projeto (PASTA/.claude/skills/spec-flow). Faça commit para valer também em sessões na nuvem.
#   ./install.sh --global            em todos os projetos desta máquina (~/.claude/skills/spec-flow)
# Também funciona sem clonar:  curl -fsSL https://raw.githubusercontent.com/srj-figueiredo/spec-flow/main/install.sh | bash -s -- --projeto
set -euo pipefail

REPO="https://github.com/srj-figueiredo/spec-flow"
REL="plugins/spec-flow/skills/spec-flow"
modo=""; alvo_proj="."

while [ $# -gt 0 ]; do
  case "$1" in
    --projeto) modo="projeto"; if [ $# -gt 1 ] && [[ "$2" != --* ]]; then alvo_proj="$2"; shift; fi ;;
    --global)  modo="global" ;;
    -h|--help) sed -n '2,6p' "$0" 2>/dev/null || true; exit 0 ;;
    *) echo "Opção desconhecida: $1" >&2; exit 1 ;;
  esac
  shift
done
[ -n "$modo" ] || { echo "Use --projeto [PASTA] ou --global" >&2; exit 1; }
command -v python3 >/dev/null || { echo "A skill precisa de python3 instalado." >&2; exit 1; }

# origem: esta cópia do repositório, ou um clone temporário
aqui="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" 2>/dev/null && pwd || true)"
tmp=""
if [ -n "$aqui" ] && [ -d "$aqui/$REL" ]; then
  origem="$aqui/$REL"
else
  command -v git >/dev/null || { echo "Preciso do git para baixar a skill." >&2; exit 1; }
  tmp="$(mktemp -d)"; trap '[ -z "$tmp" ] || rm -rf "$tmp"' EXIT
  git clone --depth 1 --quiet "$REPO" "$tmp/repo"
  origem="$tmp/repo/$REL"
fi

if [ "$modo" = "global" ]; then
  destino="$HOME/.claude/skills/spec-flow"
else
  [ -d "$alvo_proj" ] || { echo "Pasta não existe: $alvo_proj" >&2; exit 1; }
  destino="$(cd "$alvo_proj" && pwd)/.claude/skills/spec-flow"
fi

mkdir -p "$(dirname "$destino")"
rm -rf "$destino"
cp -R "$origem" "$destino"
find "$destino" -name '__pycache__' -type d -prune -exec rm -rf {} + 2>/dev/null || true

echo "spec-flow instalada em: $destino"
if [ "$modo" = "projeto" ]; then
  echo "Faça commit de .claude/skills/spec-flow para ela existir também nas sessões na nuvem."
else
  echo "Vale para todos os projetos desta máquina. Sessões na nuvem NÃO enxergam ~/.claude: use --projeto nelas."
fi
echo "Para começar, abra o Claude Code no projeto e diga: \"quero começar um projeto com a spec-flow\"."
