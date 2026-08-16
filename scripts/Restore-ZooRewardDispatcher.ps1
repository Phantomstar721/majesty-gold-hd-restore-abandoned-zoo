param(
    [string]$GamePath = "C:\Program Files (x86)\Steam\steamapps\common\Majesty HD",
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"
$SectionName = ".mzoo"
$PatchVirtualSize = 0x574
$PatchRawSize = 0x600
$DataSectionName = ".mzdt"
$DataSectionCharacteristics = [uint32]0xC0000040L
$DataSectionVirtualSize = 0x04
$DataSectionRawSize = 0x200
$LegacyPatchVirtualSize = 0xA0
$LegacyPatchRawSize = 0x200
$PrivateFactoryOffset = 0x40
$PrivateHandlerOffset = 0xE0
$PrivateVtableOffset = 0x160
$ModeRegistrationOffset = 0x1C0
$CaptureCallbackOffset = 0x240
$CapturePrototypeNameOffset = 0x420
$FactoryHookOffset = 0x10A020
$FactoryHookVa = 0x0050AC20
$FactoryResumeVa = 0x0050AC26
$Ap41FactoryVa = 0x0050AF8F
$OpenDialogVa = 0x004B03F0
$PalaceDispatchVa = 0x004A5440
$DispatchSlotOffset = 0x33DFA8
$ModeRegistryHookOffset = 0x5D8E4
$ModeRegistryHookVa = 0x0045E4E4
[byte[]]$StockFactoryHook = @(0x8B, 0x4C, 0x24, 0x14, 0x33, 0xC0)
[byte[]]$StockModeRegistryHook = @(
    0x8B,0x4C,0x24,0x10,0x64,0x89,0x0D,0x00,0x00,0x00,0x00
)
[byte[]]$StockDispatchSlot = @(0x80, 0xD2, 0x4B, 0x00) # 0x004BD280
[byte[]]$LegacyPalaceDispatchSlot = @(0x40, 0x54, 0x4A, 0x00) # checkpoint aaa9753

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
    if ($Offset -lt 0 -or ($Offset + $Patch.Length) -gt $Bytes.Length) { throw ("Restore range at 0x{0:X} is outside MajestyHD.exe." -f $Offset) }
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
            Index = $i; HeaderOffset = $off
            Name = [Text.Encoding]::ASCII.GetString($Bytes[$off..($off + 7)]).TrimEnd([char]0)
            VirtualSize = Read-U32 $Bytes ($off + 8); Rva = Read-U32 $Bytes ($off + 12)
            RawSize = Read-U32 $Bytes ($off + 16); RawOffset = Read-U32 $Bytes ($off + 20)
            Characteristics = Read-U32 $Bytes ($off + 36)
        }
    }
    [pscustomobject]@{
        SectionCountOffset = $sectionCountOffset; SectionCount = $sectionCount
        OptionalHeaderOffset = $optionalHeaderOffset; SectionTableOffset = $sectionTableOffset
        ImageBase = Read-U32 $Bytes ($optionalHeaderOffset + 28)
        SectionAlignment = Read-U32 $Bytes ($optionalHeaderOffset + 32)
        SizeOfImageOffset = $optionalHeaderOffset + 56
        Sections = $sections
    }
}
function New-RelativeInstruction {
    param([byte]$Opcode, [uint32]$SourceVa, [uint32]$TargetVa)
    [byte[]]$result = New-Object byte[] 5
    $result[0] = $Opcode
    $relative = [int]([int64]$TargetVa - ([int64]$SourceVa + 5))
    [BitConverter]::GetBytes($relative).CopyTo($result, 1)
    $result
}
function New-LegacyPatchBlob {
    param([uint32]$PatchVa)
    [byte[]]$blob = New-Object byte[] $LegacyPatchRawSize
    [byte[]]$dispatch = @(
        0x8B,0x44,0x24,0x04,0x3D,0x89,0x13,0x00,0x00,0x75,0x0F,
        0x6A,0x00,0x68,0x5A,0x43,0x30,0x31,0xE8,0,0,0,0,
        0xC2,0x04,0x00,0xE9,0,0,0,0
    )
    Write-Bytes $dispatch 18 (New-RelativeInstruction 0xE8 ([uint32]($PatchVa + 18)) $OpenDialogVa)
    Write-Bytes $dispatch 26 (New-RelativeInstruction 0xE9 ([uint32]($PatchVa + 26)) $PalaceDispatchVa)
    Write-Bytes $blob 0 $dispatch
    [byte[]]$factory = @(
        0x8B,0x4C,0x24,0x14,0x81,0xF9,0x5A,0x43,0x30,0x31,0x75,0x07,
        0x33,0xC0,0xE9,0,0,0,0,0x33,0xC0,0xE9,0,0,0,0
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
$pe = Get-PeInfo $bytes
$section = $pe.Sections | Where-Object Name -eq $SectionName | Select-Object -First 1
$dataSection = $pe.Sections | Where-Object Name -eq $DataSectionName | Select-Object -First 1
$dataSectionIsCompatible = -not $dataSection -or
    ($dataSection.Characteristics -eq $DataSectionCharacteristics -and
     $dataSection.VirtualSize -ge $DataSectionVirtualSize -and
     $dataSection.RawSize -ge $DataSectionRawSize -and
     ($dataSection.RawOffset + $dataSection.RawSize) -le $bytes.Length)
if (-not $dataSectionIsCompatible) { throw "MajestyHD.exe contains an incompatible .mzdt section." }
$factoryIsStock = Test-BytesEqual $bytes $FactoryHookOffset $StockFactoryHook
$dispatchIsStock = Test-BytesEqual $bytes $DispatchSlotOffset $StockDispatchSlot
$dispatchIsLegacy = Test-BytesEqual $bytes $DispatchSlotOffset $LegacyPalaceDispatchSlot
$modeRegistryIsStock = Test-BytesEqual $bytes $ModeRegistryHookOffset $StockModeRegistryHook

$installed = $false
$legacyInstalled = $false
$inert = $false
if ($section) {
    if ($section.RawSize -lt $LegacyPatchRawSize -or ($section.RawOffset + $section.RawSize) -gt $bytes.Length) {
        throw "MajestyHD.exe contains an incompatible .mzoo section."
    }
    $patchVa = [uint32]($pe.ImageBase + $section.Rva)
    [byte[]]$legacyPayload = New-LegacyPatchBlob $patchVa
    [byte[]]$factoryHook = New-RelativeInstruction 0xE9 $FactoryHookVa ([uint32]($patchVa + $PrivateFactoryOffset))
    $factoryHook += [byte[]]@(0x90)
    [byte[]]$modeRegistryHook = New-RelativeInstruction 0xE9 $ModeRegistryHookVa ([uint32]($patchVa + $ModeRegistrationOffset))
    $modeRegistryHook += [byte[]]@(0x90,0x90,0x90,0x90,0x90,0x90)
    [byte[]]$privateDispatchSlot = [BitConverter]::GetBytes($patchVa)
    $legacyInstalled = (Test-BytesEqual $bytes $FactoryHookOffset $factoryHook) -and
        (Test-BytesEqual $bytes $DispatchSlotOffset $privateDispatchSlot) -and
        $modeRegistryIsStock -and
        (Test-BytesEqual $bytes $section.RawOffset $legacyPayload)

    if ($section.RawSize -ge $PatchRawSize -and $section.VirtualSize -ge $PatchVirtualSize) {
        [byte[]]$signature = [Text.Encoding]::ASCII.GetBytes("RestoreAbandonedZoo.ZC01.ZCF0")
        [byte[]]$prototypeName = [Text.Encoding]::ASCII.GetBytes("Restore_Capture_Flag`0")
        $privateHandlerVa = [uint32]($patchVa + $PrivateHandlerOffset)
        $privateCallbackVa = [uint32]($patchVa + $CaptureCallbackOffset)
        $privateNameVa = [uint32]($patchVa + $CapturePrototypeNameOffset)
        $installed = (Test-BytesEqual $bytes $FactoryHookOffset $factoryHook) -and
            (Test-BytesEqual $bytes $DispatchSlotOffset $privateDispatchSlot) -and
            (Test-BytesEqual $bytes $ModeRegistryHookOffset $modeRegistryHook) -and
            (Test-BytesEqual $bytes ($section.RawOffset + 0x190) $signature) -and
            (Test-BytesEqual $bytes ($section.RawOffset + $CapturePrototypeNameOffset) $prototypeName) -and
            ((Read-U32 $bytes ($section.RawOffset + $PrivateVtableOffset + 0x0C)) -eq $privateHandlerVa) -and
            ((Read-U32 $bytes ($section.RawOffset + $ModeRegistrationOffset + 0x21)) -eq $privateCallbackVa) -and
            ((Read-U32 $bytes ($section.RawOffset + $CaptureCallbackOffset + 0xD1)) -eq $privateNameVa)
    }
    $inert = $factoryIsStock -and $dispatchIsStock -and $modeRegistryIsStock -and (Test-ZeroRange $bytes $section.RawOffset $section.RawSize)
    if (-not ($installed -or $legacyInstalled -or $inert)) { throw "MajestyHD.exe contains a partial or unrecognized Zoo private-panel patch." }
}
elseif (-not ($factoryIsStock -and $modeRegistryIsStock -and ($dispatchIsStock -or $dispatchIsLegacy))) {
    throw "MajestyHD.exe does not contain a recognized Zoo reward-dispatch state."
}

$sectionIsLast = $section -and -not $dataSection -and $section.Index -eq ($pe.SectionCount - 1) -and ($section.RawOffset + $section.RawSize) -eq $bytes.Length
$sectionPairIsLast = $section -and $dataSection -and
    $section.Index -eq ($pe.SectionCount - 2) -and
    $dataSection.Index -eq ($pe.SectionCount - 1) -and
    ($section.RawOffset + $section.RawSize) -eq $dataSection.RawOffset -and
    ($dataSection.RawOffset + $dataSection.RawSize) -eq $bytes.Length
$trailingPrivateSections = $sectionIsLast -or $sectionPairIsLast
$needsLegacyRestore = -not $section -and $dispatchIsLegacy
$needsWork = $installed -or $legacyInstalled -or $needsLegacyRestore -or ($inert -and $trailingPrivateSections)
Write-Host "Majesty Gold HD Restore Abandoned Zoo private Capture Flag restore"
if (-not $needsWork) {
    Write-Host "MajestyHD.exe: the stock MX09/factory routes are already restored."
}
elseif ($DryRun) {
    Write-Host ("MajestyHD.exe: would restore the stock routes and {0}." -f $(if ($sectionPairIsLast) { "remove trailing .mzoo/.mzdt" } elseif ($sectionIsLast) { "remove trailing .mzoo" } else { "leave inert private sections" }))
}
else {
    if (Get-Process -Name "MajestyHD" -ErrorAction SilentlyContinue) { throw "Majesty Gold HD is running. Close the game before restoring the Zoo rewards panel." }
    if ($installed -or $legacyInstalled -or $needsLegacyRestore) {
        Write-Bytes $bytes $FactoryHookOffset $StockFactoryHook
        Write-Bytes $bytes $DispatchSlotOffset $StockDispatchSlot
        if ($installed) { Write-Bytes $bytes $ModeRegistryHookOffset $StockModeRegistryHook }
    }
    if ($sectionPairIsLast) {
        [byte[]]$restored = New-Object byte[] $section.RawOffset
        [Array]::Copy($bytes, 0, $restored, 0, $restored.Length)
        Write-Bytes $restored $section.HeaderOffset (New-Object byte[] 40)
        Write-Bytes $restored $dataSection.HeaderOffset (New-Object byte[] 40)
        [BitConverter]::GetBytes([uint16]($pe.SectionCount - 2)).CopyTo($restored, $pe.SectionCountOffset)
        $previous = $pe.Sections | Where-Object { $_.Index -ne $section.Index -and $_.Index -ne $dataSection.Index } | Sort-Object { $_.Rva + [Math]::Max($_.VirtualSize, $_.RawSize) } | Select-Object -Last 1
        $sizeOfImage = Align-Value ([uint32]($previous.Rva + [Math]::Max($previous.VirtualSize, $previous.RawSize))) $pe.SectionAlignment
        [BitConverter]::GetBytes([uint32]$sizeOfImage).CopyTo($restored, $pe.SizeOfImageOffset)
    }
    elseif ($sectionIsLast) {
        [byte[]]$restored = New-Object byte[] $section.RawOffset
        [Array]::Copy($bytes, 0, $restored, 0, $restored.Length)
        Write-Bytes $restored $section.HeaderOffset (New-Object byte[] 40)
        [BitConverter]::GetBytes([uint16]($pe.SectionCount - 1)).CopyTo($restored, $pe.SectionCountOffset)
        $previous = $pe.Sections | Where-Object Index -ne $section.Index | Sort-Object { $_.Rva + [Math]::Max($_.VirtualSize, $_.RawSize) } | Select-Object -Last 1
        $sizeOfImage = Align-Value ([uint32]($previous.Rva + [Math]::Max($previous.VirtualSize, $previous.RawSize))) $pe.SectionAlignment
        [BitConverter]::GetBytes([uint32]$sizeOfImage).CopyTo($restored, $pe.SizeOfImageOffset)
    }
    else {
        $restored = $bytes
        if ($section) { Write-Bytes $restored $section.RawOffset (New-Object byte[] $section.RawSize) }
        if ($dataSection) { Write-Bytes $restored $dataSection.RawOffset (New-Object byte[] $dataSection.RawSize) }
    }
    try { [IO.File]::WriteAllBytes($exePath, $restored) }
    catch { throw "Cannot modify MajestyHD.exe. Close Majesty and try again. If needed, run PowerShell as administrator." }
    Write-Host "MajestyHD.exe: restored stock MX09/factory/flag-mode routing; unrelated CG and QOL patches were left untouched."
}
