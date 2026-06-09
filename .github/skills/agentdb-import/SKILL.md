# Skill: agentdb-import

Cross-reference `.github/agentdb_memory/memory-export.json` against the local
agentdb and import any episodes/facts/notes that are missing locally.
Use this on a new device after cloning the repo.

**Trigger phrases:** "import agentdb", "restore memory", "import memory", "sync memory from repo", "load memory export"

---

## Prerequisites

- `AGENTDB_PATH` — set in user env and PS profile (see setup below if missing)
- `AGENTDB_FORCE_SQLJS=1` — required for writes to persist
- agentdb v3.0.0-alpha.16+ installed globally (`npm install -g agentdb`)
- `@xenova/transformers` installed globally (`npm install -g @xenova/transformers`)

---

## Step 0 — First-time device setup (if agentdb not yet configured)

```powershell
# Install agentdb globally
npm install -g agentdb
npm install -g @xenova/transformers

# Create the DB directory and initialise
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.agentdb" | Out-Null
$dbPath = "$env:USERPROFILE\.agentdb\github-copilot-memory.db"

# Set permanent env vars
[System.Environment]::SetEnvironmentVariable("AGENTDB_PATH", $dbPath, "User")
[System.Environment]::SetEnvironmentVariable("AGENTDB_FORCE_SQLJS", "1", "User")
$env:AGENTDB_PATH = $dbPath
$env:AGENTDB_FORCE_SQLJS = "1"

# Write PS7 profile
$profileLines = "`$env:AGENTDB_PATH = '$dbPath'`n`$env:AGENTDB_FORCE_SQLJS = '1'"
$profileDir = Split-Path $PROFILE
if (-not (Test-Path $profileDir)) { New-Item -ItemType Directory -Path $profileDir -Force | Out-Null }
Set-Content $PROFILE -Value $profileLines -Encoding UTF8

# Initialise empty DB
agentdb init $dbPath
```

---

## Step 1 — Find the sql.js path on this device

```powershell
$globalRoot = npm root -g
$sqljsDir   = "$globalRoot/agentdb/node_modules/sql.js/dist" -replace '\\','/'
Write-Host "sql.js dir: $sqljsDir"
Test-Path ($sqljsDir -replace '/','\\' | ForEach-Object { "$_\sql-wasm.js" })
```

---

## Step 2 — Run the import script

```powershell
$env:AGENTDB_PATH        = [System.Environment]::GetEnvironmentVariable("AGENTDB_PATH","User")
$env:AGENTDB_FORCE_SQLJS = "1"
$globalRoot  = npm root -g
$sqljsDir    = ($globalRoot + "/agentdb/node_modules/sql.js/dist") -replace '\\','/'
$dbPath      = ($env:AGENTDB_PATH) -replace '\\','/'
$exportFile  = "C:/repos-github/PoE-FanController/.github/agentdb_memory/memory-export.json"

$code = @"
const initSqlJs  = require('$sqljsDir/sql-wasm.js');
const fs         = require('fs');
const { execSync } = require('child_process');

const dbPath    = '$dbPath';
const exportFile = '$exportFile';

const exportData = JSON.parse(fs.readFileSync(exportFile, 'utf8'));
const buf = fs.readFileSync(dbPath);

initSqlJs({ locateFile: f => '$sqljsDir/' + f }).then(SQL => {
  const db = new SQL.Database(buf);

  // Get existing episode IDs
  const existing = new Set();
  const r = db.exec('SELECT id FROM episodes');
  if (r[0]) r[0].values.forEach(v => existing.add(v[0]));
  console.log('Local episodes:', existing.size, '| Export episodes:', exportData.episodes.length);

  // Find missing
  const missing = exportData.episodes.filter(ep => !existing.has(ep.id));
  console.log('Missing episodes to import:', missing.length);

  db.close();

  // Import missing via CLI (so embeddings are recomputed correctly)
  let imported = 0;
  for (const ep of missing) {
    const session  = (ep.session_id || 'imported').replace(/'/g, "");
    const task     = (ep.task       || 'unknown' ).replace(/'/g, "").replace(/\s+/g, '-').substring(0, 50);
    const reward   = ep.reward   ?? 0.9;
    const success  = ep.success  ? 'true' : 'false';
    const critique = (ep.critique || 'imported').replace(/"/g, "'").substring(0, 200);
    const input    = (ep.input    || '').replace(/"/g, "'").substring(0, 500);
    const output   = (ep.output   || '').replace(/"/g, "'").substring(0, 1000);

    try {
      const cmd = 'agentdb reflexion store "' + session + '" "' + task + '" ' + reward + ' ' + success + ' "' + critique + '" "' + input + '" "' + output + '" 0 0';
      const result = execSync(cmd, { env: process.env, encoding: 'utf8', timeout: 30000 });
      if (result.includes('Stored episode')) imported++;
    } catch(e) {
      console.error('Failed to import episode:', ep.id, e.message.substring(0, 80));
    }
  }
  console.log('Imported ' + imported + ' / ' + missing.length + ' missing episodes');
});
"@

$tmp = "$env:TEMP\agentdb_import.js"
[System.IO.File]::WriteAllText($tmp, $code, [System.Text.Encoding]::UTF8)
node $tmp
Remove-Item $tmp
```

---

## Step 3 — Verify

```powershell
$env:AGENTDB_FORCE_SQLJS = "1"
agentdb db stats 2>&1 | Select-String "episodes"
agentdb query --query "PCB board size" --k 3
```

---

## Notes

- Import uses `agentdb reflexion store` so the local model recomputes embeddings (device-specific).
- Episodes already in local DB (matched by `id`) are skipped — safe to run multiple times.
- After import, run the export skill again to capture any new local episodes added since the snapshot.
