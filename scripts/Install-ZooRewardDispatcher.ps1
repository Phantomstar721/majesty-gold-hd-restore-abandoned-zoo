param(
    [string]$GamePath = "C:\Program Files (x86)\Steam\steamapps\common\Majesty HD",
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"
$DispatchSlotOffset = 0x33DFA8
$PalaceHandlerOffset = 0xA4840
$ZooHandlerOffset = 0xBC680
[byte[]]$StockDispatchSlot = @(0x80, 0xD2, 0x4B, 0x00) # 0x004BD280
[byte[]]$PalaceDispatchSlot = @(0x40, 0x54, 0x4A, 0x00) # 0x004A5440
[byte[]]$PalaceHandlerSignature = @(
    0x8B, 0x44, 0x24, 0x04, 0x3D, 0x89, 0x13, 0x00,
    0x00, 0x7F, 0x3E, 0x74, 0x2D
)
[byte[]]$ZooHandlerSignature = @(0xE9, 0x0B, 0x85, 0xFD, 0xFF)

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
if (-not (Test-BytesEqual $bytes $PalaceHandlerOffset $PalaceHandlerSignature)) {
    throw "MajestyHD.exe does not contain the recognized stock Palace reward dispatcher."
}
if (-not (Test-BytesEqual $bytes $ZooHandlerOffset $ZooHandlerSignature)) {
    throw "MajestyHD.exe does not contain the recognized stock MX09 dispatcher trampoline."
}

$isStock = Test-BytesEqual $bytes $DispatchSlotOffset $StockDispatchSlot
$isPatched = Test-BytesEqual $bytes $DispatchSlotOffset $PalaceDispatchSlot
if (-not ($isStock -or $isPatched)) {
    throw ("MajestyHD.exe has unexpected bytes at the MX09 dispatch slot 0x{0:X}." -f $DispatchSlotOffset)
}

Write-Host "Majesty Gold HD Restore Abandoned Zoo reward dispatcher"
if ($isPatched) {
    Write-Host "MajestyHD.exe: the Zoo already uses the stock Palace reward dispatcher."
}
elseif ($DryRun) {
    Write-Host ("MajestyHD.exe: would route MX09's dispatch slot at 0x{0:X} through the stock Palace handler." -f $DispatchSlotOffset)
}
else {
    if (Get-Process -Name "MajestyHD" -ErrorAction SilentlyContinue) {
        throw "Majesty Gold HD is running. Close the game before installing the Zoo reward dispatcher."
    }
    [Array]::Copy($PalaceDispatchSlot, 0, $bytes, $DispatchSlotOffset, $PalaceDispatchSlot.Length)
    try {
        [IO.File]::WriteAllBytes($exePath, $bytes)
    }
    catch {
        throw "Cannot modify MajestyHD.exe. Close Majesty and try again. If needed, run PowerShell as administrator."
    }
    [byte[]]$verified = [IO.File]::ReadAllBytes($exePath)
    if (-not (Test-BytesEqual $verified $DispatchSlotOffset $PalaceDispatchSlot)) {
        throw "MajestyHD.exe verification failed after installing the Zoo reward dispatcher."
    }
    Write-Host "MajestyHD.exe: MX09 now uses the literal stock Palace reward dispatcher."
}
