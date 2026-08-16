param(
    [string]$GamePath = "C:\Program Files (x86)\Steam\steamapps\common\Majesty HD",
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"
$SectionName = ".mzoo"
$SectionCharacteristics = 0x60000020
$PatchVirtualSize = 0x450
$PatchRawSize = 0x600
$LegacyPatchVirtualSize = 0xA0
$LegacyPatchRawSize = 0x200
$PrivateFactoryHookOffset = 0x40
$PrivateFactoryOffset = 0xA0
$PrivateHandlerOffset = 0xE0
$PrivateVtableOffset = 0x160
$ModeRegistrationOffset = 0x1C0
$CaptureCallbackOffset = 0x240
$CapturePrototypeNameOffset = 0x420
$CaptureCursorSelector = 0x20

$FactoryHookOffset = 0x10A020
$FactoryHookVa = 0x0050AC20
$FactoryResumeVa = 0x0050AC26
$FactoryNullVa = 0x0050C035
$FactoryReturnVa = 0x0050C037
$OperatorNewVa = 0x006D8F7E
$Ap41ConstructorVa = 0x004A94E0
$OpenDialogVa = 0x004B03F0
$PalaceDispatchVa = 0x004A5440
$StockAp41HandlerVa = 0x004A92F0
$GetFlagModeManagerVa = 0x00454B90
$GetSelectedFlagModeVa = 0x004556D0
$SetFlagModeVa = 0x00454E70
$DispatchSlotOffset = 0x33DFA8
$PalaceHandlerOffset = 0xA4840
$Ap41FactoryOffset = 0x10A38F
$OpenDialogOffset = 0xAF7F0

$ModeRegistryHookOffset = 0x5D8E4
$ModeRegistryHookVa = 0x0045E4E4
$ModeRegistryResumeVa = 0x0045E4EF
$Fl00RegistrationOffset = 0x5D83E
$Fl00RegistrationVa = 0x0045E43E
$Fl00RegistrationLength = 0x53
$StockCaptureCallbackOffset = 0x5C800
$StockCaptureCallbackVa = 0x0045D400
$StockCaptureCallbackLength = 0x1D2
$StockAp41VtableOffset = 0x33D3B4
$StockAp41VtableLength = 0x2C

[byte[]]$StockFactoryHook = @(0x8B, 0x4C, 0x24, 0x14, 0x33, 0xC0)
[byte[]]$StockModeRegistryHook = @(
    0x8B,0x4C,0x24,0x10,             # mov ecx,[esp+10]
    0x64,0x89,0x0D,0x00,0x00,0x00,0x00 # mov fs:[0],ecx
)
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
[byte[]]$StockCallbackCreateSignature = @(
    0x57,0x68,0x04,0xBA,0x73,0x00,0xE8,0xB6,0xF7,0xFF,0xFF
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
function New-RelativeJcc {
    param([byte]$Opcode, [uint32]$SourceVa, [uint32]$TargetVa)
    [byte[]]$result = New-Object byte[] 6
    $result[0] = 0x0F
    $result[1] = $Opcode
    $relative = [int]([int64]$TargetVa - ([int64]$SourceVa + 6))
    [BitConverter]::GetBytes($relative).CopyTo($result, 2)
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
    $factoryVa = [uint32]($PatchVa + $PrivateFactoryHookOffset)
    Write-Bytes $factory 14 (New-RelativeInstruction 0xE9 ([uint32]($factoryVa + 14)) 0x0050AF8F)
    Write-Bytes $factory 21 (New-RelativeInstruction 0xE9 ([uint32]($factoryVa + 21)) $FactoryResumeVa)
    Write-Bytes $blob $PrivateFactoryHookOffset $factory
    [Text.Encoding]::ASCII.GetBytes("RestoreAbandonedZoo.ZC01.AP41").CopyTo($blob, 0x80)
    $blob
}

function New-PrivateHandler {
    param([uint32]$HandlerVa)
    [byte[]]$handler = @(
        0x53,0x56,0x57,0x8B,0xF1,0x8B,0x5C,0x24,0x10,
        0x81,0xFB,0x8A,0x13,0x00,0x00,0x74,0x51,
        0x83,0xFB,0x0A,0x74,0x0D,
        0x83,0xFB,0x0B,0x74,0x08,
        0x5F,0x5E,0x5B,0xE9,0,0,0,0,
        0x53,0x8B,0xCE,0xE8,0,0,0,0,
        0x8B,0x0D,0xF0,0x12,0x7C,0x00,
        0xE8,0,0,0,0,0x8B,0xC8,0xE8,0,0,0,0,
        0x3D,0x5A,0x43,0x46,0x30,0x75,0x16,
        0xFF,0x35,0xA4,0x17,0x7C,0x00,
        0x68,0x5A,0x43,0x46,0x30,
        0x8B,0x0D,0xF0,0x12,0x7C,0x00,
        0xE8,0,0,0,0,
        0x33,0xC0,0x5F,0x5E,0x5B,0xC2,0x04,0x00,
        0xFF,0x35,0xA4,0x17,0x7C,0x00,
        0x68,0x5A,0x43,0x46,0x30,
        0x8B,0x0D,0xF0,0x12,0x7C,0x00,
        0xE8,0,0,0,0,
        0x33,0xC0,0x5F,0x5E,0x5B,0xC2,0x04,0x00
    )
    if ($handler.Length -ne 0x80) { throw "Private ZC01 handler assembly changed length." }
    Write-Bytes $handler 30 (New-RelativeInstruction 0xE9 ([uint32]($HandlerVa + 30)) $StockAp41HandlerVa)
    Write-Bytes $handler 38 (New-RelativeInstruction 0xE8 ([uint32]($HandlerVa + 38)) $StockAp41HandlerVa)
    Write-Bytes $handler 49 (New-RelativeInstruction 0xE8 ([uint32]($HandlerVa + 49)) $GetFlagModeManagerVa)
    Write-Bytes $handler 56 (New-RelativeInstruction 0xE8 ([uint32]($HandlerVa + 56)) $GetSelectedFlagModeVa)
    Write-Bytes $handler 85 (New-RelativeInstruction 0xE8 ([uint32]($HandlerVa + 85)) $SetFlagModeVa)
    Write-Bytes $handler 115 (New-RelativeInstruction 0xE8 ([uint32]($HandlerVa + 115)) $SetFlagModeVa)
    $handler
}

function New-PrivateFactory {
    param([uint32]$FactoryVa, [uint32]$VtableVa)
    [byte[]]$factory = @(
        0x6A,0x34,0xE8,0,0,0,0,0x83,0xC4,0x04,
        0x89,0x44,0x24,0x14,0xC7,0x44,0x24,0x0C,0x16,0,0,0,
        0x85,0xC0,0x0F,0x84,0,0,0,0,
        0x8B,0x54,0x24,0x1C,0x8B,0x4C,0x24,0x18,
        0x52,0x51,0x8B,0xC8,0xE8,0,0,0,0,
        0xC7,0x00,0,0,0,0,0xE9,0,0,0,0
    )
    Write-Bytes $factory 2 (New-RelativeInstruction 0xE8 ([uint32]($FactoryVa + 2)) $OperatorNewVa)
    Write-Bytes $factory 24 (New-RelativeJcc 0x84 ([uint32]($FactoryVa + 24)) $FactoryNullVa)
    Write-Bytes $factory 42 (New-RelativeInstruction 0xE8 ([uint32]($FactoryVa + 42)) $Ap41ConstructorVa)
    [BitConverter]::GetBytes($VtableVa).CopyTo($factory, 49)
    Write-Bytes $factory 53 (New-RelativeInstruction 0xE9 ([uint32]($FactoryVa + 53)) $FactoryReturnVa)
    $factory
}

function New-CaptureCallback {
    param([byte[]]$Bytes, [uint32]$CallbackVa, [uint32]$PrototypeNameVa)
    [byte[]]$callback = $Bytes[$StockCaptureCallbackOffset..($StockCaptureCallbackOffset + $StockCaptureCallbackLength - 1)]
    if (-not (Test-BytesEqual $callback 0xCF $StockCallbackCreateSignature)) {
        throw "Stock Attack Flag completion callback creation seam changed."
    }
    $externalCalls = @{
        0x12 = 0x0045E900; 0x19 = 0x00425D00; 0x4F = 0x006418F0
        0x66 = 0x005D8620; 0x90 = 0x00641850; 0x9A = 0x00424A00
        0xAC = 0x0045D2D0; 0xBE = 0x0045E910; 0xCA = 0x005C2060
        0xD5 = 0x0045CC90; 0x117 = 0x00641850; 0x143 = 0x0045C950
        0x163 = 0x00641990; 0x17C = 0x00641990; 0x189 = 0x0045CAF0
        0x196 = 0x0045CA40
    }
    foreach ($item in $externalCalls.GetEnumerator()) {
        $offset = [int]$item.Key
        if ($callback[$offset] -ne 0xE8) { throw ("Stock callback call changed at +0x{0:X}." -f $offset) }
        Write-Bytes $callback $offset (New-RelativeInstruction 0xE8 ([uint32]($CallbackVa + $offset)) ([uint32]$item.Value))
    }
    [BitConverter]::GetBytes($PrototypeNameVa).CopyTo($callback, 0xD1)
    $callback
}

function New-CaptureModeRegistration {
    param(
        [byte[]]$Bytes,
        [uint32]$RegistrationVa,
        [uint32]$CallbackVa,
        [byte]$CursorSelector
    )
    [byte[]]$registration = $Bytes[$Fl00RegistrationOffset..($Fl00RegistrationOffset + $Fl00RegistrationLength - 1)]
    if ($registration[0x20] -ne 0x68 -or (Read-U32 $registration 0x21) -ne $StockCaptureCallbackVa -or
        $registration[0x2E] -ne 0x6A -or $registration[0x2F] -ne 0x05 -or
        $registration[0x30] -ne 0x68 -or (Read-U32 $registration 0x31) -ne 0x30306C46) {
        throw "Stock Fl00 placement-mode registration changed."
    }
    [BitConverter]::GetBytes([uint32]0x22).CopyTo($registration, 0x14)
    [BitConverter]::GetBytes($CallbackVa).CopyTo($registration, 0x21)
    [byte[]]$captureMode = @(0x5A,0x43,0x46,0x30) # ZCF0
    $captureMode.CopyTo($registration, 0x31)
    $registration[0x2F] = $CursorSelector
    Write-Bytes $registration 0x02 (New-RelativeInstruction 0xE8 ([uint32]($RegistrationVa + 0x02)) $OperatorNewVa)
    Write-Bytes $registration 0x37 (New-RelativeInstruction 0xE8 ([uint32]($RegistrationVa + 0x37)) 0x0059D1E0)
    Write-Bytes $registration 0x44 (New-RelativeInstruction 0xE8 ([uint32]($RegistrationVa + 0x44)) 0x0059EF30)

    [byte[]]$result = New-Object byte[] ($Fl00RegistrationLength + $StockModeRegistryHook.Length + 5)
    $registration.CopyTo($result, 0)
    $StockModeRegistryHook.CopyTo($result, $Fl00RegistrationLength)
    $jumpOffset = $Fl00RegistrationLength + $StockModeRegistryHook.Length
    Write-Bytes $result $jumpOffset (New-RelativeInstruction 0xE9 ([uint32]($RegistrationVa + $jumpOffset)) $ModeRegistryResumeVa)
    $result
}

function New-PatchBlob {
    param([byte[]]$Bytes, [uint32]$PatchVa, [byte]$CursorSelector)
    [byte[]]$blob = New-Object byte[] $PatchRawSize
    [byte[]]$dispatch = @(
        0x8B,0x44,0x24,0x04,             # mov eax,[esp+4]
        0x3D,0x89,0x13,0x00,0x00,        # cmp eax,0x1389
        0x75,0x0F,                        # jne fallback
        0x6A,0x00,                        # push 0
        0x68,0x5A,0x43,0x30,0x31,         # push "ZC01"
        0xE8,0,0,0,0,                    # call OpenDialog
        0xC2,0x04,0x00,                   # ret 4
        0xE9,0,0,0,0                     # fallback: jmp Palace dispatcher
    )
    Write-Bytes $dispatch 18 (New-RelativeInstruction 0xE8 ([uint32]($PatchVa + 18)) $OpenDialogVa)
    Write-Bytes $dispatch 26 (New-RelativeInstruction 0xE9 ([uint32]($PatchVa + 26)) $PalaceDispatchVa)
    Write-Bytes $blob 0 $dispatch

    $factoryHookVa = [uint32]($PatchVa + $PrivateFactoryHookOffset)
    [byte[]]$factoryHook = @(
        0x8B,0x4C,0x24,0x14,             # mov ecx,[esp+14]
        0x81,0xF9,0x5A,0x43,0x30,0x31,   # cmp ecx,"ZC01"
        0x75,0x07,                        # jne stock
        0x33,0xC0,                        # xor eax,eax
        0xE9,0,0,0,0,                    # jmp private allocation
        0x33,0xC0,                        # stock: xor eax,eax
        0xE9,0,0,0,0                     # jmp stock factory continuation
    )
    Write-Bytes $factoryHook 14 (New-RelativeInstruction 0xE9 ([uint32]($factoryHookVa + 14)) ([uint32]($PatchVa + $PrivateFactoryOffset)))
    Write-Bytes $factoryHook 21 (New-RelativeInstruction 0xE9 ([uint32]($factoryHookVa + 21)) $FactoryResumeVa)
    Write-Bytes $blob $PrivateFactoryHookOffset $factoryHook

    $handlerVa = [uint32]($PatchVa + $PrivateHandlerOffset)
    $vtableVa = [uint32]($PatchVa + $PrivateVtableOffset)
    Write-Bytes $blob $PrivateFactoryOffset (New-PrivateFactory ([uint32]($PatchVa + $PrivateFactoryOffset)) $vtableVa)
    Write-Bytes $blob $PrivateHandlerOffset (New-PrivateHandler $handlerVa)

    [byte[]]$vtable = $Bytes[$StockAp41VtableOffset..($StockAp41VtableOffset + $StockAp41VtableLength - 1)]
    if ((Read-U32 $vtable 0x0C) -ne $StockAp41HandlerVa) { throw "Stock AP41 primary vtable changed." }
    [BitConverter]::GetBytes($handlerVa).CopyTo($vtable, 0x0C)
    Write-Bytes $blob $PrivateVtableOffset $vtable

    $registrationVa = [uint32]($PatchVa + $ModeRegistrationOffset)
    $callbackVa = [uint32]($PatchVa + $CaptureCallbackOffset)
    $prototypeNameVa = [uint32]($PatchVa + $CapturePrototypeNameOffset)
    Write-Bytes $blob $ModeRegistrationOffset (New-CaptureModeRegistration $Bytes $registrationVa $callbackVa $CursorSelector)
    Write-Bytes $blob $CaptureCallbackOffset (New-CaptureCallback $Bytes $callbackVa $prototypeNameVa)
    [Text.Encoding]::ASCII.GetBytes("Restore_Capture_Flag`0").CopyTo($blob, $CapturePrototypeNameOffset)
    [Text.Encoding]::ASCII.GetBytes("RestoreAbandonedZoo.ZC01.ZCF0").CopyTo($blob, 0x190)
    $blob
}

$resolvedGamePath = [IO.Path]::GetFullPath($GamePath)
$exePath = Join-Path $resolvedGamePath "MajestyHD.exe"
if (-not (Test-Path -LiteralPath $exePath -PathType Leaf)) { throw "Could not find MajestyHD.exe at $exePath." }
[byte[]]$bytes = [IO.File]::ReadAllBytes($exePath)
if (-not (Test-BytesEqual $bytes $PalaceHandlerOffset $PalaceHandlerSignature) -or
    -not (Test-BytesEqual $bytes $Ap41FactoryOffset $Ap41FactorySignature) -or
    -not (Test-BytesEqual $bytes $OpenDialogOffset $OpenDialogSignature) -or
    -not (Test-BytesEqual $bytes ($StockCaptureCallbackOffset + 0xCF) $StockCallbackCreateSignature)) {
    throw "MajestyHD.exe does not contain the recognized stock reward-panel and Attack Flag lifecycle."
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
elseif ($section.Characteristics -ne $SectionCharacteristics -or
        $section.RawSize -lt $LegacyPatchRawSize -or
        ($section.RawOffset + $section.RawSize) -gt $bytes.Length) {
    throw "MajestyHD.exe contains an incompatible .mzoo section."
}

$patchVa = [uint32]($pe.ImageBase + $section.Rva)
[byte[]]$payload = New-PatchBlob $bytes $patchVa $CaptureCursorSelector
[byte[]]$previousPayload = New-PatchBlob $bytes $patchVa 0x05
[byte[]]$legacyPayload = New-LegacyPatchBlob $patchVa
[byte[]]$factoryHook = New-RelativeInstruction 0xE9 $FactoryHookVa ([uint32]($patchVa + $PrivateFactoryHookOffset))
$factoryHook += [byte[]]@(0x90)
[byte[]]$modeRegistryHook = New-RelativeInstruction 0xE9 $ModeRegistryHookVa ([uint32]($patchVa + $ModeRegistrationOffset))
$modeRegistryHook += [byte[]]@(0x90,0x90,0x90,0x90,0x90,0x90)
[byte[]]$privateDispatchSlot = [BitConverter]::GetBytes($patchVa)

$factoryIsStock = Test-BytesEqual $bytes $FactoryHookOffset $StockFactoryHook
$factoryIsPatched = Test-BytesEqual $bytes $FactoryHookOffset $factoryHook
$dispatchIsStock = Test-BytesEqual $bytes $DispatchSlotOffset $StockDispatchSlot
$dispatchIsLegacy = Test-BytesEqual $bytes $DispatchSlotOffset $LegacyPalaceDispatchSlot
$dispatchIsPatched = Test-BytesEqual $bytes $DispatchSlotOffset $privateDispatchSlot
$modeRegistryIsStock = Test-BytesEqual $bytes $ModeRegistryHookOffset $StockModeRegistryHook
$modeRegistryIsPatched = Test-BytesEqual $bytes $ModeRegistryHookOffset $modeRegistryHook
$payloadMatches = -not $sectionIsNew -and $section.RawSize -ge $PatchRawSize -and (Test-BytesEqual $bytes $section.RawOffset $payload)
$previousPayloadMatches = -not $sectionIsNew -and $section.RawSize -ge $PatchRawSize -and (Test-BytesEqual $bytes $section.RawOffset $previousPayload)
$legacyPayloadMatches = -not $sectionIsNew -and (Test-BytesEqual $bytes $section.RawOffset $legacyPayload)
$payloadIsZero = -not $sectionIsNew -and (Test-ZeroRange $bytes $section.RawOffset $section.RawSize)
$installed = -not $sectionIsNew -and $factoryIsPatched -and $dispatchIsPatched -and $modeRegistryIsPatched -and $payloadMatches
$cursorUpgradeable = -not $sectionIsNew -and $factoryIsPatched -and $dispatchIsPatched -and $modeRegistryIsPatched -and $previousPayloadMatches
$legacyInstalled = -not $sectionIsNew -and $factoryIsPatched -and $dispatchIsPatched -and $modeRegistryIsStock -and $legacyPayloadMatches
$installable = $sectionIsNew -and $factoryIsStock -and $modeRegistryIsStock -and ($dispatchIsStock -or $dispatchIsLegacy)
$reactivatable = -not $sectionIsNew -and $factoryIsStock -and $modeRegistryIsStock -and ($dispatchIsStock -or $dispatchIsLegacy) -and $payloadIsZero
if (-not ($installed -or $cursorUpgradeable -or $legacyInstalled -or $installable -or $reactivatable)) {
    throw "MajestyHD.exe contains a partial or unrecognized Zoo private-panel patch; refusing to overwrite it."
}

$sectionIsLast = -not $sectionIsNew -and $section.Index -eq ($pe.SectionCount - 1) -and ($section.RawOffset + $section.RawSize) -eq $bytes.Length
$needsExpansion = -not $sectionIsNew -and ($section.RawSize -lt $PatchRawSize -or $section.VirtualSize -lt $PatchVirtualSize)
if ($needsExpansion -and -not $sectionIsLast) { throw "The existing .mzoo section is not last and cannot be safely expanded." }

Write-Host "Majesty Gold HD Restore Abandoned Zoo private Capture Flag"
if ($installed) {
    Write-Host "MajestyHD.exe: the private ZC01/ZCF0 placement lifecycle is already installed."
}
elseif ($DryRun) {
    Write-Host ("MajestyHD.exe: would {0} .mzoo and route only ZC01 through private ZCF0 placement." -f $(if ($cursorUpgradeable -or $legacyInstalled) { "upgrade" } elseif ($sectionIsNew) { "append" } else { "reactivate" }))
}
else {
    if (Get-Process -Name "MajestyHD" -ErrorAction SilentlyContinue) { throw "Majesty Gold HD is running. Close the game before installing the Zoo Capture Flag." }
    if ($sectionIsNew) {
        [byte[]]$expanded = New-Object byte[] ($section.RawOffset + $PatchRawSize)
        [Array]::Copy($bytes, 0, $expanded, 0, $bytes.Length)
        $bytes = $expanded
        Write-Bytes $bytes $section.HeaderOffset (New-SectionHeader $SectionName $PatchVirtualSize $section.Rva $PatchRawSize $section.RawOffset)
        [BitConverter]::GetBytes([uint16]($pe.SectionCount + 1)).CopyTo($bytes, $pe.SectionCountOffset)
    }
    elseif ($needsExpansion) {
        [byte[]]$expanded = New-Object byte[] ($section.RawOffset + $PatchRawSize)
        [Array]::Copy($bytes, 0, $expanded, 0, $bytes.Length)
        $bytes = $expanded
        Write-Bytes $bytes $section.HeaderOffset (New-SectionHeader $SectionName $PatchVirtualSize $section.Rva $PatchRawSize $section.RawOffset)
    }
    $sizeOfImage = Align-Value ([uint32]($section.Rva + $PatchVirtualSize)) $pe.SectionAlignment
    [BitConverter]::GetBytes([uint32]$sizeOfImage).CopyTo($bytes, $pe.SizeOfImageOffset)
    Write-Bytes $bytes $section.RawOffset $payload
    Write-Bytes $bytes $FactoryHookOffset $factoryHook
    Write-Bytes $bytes $DispatchSlotOffset $privateDispatchSlot
    Write-Bytes $bytes $ModeRegistryHookOffset $modeRegistryHook
    try { [IO.File]::WriteAllBytes($exePath, $bytes) }
    catch { throw "Cannot modify MajestyHD.exe. Close Majesty and try again. If needed, run PowerShell as administrator." }
    [byte[]]$verified = [IO.File]::ReadAllBytes($exePath)
    if (-not (Test-BytesEqual $verified $FactoryHookOffset $factoryHook) -or
        -not (Test-BytesEqual $verified $DispatchSlotOffset $privateDispatchSlot) -or
        -not (Test-BytesEqual $verified $ModeRegistryHookOffset $modeRegistryHook) -or
        -not (Test-BytesEqual $verified $section.RawOffset $payload)) {
        throw "MajestyHD.exe verification failed after installing the private Capture Flag."
    }
    Write-Host "MajestyHD.exe: ZC01 now uses private ZCF0 placement; Palace AP41 remains on stock Fl00."
}
