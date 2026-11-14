/**
 * DocuIntellect - Unified Dev Server Runner
 * Concurrently launches both FastAPI Backend and Vite Frontend in a single command:
 *   npm run dev
 */

import { spawn, execSync } from "child_process";
import path from "path";
import fs from "fs";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Root directories
const ROOT_DIR = path.resolve(__dirname, "..");
const BACKEND_DIR = path.join(ROOT_DIR, "backend");
const FRONTEND_DIR = path.join(ROOT_DIR, "frontend");

// Terminal ANSI colors
const RESET = "\x1b[0m";
const BOLD = "\x1b[1m";
const CYAN = "\x1b[36m";
const MAGENTA = "\x1b[35m";
const GREEN = "\x1b[32m";
const YELLOW = "\x1b[33m";
const RED = "\x1b[31m";

function logSystem(msg) {
  console.log(`${GREEN}${BOLD}[SYSTEM]${RESET} ${msg}`);
}

// Find Python executable (prefer local virtual environment)
function findPython() {
  const winVenv = path.join(BACKEND_DIR, "venv", "Scripts", "python.exe");
  const nixVenv = path.join(BACKEND_DIR, "venv", "bin", "python");

  if (process.platform === "win32" && fs.existsSync(winVenv)) {
    return winVenv;
  }
  if (fs.existsSync(nixVenv)) {
    return nixVenv;
  }

  // Fallback to global python
  return process.platform === "win32" ? "python" : "python3";
}

// Display startup banner
console.log(`\n${CYAN}${BOLD}======================================================================${RESET}`);
console.log(`${BOLD}  DocuIntellect - AI Document Intelligence System${RESET}`);
console.log(`${CYAN}${BOLD}======================================================================${RESET}`);
console.log(`  ${BOLD}Backend API:${RESET}        ${CYAN}http://127.0.0.1:8000${RESET} (Docs: http://127.0.0.1:8000/docs)`);
console.log(`  ${BOLD}Frontend App:${RESET}       ${MAGENTA}http://127.0.0.1:5173${RESET}`);
console.log(`  ${BOLD}Environment:${RESET}        Development (FastAPI + Vite)`);
console.log(`${CYAN}${BOLD}======================================================================${RESET}`);
console.log(`  ${YELLOW}Press Ctrl+C to terminate all services.${RESET}\n`);

const pythonExe = findPython();
const runScript = path.join(BACKEND_DIR, "run.py");

logSystem(`Using Python interpreter: ${pythonExe}`);
logSystem(`Starting FastAPI backend and Vite frontend...\n`);

// Track child processes
let backendProcess = null;
let frontendProcess = null;
let isShuttingDown = false;

// 1. Spawn FastAPI Backend via run.py
const backendEnv = {
  ...process.env,
  PYTHONPATH: BACKEND_DIR,
  PYTHONUNBUFFERED: "1",
};

backendProcess = spawn(
  pythonExe,
  [runScript],
  {
    cwd: BACKEND_DIR,
    env: backendEnv,
    shell: false,
  }
);

backendProcess.stdout?.on("data", (data) => {
  const lines = data.toString().split(/\r?\n/);
  for (const line of lines) {
    if (line.trim()) {
      console.log(`${CYAN}[BACKEND]${RESET} ${line}`);
    }
  }
});

backendProcess.stderr?.on("data", (data) => {
  const lines = data.toString().split(/\r?\n/);
  for (const line of lines) {
    if (line.trim()) {
      console.log(`${CYAN}[BACKEND]${RESET} ${line}`);
    }
  }
});

backendProcess.on("error", (err) => {
  console.error(`${RED}[BACKEND ERROR]${RESET}`, err.message);
});

backendProcess.on("close", (code) => {
  if (!isShuttingDown) {
    logSystem(`Backend process exited with code ${code}`);
  }
});

// 2. Spawn Vite Frontend
const npmCmd = process.platform === "win32" ? "npm.cmd" : "npm";

frontendProcess = spawn(
  npmCmd,
  ["run", "vite", "--", "--host", "127.0.0.1", "--port", "5173"],
  {
    cwd: FRONTEND_DIR,
    shell: true,
    env: process.env,
  }
);

frontendProcess.stdout?.on("data", (data) => {
  const lines = data.toString().split(/\r?\n/);
  for (const line of lines) {
    if (line.trim()) {
      console.log(`${MAGENTA}[FRONTEND]${RESET} ${line}`);
    }
  }
});

frontendProcess.stderr?.on("data", (data) => {
  const lines = data.toString().split(/\r?\n/);
  for (const line of lines) {
    if (line.trim()) {
      console.log(`${MAGENTA}[FRONTEND]${RESET} ${line}`);
    }
  }
});

frontendProcess.on("error", (err) => {
  console.error(`${RED}[FRONTEND ERROR]${RESET}`, err.message);
});

frontendProcess.on("close", (code) => {
  if (!isShuttingDown) {
    logSystem(`Frontend process exited with code ${code}`);
  }
});

// Graceful cleanup on exit
function shutdown() {
  if (isShuttingDown) return;
  isShuttingDown = true;
  console.log(`\n${YELLOW}${BOLD}[SYSTEM] Shutting down all servers cleanly...${RESET}`);

  if (process.platform === "win32") {
    if (backendProcess?.pid) {
      try {
        execSync(`taskkill /pid ${backendProcess.pid} /T /F`, { stdio: "ignore" });
      } catch (e) {}
    }
    if (frontendProcess?.pid) {
      try {
        execSync(`taskkill /pid ${frontendProcess.pid} /T /F`, { stdio: "ignore" });
      } catch (e) {}
    }
  } else {
    if (backendProcess) backendProcess.kill("SIGTERM");
    if (frontendProcess) frontendProcess.kill("SIGTERM");
  }

  logSystem("All servers stopped.");
  process.exit(0);
}

process.on("SIGINT", shutdown);
process.on("SIGTERM", shutdown);
process.on("exit", shutdown);
