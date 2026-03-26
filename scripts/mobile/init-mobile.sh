#!/usr/bin/env bash
# ============================================================
# VIO 83 AI ORCHESTRA — Mobile Init Script (Tauri 2.0)
# Inizializza i target iOS e Android per build mobile
# Requisiti: Xcode (iOS), Android Studio + NDK (Android)
# ============================================================
set -euo pipefail

cd "$(dirname "$0")/../.."
PROJECT_ROOT="$(pwd)"

echo "╔══════════════════════════════════════════════════════════╗"
echo "║  VIO 83 AI ORCHESTRA — Mobile Init (Tauri 2.0)        ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# ─── Prerequisiti ───
echo "━━━ Checking Prerequisites ━━━"

check_cmd() {
  if command -v "$1" &>/dev/null; then
    echo "  ✅ $1: $(command -v "$1")"
    return 0
  else
    echo "  ❌ $1: NOT FOUND"
    return 1
  fi
}

MISSING=0

check_cmd rustc || MISSING=$((MISSING+1))
check_cmd cargo || MISSING=$((MISSING+1))
check_cmd node || MISSING=$((MISSING+1))
check_cmd npm || MISSING=$((MISSING+1))

# Tauri CLI
if npx tauri --version &>/dev/null 2>&1; then
  echo "  ✅ tauri-cli: $(npx tauri --version 2>/dev/null)"
else
  echo "  ❌ tauri-cli: NOT FOUND — installing..."
  npm install -D @tauri-apps/cli@latest
fi

echo ""

# ─── iOS Setup ───
echo "━━━ iOS Setup ━━━"
if [[ "$(uname)" == "Darwin" ]]; then
  if xcode-select -p &>/dev/null; then
    echo "  ✅ Xcode Command Line Tools installed"
  else
    echo "  ❌ Xcode Command Line Tools missing"
    echo "     Run: xcode-select --install"
    MISSING=$((MISSING+1))
  fi

  # Check iOS Rust targets
  if rustup target list --installed | grep -q "aarch64-apple-ios"; then
    echo "  ✅ Rust target: aarch64-apple-ios"
  else
    echo "  📦 Installing aarch64-apple-ios target..."
    rustup target add aarch64-apple-ios
  fi

  if rustup target list --installed | grep -q "aarch64-apple-ios-sim"; then
    echo "  ✅ Rust target: aarch64-apple-ios-sim"
  else
    echo "  📦 Installing aarch64-apple-ios-sim target..."
    rustup target add aarch64-apple-ios-sim
  fi

  # Initialize Tauri iOS
  if [ -d "src-tauri/gen/apple" ]; then
    echo "  ✅ iOS project already initialized"
  else
    echo "  📦 Initializing Tauri iOS project..."
    npx tauri ios init
    echo "  ✅ iOS project initialized at src-tauri/gen/apple/"
  fi
else
  echo "  ⏭  iOS: skipped (requires macOS)"
fi

echo ""

# ─── Android Setup ───
echo "━━━ Android Setup ━━━"

# Check ANDROID_HOME
if [ -n "${ANDROID_HOME:-}" ] && [ -d "$ANDROID_HOME" ]; then
  echo "  ✅ ANDROID_HOME: $ANDROID_HOME"
elif [ -d "$HOME/Library/Android/sdk" ]; then
  export ANDROID_HOME="$HOME/Library/Android/sdk"
  echo "  ✅ ANDROID_HOME (auto-detected): $ANDROID_HOME"
  echo ""
  echo "  ⚠️  Add to ~/.zshrc:"
  echo "     export ANDROID_HOME=\"\$HOME/Library/Android/sdk\""
  echo "     export PATH=\"\$ANDROID_HOME/cmdline-tools/latest/bin:\$ANDROID_HOME/platform-tools:\$PATH\""
else
  echo "  ❌ ANDROID_HOME not set"
  echo "     Install Android Studio: https://developer.android.com/studio"
  echo "     Then: export ANDROID_HOME=\"\$HOME/Library/Android/sdk\""
  MISSING=$((MISSING+1))
fi

# Check NDK
if [ -n "${NDK_HOME:-}" ] && [ -d "$NDK_HOME" ]; then
  echo "  ✅ NDK_HOME: $NDK_HOME"
elif [ -n "${ANDROID_HOME:-}" ]; then
  NDK_DIR=$(find "$ANDROID_HOME/ndk" -maxdepth 1 -mindepth 1 -type d 2>/dev/null | sort -V | tail -1 || true)
  if [ -n "$NDK_DIR" ]; then
    export NDK_HOME="$NDK_DIR"
    echo "  ✅ NDK_HOME (auto-detected): $NDK_HOME"
  else
    echo "  ❌ Android NDK not found"
    echo "     Install via Android Studio SDK Manager"
    MISSING=$((MISSING+1))
  fi
fi

# Android Rust targets
for target in aarch64-linux-android armv7-linux-androideabi i686-linux-android x86_64-linux-android; do
  if rustup target list --installed | grep -q "$target"; then
    echo "  ✅ Rust target: $target"
  else
    echo "  📦 Installing $target..."
    rustup target add "$target"
  fi
done

# Initialize Tauri Android
if [ -d "src-tauri/gen/android" ]; then
  echo "  ✅ Android project already initialized"
else
  if [ -n "${ANDROID_HOME:-}" ]; then
    echo "  📦 Initializing Tauri Android project..."
    npx tauri android init
    echo "  ✅ Android project initialized at src-tauri/gen/android/"
  else
    echo "  ⏭  Android init: skipped (ANDROID_HOME not set)"
  fi
fi

echo ""

# ─── Summary ───
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [ "$MISSING" -eq 0 ]; then
  echo "✅ ALL PREREQUISITES MET — Mobile targets ready!"
  echo ""
  echo "Available commands:"
  echo "  npx tauri ios dev          # Run on iOS Simulator"
  echo "  npx tauri android dev      # Run on Android Emulator"
  echo "  npx tauri ios build        # Build iOS .ipa"
  echo "  npx tauri android build    # Build Android .apk/.aab"
else
  echo "⚠️  $MISSING prerequisite(s) missing — fix above issues first"
fi
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
