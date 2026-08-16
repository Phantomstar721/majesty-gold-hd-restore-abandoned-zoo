param(
    [string]$GamePath = "C:\Program Files (x86)\Steam\steamapps\common\Majesty HD",
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"
$DispatchSlotOffset = 0x33DFA8
[byte[]]$StockDispatchSlot = @(0x80, 0xD2, 0x4B, 0x00) # 0x004BD280
[byte[]]$PalaceDispatchSlot = @(0x40, 0x54, 0x4A, 0x00) # 0x004A5440

function Test-BytesEqual {
    param([byte[]]$Bytes, [int]$Offset, [byte[]]$Expected)
    if ($Offset -lt 0 -or ($Offset + $Expected.Length) -gt $Bytes.Length) { return $false }
    for ($i = 0; $i -lt $Expected.Length; $i++) {
        if ($Bytes[$Offset + $i] -ne $Expected[$i]) { return $false }
    }
    return $true
}

$resolvedGamePath = [IO.Path]::GetFullPath($GamePath)
$exePath = Join-Path $resolvedGamePath "MajestyHD.exe"
if (-not (Test-Path -LiteralPath $exePath -PathType Leaf)) {
    throw "Could not find MajestyHD.exe at $exePath."
}
[byte[]]$bytes = [IO.File]::ReadAllBytes($exePath)
$isStock = Test-BytesEqual $bytes $DispatchSlotOffset $StockDispatchSlot
$isPatched = Test-BytesEqual $bytes $DispatchSlotOffset $PalaceDispatchSlot
if (-not ($isStock -or $isPatched)) {
    throw ("MajestyHD.exe has unexpected bytes at the MX09 dispatch slot 0x{0:X}." -f $DispatchSlotOffset)
}

Write-Host "Majesty Gold HD Restore Abandoned Zoo reward-dispatch restore"
if ($isStock) {
    Write-Host "MajestyHD.exe: the stock MX09 dispatcher is already restored."
}
elseif ($DryRun) {
    Write-Host ("MajestyHD.exe: would restore MX09's stock dispatch slot at 0x{0:X}." -f $DispatchSlotOffset)
}
else {
    if (Get-Process -Name "MajestyHD" -ErrorAction SilentlyContinue) {
        throw "Majesty Gold HD is running. Close the game before restoring the Zoo reward dispatcher."
    }
    [Array]::Copy($StockDispatchSlot, 0, $bytes, $DispatchSlotOffset, $StockDispatchSlot.Length)
    try {
        [IO.File]::WriteAllBytes($exePath, $bytes)
    }
    catch {
        throw "Cannot modify MajestyHD.exe. Close Majesty and try again. If needed, run PowerShell as administrator."
    }
    [byte[]]$verified = [IO.File]::ReadAllBytes($exePath)
    if (-not (Test-BytesEqual $verified $DispatchSlotOffset $StockDispatchSlot)) {
        throw "MajestyHD.exe verification failed after restoring the MX09 dispatcher."
    }
    Write-Host "MajestyHD.exe: restored MX09's stock dispatcher; unrelated executable patches were left untouched."
}
