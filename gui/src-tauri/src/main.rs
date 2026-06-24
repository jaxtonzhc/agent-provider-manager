#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::process::Command;
use tauri::{
    Manager,
    menu::{Menu, MenuItem},
    tray::{MouseButton, MouseButtonState, TrayIconBuilder, TrayIconEvent},
};

#[derive(serde::Serialize)]
struct ApmResult {
    stdout: String,
    stderr: String,
    code: i32,
}

#[tauri::command]
fn exec_apm(args: Vec<String>) -> ApmResult {
    if args.first().map(|s| s.as_str()) == Some("--open-file") {
        if let Some(path) = args.get(1) {
            let _ = Command::new("code").arg(path).spawn()
                .or_else(|_| Command::new("open").arg(path).spawn());
        }
        return ApmResult { stdout: String::new(), stderr: String::new(), code: 0 };
    }

    let result = Command::new("apm")
        .args(&args)
        .env("APM_NO_COLOR", "1")
        .output();

    match result {
        Ok(output) => ApmResult {
            stdout: String::from_utf8_lossy(&output.stdout).into_owned(),
            stderr: String::from_utf8_lossy(&output.stderr).into_owned(),
            code: output.status.code().unwrap_or(1),
        },
        Err(e) => ApmResult {
            stdout: String::new(),
            stderr: format!("Failed to execute apm: {}", e),
            code: 1,
        },
    }
}

fn get_providers() -> Vec<String> {
    let output = Command::new("apm")
        .args(["--json", "provider", "list"])
        .env("APM_NO_COLOR", "1")
        .output();
    match output {
        Ok(o) => {
            let stdout = String::from_utf8_lossy(&o.stdout);
            serde_json::from_str::<Vec<serde_json::Value>>(&stdout)
                .unwrap_or_default()
                .iter()
                .filter_map(|p| p.get("slug").and_then(|s| s.as_str()).map(String::from))
                .collect()
        }
        Err(_) => vec![],
    }
}

fn main() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .invoke_handler(tauri::generate_handler![exec_apm])
        .setup(|app| {
            let providers = get_providers();

            let quit = MenuItem::with_id(app, "quit", "Quit APM", true, None::<&str>)?;
            let show = MenuItem::with_id(app, "show", "Show Window", true, None::<&str>)?;

            let menu = Menu::with_id(app, "tray_menu")?;
            for p in &providers {
                let item = MenuItem::with_id(app, format!("switch_{}", p), format!("Switch All → {}", p), true, None::<&str>)?;
                menu.append(&item)?;
            }
            menu.append(&tauri::menu::PredefinedMenuItem::separator(app)?)?;
            menu.append(&show)?;
            menu.append(&quit)?;

            let _tray = TrayIconBuilder::new()
                .icon(app.default_window_icon().unwrap().clone())
                .menu(&menu)
                .on_menu_event(move |app, event| {
                    let id = event.id().as_ref();
                    if id == "quit" {
                        app.exit(0);
                    } else if id == "show" {
                        if let Some(w) = app.get_webview_window("main") {
                            let _ = w.show();
                            let _ = w.set_focus();
                        }
                    } else if let Some(provider) = id.strip_prefix("switch_") {
                        let _ = Command::new("apm")
                            .args(["switch", provider])
                            .env("APM_NO_COLOR", "1")
                            .spawn();
                    }
                })
                .on_tray_icon_event(|tray, event| {
                    if let TrayIconEvent::Click { button: MouseButton::Left, button_state: MouseButtonState::Up, .. } = event {
                        let app = tray.app_handle();
                        if let Some(w) = app.get_webview_window("main") {
                            let _ = w.show();
                            let _ = w.set_focus();
                        }
                    }
                })
                .build(app)?;

            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
