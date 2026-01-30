$ErrorActionPreference = "Stop"

function Invoke-Api(
  [string]$Method,
  [string]$Path,
  [string]$BodyFile = $null,
  [string]$BodyJson = $null
) {
  $url = "http://127.0.0.1:3000$Path"
  $headers = @{ "Content-Type" = "application/json" }

  try {
    if ($BodyFile) {
      $body = Get-Content -Raw -Encoding UTF8 $BodyFile
      $resp = Invoke-WebRequest -Method $Method -Uri $url -Headers $headers -Body $body -UseBasicParsing -TimeoutSec 10
    } elseif ($BodyJson) {
      $resp = Invoke-WebRequest -Method $Method -Uri $url -Headers $headers -Body $BodyJson -UseBasicParsing -TimeoutSec 10
    } else {
      $resp = Invoke-WebRequest -Method $Method -Uri $url -Headers $headers -UseBasicParsing -TimeoutSec 10
    }

    $content = $null
    try { $content = $resp.Content } catch {}
    [PSCustomObject]@{ method=$Method; path=$Path; status=[int]$resp.StatusCode; body=$content }
  }
  catch {
    $webResp = $_.Exception.Response
    $status = $null
    $content = $null

    if ($webResp -and $webResp.StatusCode) {
      $status = [int]$webResp.StatusCode
      try {
        $sr = New-Object System.IO.StreamReader($webResp.GetResponseStream())
        $content = $sr.ReadToEnd()
        $sr.Close()
      } catch {}
    } else {
      $status = -1
      $content = $_.Exception.Message
    }

    [PSCustomObject]@{ method=$Method; path=$Path; status=$status; body=$content }
  }
}

Write-Host "== API smoke ==" -ForegroundColor Cyan

$outJson = Join-Path $PSScriptRoot "_smoke_results.json"
$outTxt  = Join-Path $PSScriptRoot "_smoke_results.txt"

$payloadLivro = Join-Path $PSScriptRoot "_smoke_payload_livro.json"
$payloadMulta = Join-Path $PSScriptRoot "_smoke_payload_multa.json"

$emptyJson = "{}"

$tests = @(
  # Saúde e consultas base
  { Invoke-Api GET "/health" },
  { Invoke-Api GET "/cliente?Nome=Teste" },
  { Invoke-Api GET "/cliente/cpf/00000000000" },
  { Invoke-Api GET "/endereco?Estado=SP" },
  { Invoke-Api GET "/livro?NomeLivro=Teste" },
  { Invoke-Api GET "/livro/autor?NomeAutor=Teste" },
  { Invoke-Api GET "/genero?NomeGenero=Teste" },

  # Operações (espera-se 400/404 em dados inválidos; falha só se 5xx)
  { Invoke-Api POST "/cliente" $null $emptyJson },
  { Invoke-Api POST "/reservas" $null $emptyJson },
  { Invoke-Api GET  "/reservas?status=ativa" },
  { Invoke-Api GET  "/reservas/0" },
  { Invoke-Api PUT  "/reservas/0" $null $emptyJson },
  { Invoke-Api PATCH "/reservas/0" $null $emptyJson },
  { Invoke-Api DELETE "/reservas/0" },
  { Invoke-Api POST "/devolucoes" $null $emptyJson },

  # Multas
  { Invoke-Api GET "/multas" },
  { Invoke-Api GET "/multas/0" },
  { Invoke-Api PATCH "/multas/0/pagar" $null $emptyJson },

  # Fluxos com payload real (quando existir)
  { if (Test-Path $payloadLivro) { Invoke-Api POST "/livro" $payloadLivro } else { [PSCustomObject]@{ method="POST"; path="/livro"; status=-1; body="payload file not found: $payloadLivro" } } },
  { if (Test-Path $payloadMulta) { Invoke-Api POST "/multas" $payloadMulta } else { [PSCustomObject]@{ method="POST"; path="/multas"; status=-1; body="payload file not found: $payloadMulta" } } }
)

$results = foreach ($t in $tests) { & $t }

# Falha só se não conectou (-1) ou retornou 5xx
$results = $results | ForEach-Object {
  $bad = ($_.status -lt 0) -or ($_.status -ge 500)
  $_ | Add-Member -NotePropertyName ok -NotePropertyValue (-not $bad) -Force
  $_
}

$results | Select-Object method,path,status,ok | Format-Table -AutoSize

# Persistência de resultados pra inspeção (mesmo quando o terminal não mostra output)
$results | ConvertTo-Json -Depth 5 | Set-Content -Encoding UTF8 $outJson
($results | Select-Object method,path,status,ok | Format-Table -AutoSize | Out-String) | Set-Content -Encoding UTF8 $outTxt

$failures = @($results | Where-Object { -not $_.ok })
if ($failures.Count -gt 0) {
  Write-Host "\n== Failures (body) ==" -ForegroundColor Yellow
  foreach ($f in $failures) {
    Write-Host ("\n{0} {1} => {2}" -f $f.method,$f.path,$f.status) -ForegroundColor Yellow
    if ($f.body) { Write-Host $f.body }
  }
  exit 1
}

Write-Host "\nAll smoke checks passed." -ForegroundColor Green
