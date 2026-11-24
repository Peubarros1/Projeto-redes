param([string]$alvo = "all")

function Start-Servers {
    Write-Host "1) Subindo servidor de nomes..."
    Start-Process python -ArgumentList "-u", "name_server.py" -WorkingDirectory $PSScriptRoot
    Start-Sleep -Seconds 1
    Write-Host "2) Subindo servicos TCP e UDP (registram-se no servidor de nomes)..."
    Start-Process python -ArgumentList "-u", "tcp_server.py" -WorkingDirectory $PSScriptRoot
    Start-Process python -ArgumentList "-u", "udp_server.py" -WorkingDirectory $PSScriptRoot
    Start-Sleep -Seconds 2
}

function Start-Clients {
    Set-Location $PSScriptRoot
    Write-Host "`n--- Cliente TCP ---";               python tcp_client.py MUL 6 7
    Write-Host "`n--- Cliente UDP ---";               python udp_client.py DIV 10 4
    Write-Host "`n--- Cliente servico inexistente ---"; python missing_client.py servico-fantasma
}

switch ($alvo) {
    "servers"   { Start-Servers }
    "clients"   { Start-Clients }
    "benchmark" { Set-Location $PSScriptRoot; python benchmark.py -n 300 }
    "all"       { Start-Servers; Start-Clients }
    default     { Write-Host "alvos: servers | clients | benchmark | all" }
}
