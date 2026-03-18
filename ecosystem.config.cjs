// PM2 Ecosystem Config — VIO 83 AI Orchestra
// Usage:
//   pm2 start ecosystem.config.cjs          # avvia tutti i processi
//   pm2 stop all                             # ferma tutto
//   pm2 restart all                          # riavvia tutto
//   pm2 logs                                 # log aggregati
//   pm2 monit                                # dashboard interattiva
//   pm2 save && pm2 startup                  # autostart al boot macOS

'use strict';

module.exports = {
  apps: [
    // ─── FastAPI Backend ───────────────────────────────────────────────────
    {
      name: 'vio83-backend',
      script: 'uvicorn',
      args: 'backend.server:app --host 127.0.0.1 --port 4000 --workers 2 --loop asyncio',
      interpreter: 'python3',
      cwd: '/Users/padronavio/Projects/vio83-ai-orchestra',
      watch: false,
      autorestart: true,
      max_restarts: 10,
      restart_delay: 3000,
      min_uptime: '5s',
      env: {
        NODE_ENV: 'production',
        PYTHONUNBUFFERED: '1',
        VIO_ENV: 'production',
        VIO_CACHE_ENABLED: 'true',
        VIO_LOG_LEVEL: 'INFO',
      },
      env_development: {
        NODE_ENV: 'development',
        VIO_ENV: 'development',
        VIO_LOG_LEVEL: 'DEBUG',
      },
      log_date_format: 'YYYY-MM-DD HH:mm:ss',
      error_file: './logs/backend-error.log',
      out_file: './logs/backend-out.log',
      merge_logs: true,
      time: true,
    },

    // ─── DB Maintenance (cron giornaliero) ────────────────────────────────
    {
      name: 'vio83-db-maintenance',
      script: './scripts/db-maintenance.sh',
      interpreter: 'bash',
      cwd: '/Users/padronavio/Projects/vio83-ai-orchestra',
      cron_restart: '0 3 * * *', // ogni notte alle 03:00
      autorestart: false,
      watch: false,
      env: {
        VIO_ENV: 'production',
      },
      log_date_format: 'YYYY-MM-DD HH:mm:ss',
      error_file: './logs/db-maintenance-error.log',
      out_file: './logs/db-maintenance-out.log',
      merge_logs: true,
      time: true,
    },
  ],

  // ─── Deploy config (opzionale — per deploy remoto via SSH) ──────────────
  deploy: {
    production: {
      user: 'padronavio',
      host: 'localhost',
      ref: 'origin/main',
      repo: 'https://github.com/vio83/vio83-ai-orchestra.git',
      path: '/Users/padronavio/Projects/vio83-ai-orchestra',
      'post-deploy': 'pip3 install -r requirements.txt && pm2 reload ecosystem.config.cjs --env production',
    },
  },
};
