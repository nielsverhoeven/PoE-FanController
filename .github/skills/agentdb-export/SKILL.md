# Skill: agentdb-export

Export all episodes (and facts/notes) from the local agentdb to
`.github/agentdb_memory/memory-export.json` so data can be transferred
to another device via git.

**Trigger phrases:** "export agentdb", "backup memory", "export memory", "sync memory to repo"

---

## Prerequisites

- `AGENTDB_PATH` — path to `github-copilot-memory.db` (set in user env + PS profile)
- `AGENTDB_FORCE_SQLJS=1` — required for sql.js backend
- Node.js with sql.js at `C:\nvm4w\nodejs\node_modules\agentdb\node_modules\sql.js`

---

## Step 1 — Run the export script

```powershell
$env:AGENTDB_PATH   = "C:\Users\Niels\.agentdb\github-copilot-memory.db"
$env:AGENTDB_FORCE_SQLJS = "1"

$dbPath   = "C:/Users/Niels/.agentdb/github-copilot-memory.db"
$sqljsDir = "C:/nvm4w/nodejs/node_modules/agentdb/node_modules/sql.js/dist"
$outFile  = "C:/repos-github/PoE-FanController/.github/agentdb_memory/memory-export.json"

$code = @"
const initSqlJs = require('$sqljsDir/sql-wasm.js');
const fs  = require('fs');
const buf = fs.readFileSync('$dbPath');
initSqlJs({ locateFile: f => '$sqljsDir/' + f }).then(SQL => {
  const db = new SQL.Database(buf);
  const query = (sql) => {
    const r = db.exec(sql);
    if (!r[0]) return [];
    const cols = r[0].columns;
    return r[0].values.map(row => { const o = {}; cols.forEach((c,i) => o[c] = row[i]); return o; });
  };
  const out = {
    version: '1.0',
    exported_at: new Date().toISOString(),
    source_db: '$dbPath',
    episodes: query('SELECT id,ts,session_id,task,input,output,critique,reward,success,latency_ms,tokens_used,tags,metadata,created_at FROM episodes ORDER BY created_at ASC'),
    facts:    query('SELECT * FROM facts ORDER BY created_at ASC'),
    notes:    query('SELECT * FROM notes ORDER BY created_at ASC')
  };
  fs.mkdirSync(require('path').dirname('$outFile'), { recursive: true });
  fs.writeFileSync('$outFile', JSON.stringify(out, null, 2), 'utf8');
  console.log('Exported ' + out.episodes.length + ' episodes, ' + out.facts.length + ' facts, ' + out.notes.length + ' notes to $outFile');
});
"@

$tmp = "$env:TEMP\agentdb_export.js"
[System.IO.File]::WriteAllText($tmp, $code, [System.Text.Encoding]::UTF8)
node $tmp
Remove-Item $tmp
```

---

## Step 2 — Commit the export file

```powershell
Set-Location C:\repos-github\PoE-FanController
git add .github/agentdb_memory/memory-export.json
git commit -m "chore: export agentdb memory snapshot

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
git push origin main
```

---

## Step 3 — Verify

```powershell
$export = Get-Content .github/agentdb_memory/memory-export.json | ConvertFrom-Json
Write-Host "Episodes: $($export.episodes.Count)"
Write-Host "Exported at: $($export.exported_at)"
```

---

## Notes

- The export file is committed to `main` so it travels with the repo to other devices.
- The export does **not** include vector embeddings (those are recomputed on import).
- Run this skill after any significant research or knowledge-building session.
