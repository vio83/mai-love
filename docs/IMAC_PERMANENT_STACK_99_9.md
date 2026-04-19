# iMac Arch Linux — Permanent Stack 99.9

## Installed components

- Local-only runtime enforcement via `VIO_NO_HYBRID=true`
- Persistent user service `vio83-imac-stack.service`
- Persistent user service `vio83-imac-sync.service`
- Certification timer `vio83-imac-certify.timer`
- Local runtime certification report in `data/config/imac-runtime-cert-latest.json`

## What it guarantees

- Self-healing startup for Ollama, backend, frontend, and runtime supervisor
- Continuous user-level systemd restart policy
- Safe sync scaffolding over Tailscale + SSH for Mac Air to iMac mirroring
- Local-only policy certification using the project’s own runtime checks

## Install / reinstall

Run from the repository root:

bash scripts/runtime/install_imac_permanent_stack.sh

## Verify

bash scripts/runtime/certify_imac_runtime_99_9.sh

## User services

- `systemctl --user status vio83-imac-stack.service`
- `systemctl --user status vio83-imac-sync.service`
- `systemctl --user status vio83-imac-certify.timer`

## Sync note

The sync daemon is legitimate and safe: it does not bypass authentication. It uses Tailscale + SSH only when the peer is reachable and authorized.
