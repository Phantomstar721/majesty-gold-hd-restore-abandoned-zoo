param(
    [string]$GamePath = "C:\Program Files (x86)\Steam\steamapps\common\Majesty HD",
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"
$SectionName = ".mzoo"
$SectionCharacteristics = 0x60000020
$PatchVirtualSize = 0xA0
$PatchRawSize = 0x200
$PrivateFactoryOffset = 0x40
$FactoryHookOffset = 0x10A020
$FactoryHookVa = 0x0050AC20
$FactoryResumeVa = 0x0050AC26
$Ap41FactoryVa = 0x0050AF8F
$OpenDialogVa = 0x004B03F0
$PalaceDispatchVa = 0x004A5440
$DispatchSlotOffset = 0x33DFA8
$PalaceHandlerOffset = 0xA4840
$Ap41FactoryOffset = 0x10A38F
$OpenDialogOffset = 0xAF7F0
[byte[]]$StockFactoryHook = @(0x8B, 0x4C, 0x24, 0x14, 0x33, 0xC0)
[byte[]]$StockDispatchSlot = @(0x80, 0xD2, 0x4B, 0x00) # 0x004BD280
[byte[]]$LegacyPalaceDispatchSlot = @(0x40, 0x54, 0x4A, 0x00) # checkpoint aaa9753
[byte[]]$PalaceHandlerSignature = @(
    0x8B, 0x44, 0x24, 0x04, 0x3D, 0x89, 0x13, 0x00,
    0x00, 0x7F, 0x3E, 0x74, 0x2D
)
[byte[]]$Ap41FactorySignature = @(
    0x6A, 0x34, 0xE8, 0xE8, 0xDF, 0x1C, 0x00, 0x83,
    0xC4, 0x04, 0x89, 0x44, 0x24, 0x14
)
[byte[]]$OpenDialogSignature = @(
    0x53, 0x56, 0x8B, 0x74, 0x24, 0x10, 0x57, 0x8B,
    0xF9, 0x85, 0xF6, 0x75, 0x07
)

function Read-U16 { param([byte[]]$Bytes, [int]$Offset) [BitConverter]::ToUInt16($Bytes, $Offset) }
function Read-U32 { param([byte[]]$Bytes, [int]$Offset) [BitConverter]::ToUInt32($Bytes, $Offset) }
function Align-Value {
    param([uint32]$Value, [uint32]$Alignment)
    [uint32](([uint64][Math]::Ceiling([double]$Value / [double]$Alignment)) * $Alignment)
}
function Test-BytesEqual {
    param([byte[]]$Bytes, [int]$Offset, [byte[]]$Expected)
    if ($Offset -lt 0 -or ($Offset + $Expected.Length) -gt $Bytes.Length) { return $false }
    for ($i = 0; $i -lt $Expected.Length; $i++) {
        if ($Bytes[$Offset + $i] -ne $Expected[$i]) { return $false }
    }
    return $true
}
function Test-ZeroRange {
    param([byte[]]$Bytes, [int]$Offset, [int]$Length)
    if ($Offset -lt 0 -or ($Offset + $Length) -gt $Bytes.Length) { return $false }
    for ($i = 0; $i -lt $Length; $i++) { if ($Bytes[$Offset + $i] -ne 0) { return $false } }
    return $true
}
function Write-Bytes {
    param([byte[]]$Bytes, [int]$Offset, [byte[]]$Patch)
    if ($Offset -lt 0 -or ($Offset + $Patch.Length) -gt $Bytes.Length) {
        throw ("Patch range at 0x{0:X} falls outside MajestyHD.exe." -f $Offset)
    }
    [Array]::Copy($Patch, 0, $Bytes, $Offset, $Patch.Length)
}
function Get-PeInfo {
    param([byte[]]$Bytes)
    $peOffset = Read-U32 $Bytes 0x3C
    $sectionCountOffset = $peOffset + 6
    $sectionCount = Read-U16 $Bytes $sectionCountOffset
    $optionalHeaderSize = Read-U16 $Bytes ($peOffset + 20)
    $optionalHeaderOffset = $peOffset + 24
    $sectionTableOffset = $optionalHeaderOffset + $optionalHeaderSize
    $sections = @()
    for ($i = 0; $i -lt $sectionCount; $i++) {
        $off = $sectionTableOffset + ($i * 40)
        $sections += [pscustomobject]@{
            Index = $i
            HeaderOffset = $off
            Name = [Text.Encoding]::ASCII.GetString($Bytes[$off..($off + 7)]).TrimEnd([char]0)
            VirtualSize = Read-U32 $Bytes ($off + 8)
            Rva = Read-U32 $Bytes ($off + 12)
            RawSize = Read-U32 $Bytes ($off + 16)
            RawOffset = Read-U32 $Bytes ($off + 20)
            Characteristics = Read-U32 $Bytes ($off + 36)
        }
    }
    [pscustomobject]@{
        SectionCountOffset = $sectionCountOffset
        SectionCount = $sectionCount
        OptionalHeaderOffset = $optionalHeaderOffset
        SectionTableOffset = $sectionTableOffset
        ImageBase = Read-U32 $Bytes ($optionalHeaderOffset + 28)
        SectionAlignment = Read-U32 $Bytes ($optionalHeaderOffset + 32)
        FileAlignment = Read-U32 $Bytes ($optionalHeaderOffset + 36)
        SizeOfImageOffset = $optionalHeaderOffset + 56
        SizeOfHeaders = Read-U32 $Bytes ($optionalHeaderOffset + 60)
        Sections = $sections
    }
}
function New-SectionHeader {
    param([string]$Name, [uint32]$VirtualSize, [uint32]$Rva, [uint32]$RawSize, [uint32]$RawOffset)
    [byte[]]$result = New-Object byte[] 40
    [Text.Encoding]::ASCII.GetBytes($Name).CopyTo($result, 0)
    [BitConverter]::GetBytes($VirtualSize).CopyTo($result, 8)
    [BitConverter]::GetBytes($Rva).CopyTo($result, 12)
    [BitConverter]::GetBytes($RawSize).CopyTo($result, 16)
    [BitConverter]::GetBytes($RawOffset).CopyTo($result, 20)
    [BitConverter]::GetBytes([uint32]$SectionCharacteristics).CopyTo($result, 36)
    $result
}
function New-RelativeInstruction {
    param([byte]$Opcode, [uint32]$SourceVa, [uint32]$TargetVa)
    [byte[]]$result = New-Object byte[] 5
    $result[0] = $Opcode
    $relative = [int]([int64]$TargetVa - ([int64]$SourceVa + 5))
    [BitConverter]::GetBytes($relative).CopyTo($result, 1)
    $result
}
function New-PatchBlob {
    param([uint32]$PatchVa)
    [byte[]]$blob = New-Object byte[] $PatchRawSize
    [byte[]]$dispatch = @(
        0x8B,0x44,0x24,0x04,             # mov eax,[esp+4]
        0x3D,0x89,0x13,0x00,0x00,        # cmp eax,0x1389
        0x75,0x0F,                        # jne fallback
        0x6A,0x00,                        # push 0
        0x68,0x5A,0x43,0x30,0x31,         # push "ZC01"
        0xE8,0x00,0x00,0x00,0x00,        # call OpenDialog
        0xC2,0x04,0x00,                   # ret 4
        0xE9,0x00,0x00,0x00,0x00         # fallback: jmp Palace dispatcher
    )
    Write-Bytes $dispatch 18 (New-RelativeInstruction 0xE8 ([uint32]($PatchVa + 18)) $OpenDialogVa)
    Write-Bytes $dispatch 26 (New-RelativeInstruction 0xE9 ([uint32]($PatchVa + 26)) $PalaceDispatchVa)
    Write-Bytes $blob 0 $dispatch

    [byte[]]$factory = @(
        0x8B,0x4C,0x24,0x14,             # mov ecx,[esp+14]
        0x81,0xF9,0x5A,0x43,0x30,0x31,   # cmp ecx,"ZC01"
        0x75,0x07,                        # jne stock
        0x33,0xC0,                        # xor eax,eax
        0xE9,0x00,0x00,0x00,0x00,        # jmp AP41 allocation
        0x33,0xC0,                        # stock: xor eax,eax
        0xE9,0x00,0x00,0x00,0x00         # jmp stock factory continuation
    )
    $factoryVa = [uint32]($PatchVa + $PrivateFactoryOffset)
    Write-Bytes $factory 14 (New-RelativeInstruction 0xE9 ([uint32]($factoryVa + 14)) $Ap41FactoryVa)
    Write-Bytes $factory 21 (New-RelativeInstruction 0xE9 ([uint32]($factoryVa + 21)) $FactoryResumeVa)
    Write-Bytes $blob $PrivateFactoryOffset $factory
    [Text.Encoding]::ASCII.GetBytes("RestoreAbandonedZoo.ZC01.AP41").CopyTo($blob, 0x80)
    $blob
}

$resolvedGamePath = [IO.Path]::GetFullPath($GamePath)
$exePath = Join-Path $resolvedGamePath "MajestyHD.exe"
if (-not (Test-Path -LiteralPath $exePath -PathType Leaf)) { throw "Could not find MajestyHD.exe at $exePath." }
[byte[]]$bytes = [IO.File]::ReadAllBytes($exePath)
if (-not (Test-BytesEqual $bytes $PalaceHandlerOffset $PalaceHandlerSignature) -or
    -not (Test-BytesEqual $bytes $Ap41FactoryOffset $Ap41FactorySignature) -or
    -not (Test-BytesEqual $bytes $OpenDialogOffset $OpenDialogSignature)) {
    throw "MajestyHD.exe does not contain the recognized stock AP41 construction and dispatch lifecycle."
}

$pe = Get-PeInfo $bytes
$section = $pe.Sections | Where-Object Name -eq $SectionName | Select-Object -First 1
$sectionIsNew = $null -eq $section
if ($sectionIsNew) {
    $headerOffset = $pe.SectionTableOffset + ($pe.SectionCount * 40)
    if (($headerOffset + 40) -gt $pe.SizeOfHeaders) { throw "MajestyHD.exe has no room for the private Zoo section header." }
    $last = $pe.Sections | Sort-Object { $_.Rva + [Math]::Max($_.VirtualSize, $_.RawSize) } | Select-Object -Last 1
    $patchRva = Align-Value ([uint32]($last.Rva + [Math]::Max($last.VirtualSize, $last.RawSize))) $pe.SectionAlignment
    $patchRawOffset = Align-Value ([uint32]$bytes.Length) $pe.FileAlignment
    $section = [pscustomobject]@{
        Index = $pe.SectionCount; HeaderOffset = $headerOffset; Name = $SectionName
        VirtualSize = $PatchVirtualSize; Rva = $patchRva
        RawSize = $PatchRawSize; RawOffset = $patchRawOffset
        Characteristics = $SectionCharacteristics
    }
}
elseif ($section.VirtualSize -lt $PatchVirtualSize -or $section.RawSize -lt $PatchRawSize -or
        $section.Characteristics -ne $SectionCharacteristics -or
        ($section.RawOffset + $PatchRawSize) -gt $bytes.Length) {
    throw "MajestyHD.exe contains an incompatible .mzoo section."
}

$patchVa = [uint32]($pe.ImageBase + $section.Rva)
[byte[]]$payload = New-PatchBlob $patchVa
[byte[]]$factoryHook = New-RelativeInstruction 0xE9 $FactoryHookVa ([uint32]($patchVa + $PrivateFactoryOffset))
$factoryHook += [byte[]]@(0x90)
[byte[]]$privateDispatchSlot = [BitConverter]::GetBytes($patchVa)
$factoryIsStock = Test-BytesEqual $bytes $FactoryHookOffset $StockFactoryHook
$factoryIsPatched = Test-BytesEqual $bytes $FactoryHookOffset $factoryHook
$dispatchIsStock = Test-BytesEqual $bytes $DispatchSlotOffset $StockDispatchSlot
$dispatchIsLegacy = Test-BytesEqual $bytes $DispatchSlotOffset $LegacyPalaceDispatchSlot
$dispatchIsPatched = Test-BytesEqual $bytes $DispatchSlotOffset $privateDispatchSlot
$payloadMatches = -not $sectionIsNew -and (Test-BytesEqual $bytes $section.RawOffset $payload)
$payloadIsZero = -not $sectionIsNew -and (Test-ZeroRange $bytes $section.RawOffset $PatchRawSize)
$installed = -not $sectionIsNew -and $factoryIsPatched -and $dispatchIsPatched -and $payloadMatches
$installable = $sectionIsNew -and $factoryIsStock -and ($dispatchIsStock -or $dispatchIsLegacy)
$reactivatable = -not $sectionIsNew -and $factoryIsStock -and ($dispatchIsStock -or $dispatchIsLegacy) -and $payloadIsZero
if (-not ($installed -or $installable -or $reactivatable)) {
    throw "MajestyHD.exe contains a partial or unrecognized Zoo private-panel patch; refusing to overwrite it."
}

Write-Host "Majesty Gold HD Restore Abandoned Zoo private rewards panel"
if ($installed) {
    Write-Host "MajestyHD.exe: the private ZC01/AP41 controller route is already installed."
}
elseif ($DryRun) {
    Write-Host ("MajestyHD.exe: would {0} .mzoo and route only ZC01 through the stock AP41 constructor." -f $(if ($sectionIsNew) { "append" } else { "reactivate" }))
}
else {
    if (Get-Process -Name "MajestyHD" -ErrorAction SilentlyContinue) { throw "Majesty Gold HD is running. Close the game before installing the Zoo rewards panel." }
    if ($sectionIsNew) {
        [byte[]]$expanded = New-Object byte[] ($section.RawOffset + $PatchRawSize)
        [Array]::Copy($bytes, 0, $expanded, 0, $bytes.Length)
        $bytes = $expanded
        Write-Bytes $bytes $section.HeaderOffset (New-SectionHeader $SectionName $PatchVirtualSize $section.Rva $PatchRawSize $section.RawOffset)
        [BitConverter]::GetBytes([uint16]($pe.SectionCount + 1)).CopyTo($bytes, $pe.SectionCountOffset)
        $sizeOfImage = Align-Value ([uint32]($section.Rva + $PatchVirtualSize)) $pe.SectionAlignment
        [BitConverter]::GetBytes([uint32]$sizeOfImage).CopyTo($bytes, $pe.SizeOfImageOffset)
    }
    Write-Bytes $bytes $section.RawOffset $payload
    Write-Bytes $bytes $FactoryHookOffset $factoryHook
    Write-Bytes $bytes $DispatchSlotOffset $privateDispatchSlot
    try { [IO.File]::WriteAllBytes($exePath, $bytes) }
    catch { throw "Cannot modify MajestyHD.exe. Close Majesty and try again. If needed, run PowerShell as administrator." }
    [byte[]]$verified = [IO.File]::ReadAllBytes($exePath)
    if (-not (Test-BytesEqual $verified $FactoryHookOffset $factoryHook) -or
        -not (Test-BytesEqual $verified $DispatchSlotOffset $privateDispatchSlot) -or
        -not (Test-BytesEqual $verified $section.RawOffset $payload)) {
        throw "MajestyHD.exe verification failed after installing the private Zoo rewards panel."
    }
    Write-Host "MajestyHD.exe: ZC01 now uses the literal stock AP41 controller; existing CG and QOL routes were preserved."
}
