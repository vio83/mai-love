use std::env;

const DEFAULT_UPDATER_PUBKEY: &str =
  "dW50cnVzdGVkIGNvbW1lbnQ6IG1pbmlzaWduIHB1YmxpYyBrZXkgVklPODMKUlVaUExBQ0VIT0xERVIK";

fn env_bool(key: &str, default: bool) -> bool {
  match env::var(key) {
    Ok(value) => matches!(value.trim().to_lowercase().as_str(), "1" | "true" | "yes" | "on"),
    Err(_) => default,
  }
}

fn updater_pubkey() -> Option<String> {
  let candidates = ["VIO_TAURI_UPDATER_PUBKEY", "TAURI_UPDATER_PUBKEY"];

  for key in candidates {
    if let Ok(value) = env::var(key) {
      let trimmed = value.trim().to_string();
      if !trimmed.is_empty() {
        return Some(trimmed);
      }
    }
  }

  Some(DEFAULT_UPDATER_PUBKEY.to_string())
}

fn updater_endpoints() -> Vec<String> {
  let configured = env::var("VIO_TAURI_UPDATER_ENDPOINTS")
    .unwrap_or_else(|_| "https://github.com/vio83/vio83-ai-orchestra/releases/latest/download/latest.json".to_string());

  configured
    .split(',')
    .map(str::trim)
    .filter(|item| !item.is_empty())
    .map(ToOwned::to_owned)
    .collect()
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
  let mut builder = tauri::Builder::default().setup(|app| {
    if cfg!(debug_assertions) {
      app.handle().plugin(
        tauri_plugin_log::Builder::default()
          .level(log::LevelFilter::Info)
          .build(),
      )?;
    }
    Ok(())
  });

  // Plugin: process (relaunch) — necessario per auto-updater restart
  builder = builder.plugin(tauri_plugin_process::init());

  // Plugin: shell (open URLs in default browser)
  builder = builder.plugin(tauri_plugin_shell::init());

  if env_bool("VIO_TAURI_UPDATER_ENABLED", true) {
    if let Some(pubkey) = updater_pubkey() {
      let endpoints = updater_endpoints();
      let mut updater_builder = tauri_plugin_updater::Builder::new().pubkey(pubkey);

      if !endpoints.is_empty() {
        updater_builder = updater_builder.endpoints(endpoints);
      }

      builder = builder.plugin(updater_builder.build());
    } else {
      eprintln!(
        "[VIO updater] disattivato: manca VIO_TAURI_UPDATER_PUBKEY / TAURI_UPDATER_PUBKEY"
      );
    }
  }

  builder
    .run(tauri::generate_context!())
    .expect("error while running tauri application");
}
