#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::process::Command;

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

fn main() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .invoke_handler(tauri::generate_handler![exec_apm])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
