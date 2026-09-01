param(
    [string]$GamePath = "C:\Program Files (x86)\Steam\steamapps\common\Majesty HD",
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"
$SectionName = ".mzoo"
$SectionCharacteristics = 0x60000020
$DataSectionName = ".mzdt"
$DataSectionCharacteristics = [uint32]0xC0000040L
$DataSectionVirtualSize = 0x08
$DataSectionRawSize = 0x200
$PatchVirtualSize = 0x600
$PatchRawSize = 0x600
$LegacyPatchVirtualSize = 0xA0
$LegacyPatchRawSize = 0x200
$PrivateFactoryHookOffset = 0x40
$CaptureTargetValidatorOffset = 0x60
$PrivateCaptureTargetLegalityOffset = 0x60
$PrivateFactoryOffset = 0xA0
$PrivateHandlerOffset = 0xE0
$PrivateVtableOffset = 0x160
$ModeRegistrationOffset = 0x1C0
$CaptureCallbackOffset = 0x240
$CapturePrototypeNameOffset = 0x420
$CaptureCompletionTargetCheckOffset = 0x450
$PrivateRewardSwapOffset = 0x450
$PrivateActivationOffset = 0x470
$PrivateRewardSwapV17Offset = 0x1AD
$PrivateActivationV17Offset = 0x435
$PrivateRefreshV17Offset = 0x450
$CapacityTargetValidatorOffset = 0x490
$CapacityCompletionTargetCheckOffset = 0x4F0
$CapacityArmWrapperOffset = 0x550
$LegacyCaptureZooSlotOffset = 0x570
$BuggyZooFullAlertOffset = 0x580
$BuggyZooFullAlertTextOffset = 0x5B0
$ZooFullAlertOffset = 0x590
$ZooFullAlertTextOffset = 0x5C0
$CaptureCursorSelector = 0x26
$profileScript = Join-Path $PSScriptRoot "ZooRewardDispatcherProfiles.ps1"
if (-not (Test-Path -LiteralPath $profileScript -PathType Leaf)) {
    throw "Zoo reward-dispatcher profile table was not found: $profileScript"
}
. $profileScript

$Fl00RegistrationLength = 0x53
$StockCaptureCallbackLength = 0x1D2
$AttribZooLegalTarget = 0x00305A41
$CaptureFlagArtRelation = 0x3241435A # "ZCA2" (failed v14 assumption)
$CaptureFlagDescriptionRelation = 0x3046435A # "ZCF0"
$StockAp41VtableLength = 0x2C

[byte[]]$StockFactoryHook = @(0x8B, 0x4C, 0x24, 0x14, 0x33, 0xC0)
[byte[]]$StockModeRegistryHook = @(
    0x8B,0x4C,0x24,0x10,             # mov ecx,[esp+10]
    0x64,0x89,0x0D,0x00,0x00,0x00,0x00 # mov fs:[0],ecx
)
[byte[]]$PalaceHandlerSignature = @(
    0x8B, 0x44, 0x24, 0x04, 0x3D, 0x89, 0x13, 0x00,
    0x00, 0x7F, 0x3E, 0x74, 0x2D
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
    param(
        [string]$Name, [uint32]$VirtualSize, [uint32]$Rva,
        [uint32]$RawSize, [uint32]$RawOffset,
        [uint32]$Characteristics = $SectionCharacteristics
    )
    [byte[]]$result = New-Object byte[] 40
    [Text.Encoding]::ASCII.GetBytes($Name).CopyTo($result, 0)
    [BitConverter]::GetBytes($VirtualSize).CopyTo($result, 8)
    [BitConverter]::GetBytes($Rva).CopyTo($result, 12)
    [BitConverter]::GetBytes($RawSize).CopyTo($result, 16)
    [BitConverter]::GetBytes($RawOffset).CopyTo($result, 20)
    [BitConverter]::GetBytes($Characteristics).CopyTo($result, 36)
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
    Write-Bytes $factory 14 (New-RelativeInstruction 0xE9 ([uint32]($factoryVa + 14)) $Ap41FactoryVa)
    Write-Bytes $factory 21 (New-RelativeInstruction 0xE9 ([uint32]($factoryVa + 21)) $FactoryResumeVa)
    Write-Bytes $blob $PrivateFactoryHookOffset $factory
    [Text.Encoding]::ASCII.GetBytes("RestoreAbandonedZoo.ZC01.AP41").CopyTo($blob, 0x80)
    $blob
}

function New-PrivateHandler {
    param([uint32]$HandlerVa, [uint32]$CaptureArmVa)
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
    Write-Bytes $handler 115 (New-RelativeInstruction 0xE8 ([uint32]($HandlerVa + 115)) $CaptureArmVa)
    for ($i = 0; $i -le ($handler.Length - 4); $i++) {
        $value = Read-U32 $handler $i
        if ($value -eq 0x007C12F0) {
            [BitConverter]::GetBytes([uint32]$FlagModeOwnerVa).CopyTo($handler, $i)
        }
        elseif ($value -eq 0x007C17A4) {
            [BitConverter]::GetBytes([uint32]$AttackRewardAmountVa).CopyTo($handler, $i)
        }
    }
    $handler
}

function New-PrivateRewardSwap {
    param([uint32]$CaptureRewardAmountVa)
    # AP41's shipped Attack amount lives at 0x7C17A4. Swap the private Capture
    # channel through that exact stock slot while AP41 clamps, displays, or
    # adjusts it; calling this function a second time stores the updated
    # Capture value and restores Palace Attack atomically.
    [byte[]]$swap = @(
        0xA1,0,0,0,0,                    # mov eax,[CaptureRewardAmount]
        0x87,0x05,0,0,0,0,               # xchg [stock Attack amount],eax
        0xA3,0,0,0,0,                    # mov [CaptureRewardAmount],eax
        0xC3                               # ret
    )
    if ($swap.Length -ne 0x11) { throw "Private Capture reward swap changed length." }
    [BitConverter]::GetBytes($CaptureRewardAmountVa).CopyTo($swap, 0x01)
    [BitConverter]::GetBytes([uint32]$AttackRewardAmountVa).CopyTo($swap, 0x07)
    [BitConverter]::GetBytes($CaptureRewardAmountVa).CopyTo($swap, 0x0C)
    $swap
}

function New-PrivateRewardActivation {
    param([uint32]$ActivationVa, [uint32]$RewardSwapVa)
    # AP41 activation calls its stock refresh, which normalizes a negative
    # amount to RewardDelta, caps it against current gold, updates +/- enabled
    # states, and paints the numeric control. Scope that literal lifecycle to
    # Capture's private channel, then restore Palace Attack before returning.
    [byte[]]$activation = @(
        0x56,                              # push esi
        0x8B,0xF1,                        # mov esi,ecx
        0xE8,0,0,0,0,                    # call private reward swap (Capture in)
        0x8B,0xCE,                        # mov ecx,esi
        0xE8,0,0,0,0,                    # call stock AP41 activation
        0x50,                              # push eax (preserve stock result)
        0xE8,0,0,0,0,                    # call private reward swap (Capture out)
        0x58,                              # pop eax
        0x5E,                              # pop esi
        0xC3                               # ret
    )
    if ($activation.Length -ne 0x18) { throw "Private Capture activation wrapper changed length." }
    Write-Bytes $activation 0x03 (New-RelativeInstruction 0xE8 ([uint32]($ActivationVa + 0x03)) $RewardSwapVa)
    Write-Bytes $activation 0x0A (New-RelativeInstruction 0xE8 ([uint32]($ActivationVa + 0x0A)) $StockAp41ActivationVa)
    Write-Bytes $activation 0x10 (New-RelativeInstruction 0xE8 ([uint32]($ActivationVa + 0x10)) $RewardSwapVa)
    $activation
}

function New-PrivateRewardRefresh {
    param([uint32]$RefreshVa, [uint32]$RewardSwapVa)
    # AP41's secondary vtable refresh calls 0x4A9100 for APPA updates after
    # activation. Copy all four original arguments, run that complete shipped
    # callback with Capture scoped into the Attack slot, then restore Palace
    # Attack before returning through the callback's original RET 0x10 shape.
    [byte[]]$refresh = @(
        0x56,                              # push esi
        0x8B,0xF1,                        # mov esi,ecx
        0xE8,0,0,0,0,                    # call reward swap (Capture in)
        0xFF,0x74,0x24,0x14,              # push original arg 4
        0xFF,0x74,0x24,0x14,              # push original arg 3
        0xFF,0x74,0x24,0x14,              # push original arg 2
        0xFF,0x74,0x24,0x14,              # push original arg 1
        0x8B,0xCE,                        # mov ecx,esi
        0xE8,0,0,0,0,                    # call stock AP41 refresh
        0x50,                              # push eax (preserve stock result)
        0xE8,0,0,0,0,                    # call reward swap (Capture out)
        0x58,                              # pop eax
        0x5E,                              # pop esi
        0xC2,0x10,0x00                    # ret 0x10
    )
    if ($refresh.Length -ne 0x2A) { throw "Private Capture refresh wrapper changed length." }
    Write-Bytes $refresh 0x03 (New-RelativeInstruction 0xE8 ([uint32]($RefreshVa + 0x03)) $RewardSwapVa)
    Write-Bytes $refresh 0x1A (New-RelativeInstruction 0xE8 ([uint32]($RefreshVa + 0x1A)) $StockAp41RefreshVa)
    Write-Bytes $refresh 0x20 (New-RelativeInstruction 0xE8 ([uint32]($RefreshVa + 0x20)) $RewardSwapVa)
    $refresh
}

function New-PrivateRewardHandler {
    param(
        [uint32]$HandlerVa,
        [uint32]$CaptureArmVa,
        [uint32]$CaptureRewardAmountVa,
        [uint32]$RewardSwapVa
    )
    # Preserve AP41 command order. Non-Capture controls tail-call stock. The
    # shipped minus/plus commands run with Capture temporarily occupying the
    # stock Attack channel, so stock performs its exact adjustment, clamp, UI
    # refresh, and active-mode update. Direct placement pushes the private
    # amount without modifying Palace Attack.
    [byte[]]$handler = @(
        0x56,                              # push esi
        0x8B,0xF1,                        # mov esi,ecx
        0x8B,0x44,0x24,0x08,              # mov eax,[esp+8] (control ID)
        0x3D,0x8A,0x13,0x00,0x00,         # cmp eax,0x138A (Capture)
        0x74,0x53,                        # je direct
        0x83,0xF8,0x0A,                   # cmp eax,10 (minus)
        0x74,0x0B,                        # je adjust
        0x83,0xF8,0x0B,                   # cmp eax,11 (plus)
        0x74,0x06,                        # je adjust
        0x5E,                              # pop esi
        0xE9,0,0,0,0,                    # jmp stock AP41 handler
        0x50,                              # adjust: push control ID
        0xE8,0,0,0,0,                    # call reward swap (Capture in)
        0x8B,0xCE,                        # mov ecx,esi
        0xE8,0,0,0,0,                    # call stock AP41 handler
        0xE8,0,0,0,0,                    # call reward swap (Capture out)
        0x8B,0x0D,0xF0,0x12,0x7C,0x00,   # mov ecx,[flag-mode manager]
        0xE8,0,0,0,0,                    # call GetFlagModeManager
        0x8B,0xC8,                        # mov ecx,eax
        0xE8,0,0,0,0,                    # call GetSelectedFlagMode
        0x3D,0x5A,0x43,0x46,0x30,         # cmp eax,"ZCF0"
        0x75,0x2E,                        # jne done
        0xFF,0x35,0,0,0,0,               # push [CaptureRewardAmount]
        0x68,0x5A,0x43,0x46,0x30,         # push "ZCF0"
        0x8B,0x0D,0xF0,0x12,0x7C,0x00,   # mov ecx,[flag-mode manager]
        0xE8,0,0,0,0,                    # call stock SetFlagMode
        0xEB,0x16,                        # jmp done
        0xFF,0x35,0,0,0,0,               # direct: push [CaptureRewardAmount]
        0x68,0x5A,0x43,0x46,0x30,         # push "ZCF0"
        0x8B,0x0D,0xF0,0x12,0x7C,0x00,   # mov ecx,[flag-mode manager]
        0xE8,0,0,0,0,                    # call capacity-gated Capture arm
        0x33,0xC0,                        # done: xor eax,eax
        0x5E,                              # pop esi
        0xC2,0x04,0x00                    # ret 4
    )
    if ($handler.Length -ne 0x7D) { throw "Private Capture reward handler changed length." }
    Write-Bytes $handler 0x19 (New-RelativeInstruction 0xE9 ([uint32]($HandlerVa + 0x19)) $StockAp41HandlerVa)
    Write-Bytes $handler 0x1F (New-RelativeInstruction 0xE8 ([uint32]($HandlerVa + 0x1F)) $RewardSwapVa)
    Write-Bytes $handler 0x26 (New-RelativeInstruction 0xE8 ([uint32]($HandlerVa + 0x26)) $StockAp41HandlerVa)
    Write-Bytes $handler 0x2B (New-RelativeInstruction 0xE8 ([uint32]($HandlerVa + 0x2B)) $RewardSwapVa)
    Write-Bytes $handler 0x36 (New-RelativeInstruction 0xE8 ([uint32]($HandlerVa + 0x36)) $GetFlagModeManagerVa)
    Write-Bytes $handler 0x3D (New-RelativeInstruction 0xE8 ([uint32]($HandlerVa + 0x3D)) $GetSelectedFlagModeVa)
    [BitConverter]::GetBytes($CaptureRewardAmountVa).CopyTo($handler, 0x4B)
    Write-Bytes $handler 0x5A (New-RelativeInstruction 0xE8 ([uint32]($HandlerVa + 0x5A)) $SetFlagModeVa)
    [BitConverter]::GetBytes($CaptureRewardAmountVa).CopyTo($handler, 0x63)
    Write-Bytes $handler 0x72 (New-RelativeInstruction 0xE8 ([uint32]($HandlerVa + 0x72)) $CaptureArmVa)
    foreach ($offset in @(0x32, 0x56, 0x6E)) {
        [BitConverter]::GetBytes([uint32]$FlagModeOwnerVa).CopyTo($handler, $offset)
    }
    $handler
}

function New-CapacityArmWrapper {
    param([uint32]$WrapperVa, [uint32]$CaptureZooSlotVa, [bool]$UsePanelController)
    # The direct Capture command is entered while its owning Zoo is selected.
    # Remember that stock selection, then tail-call the unchanged SetFlagMode.
    if ($UsePanelController) {
        # Literal AP41 sequence at 0x4A9246/0x4A9471: mov ecx,esi; call
        # 0x467540. ESI is the reward-panel controller saved by its handler.
        [byte[]]$wrapper = @(
            0x51,                          # push ecx (flag manager)
            0x8B,0xCE,                    # mov ecx,esi (AP41 controller)
            0xE8,0,0,0,0,                 # call selected-agent getter
            0xA3,0,0,0,0,                 # mov [CaptureZooSlot],eax
            0x59,                          # pop ecx (flag manager)
            0xE9,0,0,0,0                  # jmp stock SetFlagMode
        )
        Write-Bytes $wrapper 0x03 (New-RelativeInstruction 0xE8 ([uint32]($WrapperVa + 0x03)) $GetSelectedAgentVa)
        [BitConverter]::GetBytes($CaptureZooSlotVa).CopyTo($wrapper, 0x09)
        Write-Bytes $wrapper 0x0E (New-RelativeInstruction 0xE9 ([uint32]($WrapperVa + 0x0E)) $SetFlagModeVa)
    }
    else {
        # Upgrade-only fingerprint for the broken version-6 arm wrapper, which
        # incorrectly passed the flag manager as this to 0x467540.
        [byte[]]$wrapper = @(
            0x51,0xE8,0,0,0,0,0xA3,0,0,0,0,0x59,0xE9,0,0,0,0
        )
        Write-Bytes $wrapper 0x01 (New-RelativeInstruction 0xE8 ([uint32]($WrapperVa + 0x01)) $GetSelectedAgentVa)
        [BitConverter]::GetBytes($CaptureZooSlotVa).CopyTo($wrapper, 0x07)
        Write-Bytes $wrapper 0x0C (New-RelativeInstruction 0xE9 ([uint32]($WrapperVa + 0x0C)) $SetFlagModeVa)
    }
    $wrapper
}

function New-AlertingCapacityArmWrapperV11 {
    param(
        [uint32]$WrapperVa,
        [uint32]$CaptureZooSlotVa,
        [uint32]$AttributeGetterVa,
        [uint32]$ZooFullAlertVa
    )
    # Preserve the stock AP41 selected-building lookup and SetFlagMode handoff.
    # If that completed Zoo currently reports no legal capacity, stop before
    # arming placement and post the same native system alert lifecycle used by
    # stock placement failures. The completion check repeats the gate for the
    # narrow race where capacity changes after the cursor was armed.
    [byte[]]$wrapper = @(
        0x51,                              # push ecx (flag manager)
        0x8B,0xCE,                        # mov ecx,esi (AP41 controller)
        0xE8,0,0,0,0,                    # call selected-agent getter
        0xA3,0,0,0,0,                    # mov [CaptureZooSlot],eax
        0x85,0xC0,                        # test eax,eax
        0x74,0x18,                        # je full
        0x8B,0xC8,                        # mov ecx,eax (selected Zoo)
        0x6A,0x00,                        # push 0 (attribute default)
        0x68,0,0,0,0,                    # push ATTRIB_Zoo_Legal_Target
        0xE8,0,0,0,0,                    # call stock attribute getter
        0x85,0xC0,                        # test eax,eax
        0x74,0x06,                        # je full
        0x59,                              # pop ecx (flag manager)
        0xE9,0,0,0,0,                    # jmp stock SetFlagMode
        0x59,                              # full: pop ecx
        0xE8,0,0,0,0,                    # call native Zoo-full alert
        0xC3                              # ret to private panel handler
    )
    if ($wrapper.Length -ne 0x30) { throw "Alerting capacity arm wrapper changed length." }
    Write-Bytes $wrapper 0x03 (New-RelativeInstruction 0xE8 ([uint32]($WrapperVa + 0x03)) $GetSelectedAgentVa)
    [BitConverter]::GetBytes($CaptureZooSlotVa).CopyTo($wrapper, 0x09)
    [BitConverter]::GetBytes([uint32]$AttribZooLegalTarget).CopyTo($wrapper, 0x16)
    Write-Bytes $wrapper 0x1A (New-RelativeInstruction 0xE8 ([uint32]($WrapperVa + 0x1A)) $AttributeGetterVa)
    Write-Bytes $wrapper 0x24 (New-RelativeInstruction 0xE9 ([uint32]($WrapperVa + 0x24)) $SetFlagModeVa)
    Write-Bytes $wrapper 0x2A (New-RelativeInstruction 0xE8 ([uint32]($WrapperVa + 0x2A)) $ZooFullAlertVa)
    $wrapper
}

function New-AlertingCapacityArmWrapper {
    param(
        [uint32]$WrapperVa,
        [uint32]$CaptureZooSlotVa,
        [uint32]$AttributeGetterVa,
        [uint32]$ZooFullAlertVa
    )
    # SetFlagMode is a thiscall whose RET 8 consumes the mode and reward
    # arguments already pushed by the private panel handler. The full branch
    # bypasses that stock callee, so it must perform the identical RET 8 before
    # the handler restores its saved registers.
    [byte[]]$wrapper = @(
        0x51,
        0x8B,0xCE,
        0xE8,0,0,0,0,
        0xA3,0,0,0,0,
        0x85,0xC0,
        0x74,0x18,
        0x8B,0xC8,
        0x6A,0x00,
        0x68,0,0,0,0,
        0xE8,0,0,0,0,
        0x85,0xC0,
        0x74,0x06,
        0x59,
        0xE9,0,0,0,0,
        0x59,
        0xE8,0,0,0,0,
        0xC2,0x08,0x00                   # ret 8: match stock SetFlagMode
    )
    if ($wrapper.Length -ne 0x32) { throw "Alerting capacity arm wrapper changed length." }
    Write-Bytes $wrapper 0x03 (New-RelativeInstruction 0xE8 ([uint32]($WrapperVa + 0x03)) $GetSelectedAgentVa)
    [BitConverter]::GetBytes($CaptureZooSlotVa).CopyTo($wrapper, 0x09)
    [BitConverter]::GetBytes([uint32]$AttribZooLegalTarget).CopyTo($wrapper, 0x16)
    Write-Bytes $wrapper 0x1A (New-RelativeInstruction 0xE8 ([uint32]($WrapperVa + 0x1A)) $AttributeGetterVa)
    Write-Bytes $wrapper 0x24 (New-RelativeInstruction 0xE9 ([uint32]($WrapperVa + 0x24)) $SetFlagModeVa)
    Write-Bytes $wrapper 0x2A (New-RelativeInstruction 0xE8 ([uint32]($WrapperVa + 0x2A)) $ZooFullAlertVa)
    $wrapper
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
    param(
        [byte[]]$Bytes,
        [uint32]$CallbackVa,
        [uint32]$PrototypeNameVa,
        [uint32]$TargetCheckVa
    )
    [byte[]]$callback = $Bytes[$StockCaptureCallbackOffset..($StockCaptureCallbackOffset + $StockCaptureCallbackLength - 1)]
    if (-not (Test-BytesEqual $callback 0xCF $StockCallbackCreateSignature)) {
        throw "Stock Attack Flag completion callback creation seam changed."
    }
    foreach ($item in $StockCaptureCallbackExternalCalls.GetEnumerator()) {
        $offset = [int]$item.Key
        if ($callback[$offset] -ne 0xE8) { throw ("Stock callback call changed at +0x{0:X}." -f $offset) }
        $stockRelative = [BitConverter]::ToInt32($callback, $offset + 1)
        $stockTarget = [uint32]([int64]$StockCaptureCallbackVa + $offset + 5 + $stockRelative)
        if ($stockTarget -ne [uint32]$item.Value) {
            throw ("Stock callback target changed at +0x{0:X}: expected 0x{1:X8}, found 0x{2:X8}." -f $offset, [uint32]$item.Value, $stockTarget)
        }
        $relocatedTarget = $(if ($offset -eq 0xAC) { $TargetCheckVa } else { [uint32]$item.Value })
        Write-Bytes $callback $offset (New-RelativeInstruction 0xE8 ([uint32]($CallbackVa + $offset)) $relocatedTarget)
    }
    [BitConverter]::GetBytes($PrototypeNameVa).CopyTo($callback, 0xD1)
    $callback
}

function New-CaptureModeRegistration {
    param(
        [byte[]]$Bytes,
        [uint32]$RegistrationVa,
        [uint32]$ValidatorVa,
        [uint32]$CallbackVa,
        [byte]$CursorSelector
    )
    [byte[]]$registration = $Bytes[$Fl00RegistrationOffset..($Fl00RegistrationOffset + $Fl00RegistrationLength - 1)]
    if ($registration[0] -ne 0x6A -or $registration[1] -ne 0x20 -or
        $registration[0x20] -ne 0x68 -or (Read-U32 $registration 0x21) -ne $StockCaptureCallbackVa -or
        $registration[0x25] -ne 0x68 -or (Read-U32 $registration 0x26) -ne $StockCaptureValidatorVa -or
        $registration[0x2E] -ne 0x6A -or $registration[0x2F] -ne 0x05 -or
        $registration[0x30] -ne 0x68 -or (Read-U32 $registration 0x31) -ne 0x30306C46) {
        throw "Stock Fl00 placement-mode registration changed."
    }
    # Preserve stock's leading `push 0x20` allocation exactly. Offset 0x14 is
    # the later `C7 44 24 18` stack-state marker, not the mode-object size.
    [BitConverter]::GetBytes([uint32]0x22).CopyTo($registration, 0x14)
    [BitConverter]::GetBytes($CallbackVa).CopyTo($registration, 0x21)
    [BitConverter]::GetBytes($ValidatorVa).CopyTo($registration, 0x26)
    [byte[]]$captureMode = @(0x5A,0x43,0x46,0x30) # ZCF0
    $captureMode.CopyTo($registration, 0x31)
    $registration[0x2F] = $CursorSelector
    Write-Bytes $registration 0x02 (New-RelativeInstruction 0xE8 ([uint32]($RegistrationVa + 0x02)) $OperatorNewVa)
    Write-Bytes $registration 0x37 (New-RelativeInstruction 0xE8 ([uint32]($RegistrationVa + 0x37)) $FlagModeConstructorVa)
    Write-Bytes $registration 0x44 (New-RelativeInstruction 0xE8 ([uint32]($RegistrationVa + 0x44)) $GetFlagModeRegistryVa)

    [byte[]]$result = New-Object byte[] ($Fl00RegistrationLength + $StockModeRegistryHook.Length + 5)
    $registration.CopyTo($result, 0)
    $StockModeRegistryHook.CopyTo($result, $Fl00RegistrationLength)
    $jumpOffset = $Fl00RegistrationLength + $StockModeRegistryHook.Length
    Write-Bytes $result $jumpOffset (New-RelativeInstruction 0xE9 ([uint32]($RegistrationVa + $jumpOffset)) $ModeRegistryResumeVa)
    $result
}

function New-UnsafeCaptureTargetValidator {
    param([uint32]$ValidatorVa)
    # Upgrade-only fingerprint for the first monster filter. It omitted the
    # stock placement mode's empty selected-target state and must never be used
    # by the current payload.
    [byte[]]$validator = @(
        0x56,                              # push esi
        0x8B,0x74,0x24,0x08,              # mov esi,[esp+8]
        0x56,                              # push esi
        0xE8,0,0,0,0,                     # call stock Fl00 validator
        0x83,0xC4,0x04,                   # add esp,4
        0x85,0xC0,                        # test eax,eax
        0x75,0x28,                        # jne done (preserve stock 1/2)
        0x8B,0xCE,                        # mov ecx,esi
        0xE8,0,0,0,0,                    # call placement-mode state getter
        0x8B,0x48,0x08,                   # mov ecx,[eax+8] (selected target)
        0x8B,0x81,0x90,0x00,0x00,0x00,   # mov eax,[ecx+90] (description)
        0x83,0x78,0x08,0x03,              # cmp dword ptr [eax+8],Character
        0x75,0x0D,                        # jne invalid
        0x51,                              # push ecx
        0xE8,0,0,0,0,                    # call stock display classifier
        0x83,0xC4,0x04,                   # add esp,4
        0x85,0xC0,                        # test eax,eax (OTHER == 0)
        0x74,0x05,                        # je done
        0xB8,0x01,0x00,0x00,0x00,        # invalid: mov eax,1
        0x5E,                              # done: pop esi
        0xC3                               # ret
    )
    if ($validator.Length -ne 0x3C) { throw "Unsafe Capture target validator fingerprint changed length." }
    Write-Bytes $validator 0x06 (New-RelativeInstruction 0xE8 ([uint32]($ValidatorVa + 0x06)) $StockCaptureValidatorVa)
    Write-Bytes $validator 0x14 (New-RelativeInstruction 0xE8 ([uint32]($ValidatorVa + 0x14)) $GetFlagModeStateVa)
    Write-Bytes $validator 0x29 (New-RelativeInstruction 0xE8 ([uint32]($ValidatorVa + 0x29)) $DisplayClassifierVa)
    $validator
}

function New-StateTargetCaptureTargetValidator {
    param([uint32]$ValidatorVa)
    # Upgrade-only fingerprint for the null-safe second filter. It read the
    # picker object from placement state +8 rather than the selected agent that
    # stock Fl00 stores on the placement mode at +60.
    [byte[]]$validator = @(
        0x56,                              # push esi
        0x8B,0x74,0x24,0x08,              # mov esi,[esp+8]
        0x56,                              # push esi
        0xE8,0,0,0,0,                     # call stock Fl00 validator
        0x83,0xC4,0x04,                   # add esp,4
        0x85,0xC0,                        # test eax,eax
        0x75,0x2A,                        # jne done (preserve stock 1/2)
        0x8B,0xCE,                        # mov ecx,esi
        0xE8,0,0,0,0,                    # call placement-mode state getter
        0x8B,0x48,0x08,                   # mov ecx,[eax+8] (selected target)
        0xE3,0x19,                        # jecxz invalid (empty placement state)
        0x8B,0x81,0x90,0x00,0x00,0x00,   # mov eax,[ecx+90] (description)
        0x83,0x78,0x08,0x03,              # cmp dword ptr [eax+8],Character
        0x75,0x0D,                        # jne invalid
        0x51,                              # push ecx
        0xE8,0,0,0,0,                    # call stock display classifier
        0x83,0xC4,0x04,                   # add esp,4
        0x85,0xC0,                        # test eax,eax (OTHER == 0)
        0x74,0x05,                        # je done
        0xB8,0x01,0x00,0x00,0x00,        # invalid: mov eax,1
        0x5E,                              # done: pop esi
        0xC3                               # ret
    )
    if ($validator.Length -ne 0x3E) { throw "State-target Capture validator fingerprint changed length." }
    Write-Bytes $validator 0x06 (New-RelativeInstruction 0xE8 ([uint32]($ValidatorVa + 0x06)) $StockCaptureValidatorVa)
    Write-Bytes $validator 0x14 (New-RelativeInstruction 0xE8 ([uint32]($ValidatorVa + 0x14)) $GetFlagModeStateVa)
    Write-Bytes $validator 0x2B (New-RelativeInstruction 0xE8 ([uint32]($ValidatorVa + 0x2B)) $DisplayClassifierVa)
    $validator
}

function New-ZeroCategoryCaptureTargetValidator {
    param([uint32]$ValidatorVa)
    # Preserve the complete stock Fl00 validator first. Its 0x45D2D0 target
    # check stores the selected agent at placement mode +60. Accept that agent
    # only when the display classifier returns 0 and its description registry
    # reports Character (3). This is retained only to recognize and upgrade the
    # failed version-3/version-4 payloads; live tracing proved monsters are 4.
    [byte[]]$validator = @(
        0x56,                              # push esi
        0x8B,0x74,0x24,0x08,              # mov esi,[esp+8]
        0x56,                              # push esi
        0xE8,0,0,0,0,                     # call stock Fl00 validator
        0x83,0xC4,0x04,                   # add esp,4
        0x85,0xC0,                        # test eax,eax
        0x75,0x26,                        # jne done (preserve stock 1/2)
        0x8B,0x8E,0x60,0x00,0x00,0x00,   # mov ecx,[esi+60] (selected agent)
        0xE3,0x19,                        # jecxz invalid (empty placement state)
        0x8B,0x81,0x90,0x00,0x00,0x00,   # mov eax,[ecx+90] (description)
        0x83,0x78,0x08,0x03,              # cmp dword ptr [eax+8],Character
        0x75,0x0D,                        # jne invalid
        0x51,                              # push ecx
        0xE8,0,0,0,0,                    # call stock display classifier
        0x83,0xC4,0x04,                   # add esp,4
        0x85,0xC0,                        # test eax,eax (OTHER == 0)
        0x74,0x05,                        # je done
        0xB8,0x01,0x00,0x00,0x00,        # invalid: mov eax,1
        0x5E,                              # done: pop esi
        0xC3                               # ret
    )
    if ($validator.Length -ne 0x3A) { throw "Private Capture target validator assembly changed length." }
    Write-Bytes $validator 0x06 (New-RelativeInstruction 0xE8 ([uint32]($ValidatorVa + 0x06)) $StockCaptureValidatorVa)
    Write-Bytes $validator 0x27 (New-RelativeInstruction 0xE8 ([uint32]($ValidatorVa + 0x27)) $DisplayClassifierVa)
    $validator
}

function New-ZeroCategoryCaptureCompletionTargetCheck {
    param([uint32]$TargetCheckVa)
    # The stock completion callback independently calls 0x45D2D0 and expects
    # either the selected-agent pointer or zero. Preserve that complete check,
    # then return its pointer only for category-0 Character agents. Retained
    # only as the failed version-4 upgrade fingerprint.
    [byte[]]$targetCheck = @(
        0x56,                              # push esi
        0x8B,0x44,0x24,0x0C,              # mov eax,[esp+0C] (stock arg 2)
        0x8B,0x4C,0x24,0x08,              # mov ecx,[esp+08] (placement mode)
        0x50,                              # push eax
        0x51,                              # push ecx
        0xE8,0,0,0,0,                     # call stock 0x45D2D0
        0x83,0xC4,0x08,                   # add esp,8
        0x85,0xC0,                        # test eax,eax
        0x74,0x1D,                        # je done
        0x8B,0xF0,                        # mov esi,eax (selected agent)
        0x8B,0x8E,0x90,0x00,0x00,0x00,   # mov ecx,[esi+90] (description)
        0x83,0x79,0x08,0x03,              # cmp dword ptr [ecx+8],Character
        0x75,0x11,                        # jne invalid
        0x56,                              # push esi
        0xE8,0,0,0,0,                    # call stock display classifier
        0x83,0xC4,0x04,                   # add esp,4
        0x85,0xC0,                        # test eax,eax (OTHER == 0)
        0x75,0x04,                        # jne invalid
        0x8B,0xC6,                        # mov eax,esi
        0x5E,                              # done: pop esi
        0xC3,                              # ret
        0x33,0xC0,                        # invalid: xor eax,eax
        0xEB,0xFA                         # jmp done
    )
    if ($targetCheck.Length -ne 0x3A) { throw "Private Capture completion target check changed length." }
    Write-Bytes $targetCheck 0x0B (New-RelativeInstruction 0xE8 ([uint32]($TargetCheckVa + 0x0B)) $StockFlagTargetCheckVa)
    Write-Bytes $targetCheck 0x26 (New-RelativeInstruction 0xE8 ([uint32]($TargetCheckVa + 0x26)) $DisplayClassifierVa)
    $targetCheck
}

function New-CaptureTargetValidator {
    param([uint32]$ValidatorVa)
    # Preserve the complete stock Fl00 validator first. Its 0x45D2D0 target
    # check stores the selected agent at placement mode +60. The stock display
    # classifier returns 4 for ordinary monsters; require that category plus
    # the stock structural Character (3) description subtype. Empty +60 maps
    # to stock invalid result 1.
    [byte[]]$validator = @(
        0x56,                              # push esi
        0x8B,0x74,0x24,0x08,              # mov esi,[esp+8]
        0x56,                              # push esi
        0xE8,0,0,0,0,                     # call stock Fl00 validator
        0x83,0xC4,0x04,                   # add esp,4
        0x85,0xC0,                        # test eax,eax
        0x75,0x27,                        # jne done (preserve stock 1/2)
        0x8B,0x8E,0x60,0x00,0x00,0x00,   # mov ecx,[esi+60] (selected agent)
        0xE3,0x1A,                        # jecxz invalid (empty placement state)
        0x8B,0x81,0x90,0x00,0x00,0x00,   # mov eax,[ecx+90] (description)
        0x83,0x78,0x08,0x03,              # cmp dword ptr [eax+8],Character
        0x75,0x0E,                        # jne invalid
        0x51,                              # push ecx
        0xE8,0,0,0,0,                    # call stock display classifier
        0x83,0xC4,0x04,                   # add esp,4
        0x83,0xF8,0x04,                   # cmp eax,4 (monster)
        0x74,0x05,                        # je done
        0xB8,0x01,0x00,0x00,0x00,        # invalid: mov eax,1
        0x5E,                              # done: pop esi
        0xC3                               # ret
    )
    if ($validator.Length -ne 0x3B) { throw "Private Capture target validator assembly changed length." }
    Write-Bytes $validator 0x06 (New-RelativeInstruction 0xE8 ([uint32]($ValidatorVa + 0x06)) $StockCaptureValidatorVa)
    Write-Bytes $validator 0x27 (New-RelativeInstruction 0xE8 ([uint32]($ValidatorVa + 0x27)) $DisplayClassifierVa)
    $validator
}

function New-CaptureCompletionTargetCheck {
    param([uint32]$TargetCheckVa)
    # Stock completion independently reacquires a selected-agent pointer. Call
    # that stock check first, then return its pointer only for category-4
    # Character agents, matching the hover validator exactly.
    [byte[]]$targetCheck = @(
        0x56,                              # push esi
        0x8B,0x44,0x24,0x0C,              # mov eax,[esp+0C] (stock arg 2)
        0x8B,0x4C,0x24,0x08,              # mov ecx,[esp+08] (placement mode)
        0x50,                              # push eax
        0x51,                              # push ecx
        0xE8,0,0,0,0,                     # call stock 0x45D2D0
        0x83,0xC4,0x08,                   # add esp,8
        0x85,0xC0,                        # test eax,eax
        0x74,0x1E,                        # je done
        0x8B,0xF0,                        # mov esi,eax (selected agent)
        0x8B,0x8E,0x90,0x00,0x00,0x00,   # mov ecx,[esi+90] (description)
        0x83,0x79,0x08,0x03,              # cmp dword ptr [ecx+8],Character
        0x75,0x12,                        # jne invalid
        0x56,                              # push esi
        0xE8,0,0,0,0,                    # call stock display classifier
        0x83,0xC4,0x04,                   # add esp,4
        0x83,0xF8,0x04,                   # cmp eax,4 (monster)
        0x75,0x04,                        # jne invalid
        0x8B,0xC6,                        # mov eax,esi
        0x5E,                              # done: pop esi
        0xC3,                              # ret
        0x33,0xC0,                        # invalid: xor eax,eax
        0xEB,0xFA                         # jmp done
    )
    if ($targetCheck.Length -ne 0x3B) { throw "Private Capture completion target check changed length." }
    Write-Bytes $targetCheck 0x0B (New-RelativeInstruction 0xE8 ([uint32]($TargetCheckVa + 0x0B)) $StockFlagTargetCheckVa)
    Write-Bytes $targetCheck 0x26 (New-RelativeInstruction 0xE8 ([uint32]($TargetCheckVa + 0x26)) $DisplayClassifierVa)
    $targetCheck
}

function New-CapacityCaptureTargetValidator {
    param([uint32]$ValidatorVa, [uint32]$CaptureZooSlotVa, [uint32]$AttributeGetterVa)
    # Extend the proven private monster gate with one preceding capacity test.
    # ATTRIB_Zoo_Legal_Target is refreshed by GPL whenever the selected Zoo's
    # Occupants/reservations or completed building level changes.
    [byte[]]$validator = @(
        0x56,                              # push esi
        0x8B,0x74,0x24,0x08,              # mov esi,[esp+8]
        0x56,                              # push esi
        0xE8,0,0,0,0,                     # call stock Fl00 validator
        0x83,0xC4,0x04,                   # add esp,4
        0x85,0xC0,                        # test eax,eax
        0x75,0x3F,                        # jne done (preserve stock 1/2)
        0x8B,0x0D,0,0,0,0,               # mov ecx,[CaptureZooSlot]
        0xE3,0x32,                        # jecxz invalid
        0x6A,0x00,                        # push 0 (attribute default)
        0x68,0,0,0,0,                    # push ATTRIB_Zoo_Legal_Target
        0xE8,0,0,0,0,                    # call stock attribute getter
        0x85,0xC0,                        # test eax,eax
        0x74,0x22,                        # je invalid (Zoo full)
        0x8B,0x8E,0x60,0x00,0x00,0x00,   # mov ecx,[esi+60] (selected agent)
        0xE3,0x1A,                        # jecxz invalid
        0x8B,0x81,0x90,0x00,0x00,0x00,   # mov eax,[ecx+90] (description)
        0x83,0x78,0x08,0x03,              # cmp dword ptr [eax+8],Character
        0x75,0x0E,                        # jne invalid
        0x51,                              # push ecx
        0xE8,0,0,0,0,                    # call stock display classifier
        0x83,0xC4,0x04,                   # add esp,4
        0x83,0xF8,0x04,                   # cmp eax,4 (monster)
        0x74,0x05,                        # je done
        0xB8,0x01,0x00,0x00,0x00,        # invalid: mov eax,1
        0x5E,                              # done: pop esi
        0xC3                               # ret
    )
    if ($validator.Length -ne 0x53) { throw "Capacity Capture target validator assembly changed length." }
    Write-Bytes $validator 0x06 (New-RelativeInstruction 0xE8 ([uint32]($ValidatorVa + 0x06)) $StockCaptureValidatorVa)
    [BitConverter]::GetBytes($CaptureZooSlotVa).CopyTo($validator, 0x14)
    [BitConverter]::GetBytes([uint32]$AttribZooLegalTarget).CopyTo($validator, 0x1D)
    Write-Bytes $validator 0x21 (New-RelativeInstruction 0xE8 ([uint32]($ValidatorVa + 0x21)) $AttributeGetterVa)
    Write-Bytes $validator 0x3F (New-RelativeInstruction 0xE8 ([uint32]($ValidatorVa + 0x3F)) $DisplayClassifierVa)
    $validator
}

function New-NormalizedCapacityCaptureTargetValidatorV12 {
    param([uint32]$ValidatorVa, [uint32]$CaptureZooSlotVa, [uint32]$AttributeGetterVa)
    # The classifier is a predicate here, not the placement result. Return the
    # stock validator's legal value 0 after category 4 matches so the cursor
    # renderer retains the selected Capture cursor over a valid Monster.
    [byte[]]$validator = @(
        0x56,                              # push esi
        0x8B,0x74,0x24,0x08,              # mov esi,[esp+8]
        0x56,                              # push esi
        0xE8,0,0,0,0,                     # call stock Fl00 validator
        0x83,0xC4,0x04,                   # add esp,4
        0x85,0xC0,                        # test eax,eax
        0x75,0x43,                        # jne done (preserve stock 1/2)
        0x8B,0x0D,0,0,0,0,               # mov ecx,[CaptureZooSlot]
        0xE3,0x36,                        # jecxz invalid
        0x6A,0x00,                        # push 0 (attribute default)
        0x68,0,0,0,0,                    # push ATTRIB_Zoo_Legal_Target
        0xE8,0,0,0,0,                    # call stock attribute getter
        0x85,0xC0,                        # test eax,eax
        0x74,0x26,                        # je invalid (Zoo full)
        0x8B,0x8E,0x60,0x00,0x00,0x00,   # mov ecx,[esi+60] (selected agent)
        0xE3,0x1E,                        # jecxz invalid
        0x8B,0x81,0x90,0x00,0x00,0x00,   # mov eax,[ecx+90] (description)
        0x83,0x78,0x08,0x03,              # cmp dword ptr [eax+8],Character
        0x75,0x12,                        # jne invalid
        0x51,                              # push ecx
        0xE8,0,0,0,0,                    # call stock display classifier
        0x83,0xC4,0x04,                   # add esp,4
        0x83,0xF8,0x04,                   # cmp eax,4 (monster)
        0x75,0x04,                        # jne invalid
        0x33,0xC0,                        # xor eax,eax (stock legal result)
        0xEB,0x05,                        # jmp done
        0xB8,0x01,0x00,0x00,0x00,        # invalid: mov eax,1
        0x5E,                              # done: pop esi
        0xC3                               # ret
    )
    if ($validator.Length -ne 0x57) { throw "Normalized capacity validator assembly changed length." }
    Write-Bytes $validator 0x06 (New-RelativeInstruction 0xE8 ([uint32]($ValidatorVa + 0x06)) $StockCaptureValidatorVa)
    [BitConverter]::GetBytes($CaptureZooSlotVa).CopyTo($validator, 0x14)
    [BitConverter]::GetBytes([uint32]$AttribZooLegalTarget).CopyTo($validator, 0x1D)
    Write-Bytes $validator 0x21 (New-RelativeInstruction 0xE8 ([uint32]($ValidatorVa + 0x21)) $AttributeGetterVa)
    Write-Bytes $validator 0x3F (New-RelativeInstruction 0xE8 ([uint32]($ValidatorVa + 0x3F)) $DisplayClassifierVa)
    $validator
}

function New-HostileCapacityCaptureTargetValidator {
    param([uint32]$ValidatorVa, [uint32]$CaptureZooSlotVa, [uint32]$AttributeGetterVa)
    # Preserve the proven capacity/category gate, then use the same unit vtable
    # method exposed by stock GetUnitPlayerNumber. Only Monster Player (7) may
    # receive a Capture Flag; controlled/charmed player units are invalid.
    [byte[]]$validator = @(
        0x56,                              # push esi
        0x8B,0x74,0x24,0x08,              # mov esi,[esp+8]
        0x56,                              # push esi
        0xE8,0,0,0,0,                     # call stock Fl00 validator
        0x83,0xC4,0x04,                   # add esp,4
        0x85,0xC0,                        # test eax,eax
        0x75,0x47,                        # jne done (preserve stock 1/2)
        0x8B,0x0D,0,0,0,0,               # mov ecx,[CaptureZooSlot]
        0xE3,0x3A,                        # jecxz invalid
        0x6A,0x00,                        # push 0 (attribute default)
        0x68,0,0,0,0,                    # push ATTRIB_Zoo_Legal_Target
        0xE8,0,0,0,0,                    # call stock attribute getter
        0x85,0xC0,                        # test eax,eax
        0x74,0x2A,                        # je invalid (Zoo full)
        0x8B,0x8E,0x60,0x00,0x00,0x00,   # mov ecx,[esi+60] (selected agent)
        0xE3,0x22,                        # jecxz invalid
        0x51,                              # push ecx
        0xE8,0,0,0,0,                    # call stock display classifier
        0x83,0xC4,0x04,                   # add esp,4
        0x83,0xF8,0x04,                   # cmp eax,4 (monster)
        0x75,0x14,                        # jne invalid
        0x8B,0x8E,0x60,0x00,0x00,0x00,   # mov ecx,[esi+60] (selected agent)
        0x8B,0x01,                        # mov eax,[ecx] (unit vtable)
        0xFF,0x50,0x1C,                   # call [eax+1C] (GetUnitPlayerNumber)
        0x83,0xF8,0x07,                   # cmp eax,Monster_Player
        0x75,0x04,                        # jne invalid
        0x33,0xC0,                        # xor eax,eax (stock legal result)
        0xEB,0x05,                        # jmp done
        0xB8,0x01,0x00,0x00,0x00,        # invalid: mov eax,1
        0x5E,                              # done: pop esi
        0xC3                               # ret
    )
    if ($validator.Length -ne 0x5B) { throw "Hostile capacity validator assembly changed length." }
    Write-Bytes $validator 0x06 (New-RelativeInstruction 0xE8 ([uint32]($ValidatorVa + 0x06)) $StockCaptureValidatorVa)
    [BitConverter]::GetBytes($CaptureZooSlotVa).CopyTo($validator, 0x14)
    [BitConverter]::GetBytes([uint32]$AttribZooLegalTarget).CopyTo($validator, 0x1D)
    Write-Bytes $validator 0x21 (New-RelativeInstruction 0xE8 ([uint32]($ValidatorVa + 0x21)) $AttributeGetterVa)
    Write-Bytes $validator 0x33 (New-RelativeInstruction 0xE8 ([uint32]($ValidatorVa + 0x33)) $DisplayClassifierVa)
    $validator
}

function New-PrivateCaptureTargetLegality {
    param([uint32]$HelperVa, [uint32]$CaptureRelation)
    # Stock Attack placement ends its target-side legality check by looking up
    # the attached ARA2 relation at target+0xA4.  A relation already owned by
    # the placing player rejects the target before reward deduction/creation.
    # Capture Flags are private to the player's Zoo and attach as ZCF0, so the
    # equivalent private test rejects any existing ZCF0 relation after keeping
    # the proven stock monster-category and current-ownership checks.
    #
    # Contract: ecx = non-null selected target; eax = 1 legal / 0 invalid.
    [byte[]]$helper = @(
        0x56,                              # push esi
        0x8B,0xF1,                        # mov esi,ecx
        0x56,                              # push esi
        0xE8,0,0,0,0,                    # call stock display classifier
        0x83,0xC4,0x04,                   # add esp,4
        0x83,0xF8,0x04,                   # cmp eax,4 (monster)
        0x75,0x27,                        # jne invalid
        0x8B,0xCE,                        # mov ecx,esi
        0x8B,0x01,                        # mov eax,[ecx] (unit vtable)
        0xFF,0x50,0x1C,                   # call [eax+1C] (GetUnitPlayerNumber)
        0x83,0xF8,0x07,                   # cmp eax,Monster_Player
        0x75,0x1B,                        # jne invalid
        0x6A,0x01,                        # push 1 (stock relation lookup mode)
        0x68,0,0,0,0,                    # push private ZCF0 attachment key
        0x8D,0x8E,0xA4,0x00,0x00,0x00,   # lea ecx,[esi+A4] (relations)
        0xE8,0,0,0,0,                    # call stock attached-relation lookup
        0x85,0xC0,                        # test eax,eax
        0x75,0x05,                        # jne invalid (Capture Flag exists)
        0x6A,0x01,                        # push 1
        0x58,                              # pop eax
        0x5E,                              # pop esi
        0xC3,                              # ret
        0x33,0xC0,                        # invalid: xor eax,eax
        0x5E,                              # pop esi
        0xC3                               # ret
    )
    if ($helper.Length -ne 0x3C) { throw "Private Capture target-legality helper changed length." }
    Write-Bytes $helper 0x04 (New-RelativeInstruction 0xE8 ([uint32]($HelperVa + 0x04)) $DisplayClassifierVa)
    [BitConverter]::GetBytes($CaptureRelation).CopyTo($helper, 0x20)
    Write-Bytes $helper 0x2A (New-RelativeInstruction 0xE8 ([uint32]($HelperVa + 0x2A)) $FindAttachedRelationVa)
    $helper
}

function New-DeduplicatedCaptureTargetValidator {
    param(
        [uint32]$ValidatorVa,
        [uint32]$CaptureZooSlotVa,
        [uint32]$AttributeGetterVa,
        [uint32]$TargetLegalityVa
    )
    # Preserve the complete stock Fl00 validator and capacity gate, then apply
    # the private ZCF0 form of stock's attached-ARA2 target test together with
    # the already-proven generic hostile-monster classification.
    [byte[]]$validator = @(
        0x56,                              # push esi
        0x8B,0x74,0x24,0x08,              # mov esi,[esp+8]
        0x56,                              # push esi
        0xE8,0,0,0,0,                    # call stock Fl00 validator
        0x83,0xC4,0x04,                   # add esp,4
        0x85,0xC0,                        # test eax,eax
        0x75,0x32,                        # jne done (preserve stock 1/2)
        0x8B,0x0D,0,0,0,0,               # mov ecx,[CaptureZooSlot]
        0xE3,0x25,                        # jecxz invalid
        0x6A,0x00,                        # push 0 (attribute default)
        0x68,0,0,0,0,                    # push ATTRIB_Zoo_Legal_Target
        0xE8,0,0,0,0,                    # call stock attribute getter
        0x85,0xC0,                        # test eax,eax
        0x74,0x15,                        # je invalid (Zoo full)
        0x8B,0x8E,0x60,0x00,0x00,0x00,   # mov ecx,[esi+60] (selected agent)
        0xE3,0x0D,                        # jecxz invalid
        0xE8,0,0,0,0,                    # call private target legality
        0x85,0xC0,                        # test eax,eax
        0x74,0x04,                        # je invalid
        0x33,0xC0,                        # xor eax,eax (stock legal result)
        0xEB,0x05,                        # jmp done
        0xB8,0x01,0x00,0x00,0x00,        # invalid: mov eax,1
        0x5E,                              # done: pop esi
        0xC3                               # ret
    )
    if ($validator.Length -ne 0x46) { throw "Deduplicated Capture validator assembly changed length." }
    Write-Bytes $validator 0x06 (New-RelativeInstruction 0xE8 ([uint32]($ValidatorVa + 0x06)) $StockCaptureValidatorVa)
    [BitConverter]::GetBytes($CaptureZooSlotVa).CopyTo($validator, 0x14)
    [BitConverter]::GetBytes([uint32]$AttribZooLegalTarget).CopyTo($validator, 0x1D)
    Write-Bytes $validator 0x21 (New-RelativeInstruction 0xE8 ([uint32]($ValidatorVa + 0x21)) $AttributeGetterVa)
    Write-Bytes $validator 0x32 (New-RelativeInstruction 0xE8 ([uint32]($ValidatorVa + 0x32)) $TargetLegalityVa)
    $validator
}

function New-CapacityCaptureCompletionTargetCheckV10 {
    param([uint32]$TargetCheckVa, [uint32]$CaptureZooSlotVa, [uint32]$AttributeGetterVa)
    # Previous capacity-gated completion check retained solely so an installed
    # checkpoint can be recognized and upgraded without weakening validation.
    [byte[]]$targetCheck = @(
        0x56,
        0x8B,0x44,0x24,0x0C,
        0x8B,0x4C,0x24,0x08,
        0x50,
        0x51,
        0xE8,0,0,0,0,
        0x83,0xC4,0x08,
        0x85,0xC0,
        0x74,0x36,
        0x8B,0xF0,
        0x8B,0x0D,0,0,0,0,
        0xE3,0x2E,
        0x6A,0x00,
        0x68,0,0,0,0,
        0xE8,0,0,0,0,
        0x85,0xC0,
        0x74,0x1E,
        0x8B,0x8E,0x90,0x00,0x00,0x00,
        0x83,0x79,0x08,0x03,
        0x75,0x12,
        0x56,
        0xE8,0,0,0,0,
        0x83,0xC4,0x04,
        0x83,0xF8,0x04,
        0x75,0x04,
        0x8B,0xC6,
        0x5E,
        0xC3,
        0x33,0xC0,
        0xEB,0xFA
    )
    if ($targetCheck.Length -ne 0x53) { throw "V10 capacity completion check changed length." }
    Write-Bytes $targetCheck 0x0B (New-RelativeInstruction 0xE8 ([uint32]($TargetCheckVa + 0x0B)) $StockFlagTargetCheckVa)
    [BitConverter]::GetBytes($CaptureZooSlotVa).CopyTo($targetCheck, 0x1B)
    [BitConverter]::GetBytes([uint32]$AttribZooLegalTarget).CopyTo($targetCheck, 0x24)
    Write-Bytes $targetCheck 0x28 (New-RelativeInstruction 0xE8 ([uint32]($TargetCheckVa + 0x28)) $AttributeGetterVa)
    Write-Bytes $targetCheck 0x3E (New-RelativeInstruction 0xE8 ([uint32]($TargetCheckVa + 0x3E)) $DisplayClassifierVa)
    $targetCheck
}

function New-CapacityCaptureCompletionTargetCheckV12 {
    param(
        [uint32]$TargetCheckVa,
        [uint32]$CaptureZooSlotVa,
        [uint32]$AttributeGetterVa,
        [uint32]$ZooFullAlertVa
    )
    # Stock completion independently reacquires and authorizes its target. Apply
    # the same selected-Zoo capacity gate here so a full Zoo cannot race a click.
    [byte[]]$targetCheck = @(
        0x56,                              # push esi
        0x8B,0x44,0x24,0x0C,              # mov eax,[esp+0C] (stock arg 2)
        0x8B,0x4C,0x24,0x08,              # mov ecx,[esp+08] (placement mode)
        0x50,                              # push eax
        0x51,                              # push ecx
        0xE8,0,0,0,0,                     # call stock 0x45D2D0
        0x83,0xC4,0x08,                   # add esp,8
        0x85,0xC0,                        # test eax,eax
        0x74,0x36,                        # je done
        0x8B,0xF0,                        # mov esi,eax (selected agent)
        0x8B,0x0D,0,0,0,0,               # mov ecx,[CaptureZooSlot]
        0xE3,0x2E,                        # jecxz invalid
        0x6A,0x00,                        # push 0 (attribute default)
        0x68,0,0,0,0,                    # push ATTRIB_Zoo_Legal_Target
        0xE8,0,0,0,0,                    # call stock attribute getter
        0x85,0xC0,                        # test eax,eax
        0x74,0x22,                        # je full (Zoo full)
        0x8B,0x8E,0x90,0x00,0x00,0x00,   # mov ecx,[esi+90] (description)
        0x83,0x79,0x08,0x03,              # cmp dword ptr [ecx+8],Character
        0x75,0x12,                        # jne invalid
        0x56,                              # push esi
        0xE8,0,0,0,0,                    # call stock display classifier
        0x83,0xC4,0x04,                   # add esp,4
        0x83,0xF8,0x04,                   # cmp eax,4 (monster)
        0x75,0x04,                        # jne invalid
        0x8B,0xC6,                        # mov eax,esi
        0x5E,                              # done: pop esi
        0xC3,                              # ret
        0x33,0xC0,                        # invalid: xor eax,eax
        0xEB,0xFA,                        # jmp done
        0xE8,0,0,0,0,                    # full: post native full-Zoo alert
        0xEB,0xF5                         # jmp invalid
    )
    if ($targetCheck.Length -ne 0x5A) { throw "Capacity Capture completion target check changed length." }
    Write-Bytes $targetCheck 0x0B (New-RelativeInstruction 0xE8 ([uint32]($TargetCheckVa + 0x0B)) $StockFlagTargetCheckVa)
    [BitConverter]::GetBytes($CaptureZooSlotVa).CopyTo($targetCheck, 0x1B)
    [BitConverter]::GetBytes([uint32]$AttribZooLegalTarget).CopyTo($targetCheck, 0x24)
    Write-Bytes $targetCheck 0x28 (New-RelativeInstruction 0xE8 ([uint32]($TargetCheckVa + 0x28)) $AttributeGetterVa)
    Write-Bytes $targetCheck 0x3E (New-RelativeInstruction 0xE8 ([uint32]($TargetCheckVa + 0x3E)) $DisplayClassifierVa)
    Write-Bytes $targetCheck 0x53 (New-RelativeInstruction 0xE8 ([uint32]($TargetCheckVa + 0x53)) $ZooFullAlertVa)
    $targetCheck
}

function New-HostileCapacityCaptureCompletionTargetCheck {
    param(
        [uint32]$TargetCheckVa,
        [uint32]$CaptureZooSlotVa,
        [uint32]$AttributeGetterVa,
        [uint32]$ZooFullAlertVa
    )
    # Repeat hover validation at click completion, including current stock unit
    # ownership. This prevents a target charmed between hover and placement.
    [byte[]]$targetCheck = @(
        0x56,                              # push esi
        0x8B,0x44,0x24,0x0C,              # mov eax,[esp+0C] (stock arg 2)
        0x8B,0x4C,0x24,0x08,              # mov ecx,[esp+08] (placement mode)
        0x50,                              # push eax
        0x51,                              # push ecx
        0xE8,0,0,0,0,                     # call stock 0x45D2D0
        0x83,0xC4,0x08,                   # add esp,8
        0x85,0xC0,                        # test eax,eax
        0x74,0x36,                        # je done
        0x8B,0xF0,                        # mov esi,eax (selected agent)
        0x8B,0x0D,0,0,0,0,               # mov ecx,[CaptureZooSlot]
        0xE3,0x2E,                        # jecxz invalid
        0x6A,0x00,                        # push 0 (attribute default)
        0x68,0,0,0,0,                    # push ATTRIB_Zoo_Legal_Target
        0xE8,0,0,0,0,                    # call stock attribute getter
        0x85,0xC0,                        # test eax,eax
        0x74,0x22,                        # je full (Zoo full)
        0x56,                              # push esi
        0xE8,0,0,0,0,                    # call stock display classifier
        0x83,0xC4,0x04,                   # add esp,4
        0x83,0xF8,0x04,                   # cmp eax,4 (monster)
        0x75,0x10,                        # jne invalid
        0x8B,0xCE,                        # mov ecx,esi
        0x8B,0x01,                        # mov eax,[ecx] (unit vtable)
        0xFF,0x50,0x1C,                   # call [eax+1C] (GetUnitPlayerNumber)
        0x83,0xF8,0x07,                   # cmp eax,Monster_Player
        0x75,0x04,                        # jne invalid
        0x8B,0xC6,                        # mov eax,esi
        0x5E,                              # done: pop esi
        0xC3,                              # ret
        0x33,0xC0,                        # invalid: xor eax,eax
        0xEB,0xFA,                        # jmp done
        0xE8,0,0,0,0,                    # full: post native full-Zoo alert
        0xEB,0xF5                         # jmp invalid
    )
    if ($targetCheck.Length -ne 0x5A) { throw "Hostile capacity completion check changed length." }
    Write-Bytes $targetCheck 0x0B (New-RelativeInstruction 0xE8 ([uint32]($TargetCheckVa + 0x0B)) $StockFlagTargetCheckVa)
    [BitConverter]::GetBytes($CaptureZooSlotVa).CopyTo($targetCheck, 0x1B)
    [BitConverter]::GetBytes([uint32]$AttribZooLegalTarget).CopyTo($targetCheck, 0x24)
    Write-Bytes $targetCheck 0x28 (New-RelativeInstruction 0xE8 ([uint32]($TargetCheckVa + 0x28)) $AttributeGetterVa)
    Write-Bytes $targetCheck 0x32 (New-RelativeInstruction 0xE8 ([uint32]($TargetCheckVa + 0x32)) $DisplayClassifierVa)
    Write-Bytes $targetCheck 0x53 (New-RelativeInstruction 0xE8 ([uint32]($TargetCheckVa + 0x53)) $ZooFullAlertVa)
    $targetCheck
}

function New-DeduplicatedCaptureCompletionTargetCheck {
    param(
        [uint32]$TargetCheckVa,
        [uint32]$CaptureZooSlotVa,
        [uint32]$AttributeGetterVa,
        [uint32]$ZooFullAlertVa,
        [uint32]$TargetLegalityVa
    )
    # Stock completion independently reacquires its target. Repeat the private
    # ZCF0 relation check here so a second Capture Flag cannot race through
    # after hover validation, and retain the existing capacity-race alert.
    [byte[]]$targetCheck = @(
        0x56,                              # push esi
        0x8B,0x44,0x24,0x0C,              # mov eax,[esp+0C] (stock arg 2)
        0x8B,0x4C,0x24,0x08,              # mov ecx,[esp+08] (placement mode)
        0x50,                              # push eax
        0x51,                              # push ecx
        0xE8,0,0,0,0,                    # call stock 0x45D2D0
        0x83,0xC4,0x08,                   # add esp,8
        0x85,0xC0,                        # test eax,eax
        0x74,0x27,                        # je done
        0x8B,0xF0,                        # mov esi,eax (selected agent)
        0x8B,0x0D,0,0,0,0,               # mov ecx,[CaptureZooSlot]
        0xE3,0x1F,                        # jecxz invalid
        0x6A,0x00,                        # push 0 (attribute default)
        0x68,0,0,0,0,                    # push ATTRIB_Zoo_Legal_Target
        0xE8,0,0,0,0,                    # call stock attribute getter
        0x85,0xC0,                        # test eax,eax
        0x74,0x13,                        # je full (Zoo full)
        0x8B,0xCE,                        # mov ecx,esi
        0xE8,0,0,0,0,                    # call private target legality
        0x85,0xC0,                        # test eax,eax
        0x74,0x04,                        # je invalid
        0x8B,0xC6,                        # mov eax,esi
        0x5E,                              # done: pop esi
        0xC3,                              # ret
        0x33,0xC0,                        # invalid: xor eax,eax
        0xEB,0xFA,                        # jmp done
        0xE8,0,0,0,0,                    # full: post native full-Zoo alert
        0xEB,0xF5                         # jmp invalid
    )
    if ($targetCheck.Length -ne 0x4B) { throw "Deduplicated Capture completion check changed length." }
    Write-Bytes $targetCheck 0x0B (New-RelativeInstruction 0xE8 ([uint32]($TargetCheckVa + 0x0B)) $StockFlagTargetCheckVa)
    [BitConverter]::GetBytes($CaptureZooSlotVa).CopyTo($targetCheck, 0x1B)
    [BitConverter]::GetBytes([uint32]$AttribZooLegalTarget).CopyTo($targetCheck, 0x24)
    Write-Bytes $targetCheck 0x28 (New-RelativeInstruction 0xE8 ([uint32]($TargetCheckVa + 0x28)) $AttributeGetterVa)
    Write-Bytes $targetCheck 0x33 (New-RelativeInstruction 0xE8 ([uint32]($TargetCheckVa + 0x33)) $TargetLegalityVa)
    Write-Bytes $targetCheck 0x44 (New-RelativeInstruction 0xE8 ([uint32]($TargetCheckVa + 0x44)) $ZooFullAlertVa)
    $targetCheck
}

function New-ZooFullAlert {
    param([uint32]$AlertVa, [uint32]$AlertTextVa)
    # Literal stock system-alert lifecycle used by placement failures:
    # select the standard alert presentation, construct the engine string from
    # a literal, post it globally, and let the shipped helper destroy it.
    [byte[]]$alert = @(
        0x8B,0x0D,0,0,0,0,               # mov ecx,[system alert owner]
        0x6A,0xFF,                        # push 255
        0x68,0x00,0xFF,0x00,0x80,         # push stock alert color
        0x6A,0x01,                        # push 1
        0xE8,0,0,0,0,                    # call stock alert presentation
        0x6A,0x01,                        # push 1
        0x6A,0xFF,                        # push -1 (global alert)
        0x68,0,0,0,0,                    # push literal text
        0xE8,0,0,0,0,                    # call stock literal-string alert helper
        0x83,0xC4,0x0C,                  # add esp,12
        0xC3                              # ret
    )
    if ($alert.Length -ne 0x26) { throw "Zoo-full alert assembly changed length." }
    [BitConverter]::GetBytes([uint32]$SystemAlertOwnerVa).CopyTo($alert, 0x02)
    Write-Bytes $alert 0x0F (New-RelativeInstruction 0xE8 ([uint32]($AlertVa + 0x0F)) $PrepareSystemAlertVa)
    [BitConverter]::GetBytes($AlertTextVa).CopyTo($alert, 0x19)
    Write-Bytes $alert 0x1D (New-RelativeInstruction 0xE8 ([uint32]($AlertVa + 0x1D)) $PostLiteralSystemAlertVa)
    $alert
}

function New-PatchBlob {
    param(
        [byte[]]$Bytes,
        [uint32]$PatchVa,
        [byte]$CursorSelector,
        [int]$CaptureTargetValidatorVersion,
        [uint32]$CapacitySlotVa = 0
    )
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

    $captureTargetValidatorVa = [uint32]($PatchVa + $CaptureTargetValidatorOffset)
    $privateCaptureTargetLegalityVa = [uint32]($PatchVa + $PrivateCaptureTargetLegalityOffset)
    $selectedRewardSwapOffset = $(if ($CaptureTargetValidatorVersion -ge 17) { $PrivateRewardSwapV17Offset } else { $PrivateRewardSwapOffset })
    $selectedActivationOffset = $(if ($CaptureTargetValidatorVersion -ge 17) { $PrivateActivationV17Offset } else { $PrivateActivationOffset })
    $privateRewardSwapVa = [uint32]($PatchVa + $selectedRewardSwapOffset)
    $privateActivationVa = [uint32]($PatchVa + $selectedActivationOffset)
    $privateRefreshVa = [uint32]($PatchVa + $PrivateRefreshV17Offset)
    $capacityTargetValidatorVa = [uint32]($PatchVa + $CapacityTargetValidatorOffset)
    $capacityCompletionTargetCheckVa = [uint32]($PatchVa + $CapacityCompletionTargetCheckOffset)
    $capacityArmWrapperVa = [uint32]($PatchVa + $CapacityArmWrapperOffset)
    $zooFullAlertOffset = $(if ($CaptureTargetValidatorVersion -ge 12) { $ZooFullAlertOffset } else { $BuggyZooFullAlertOffset })
    $zooFullAlertTextOffset = $(if ($CaptureTargetValidatorVersion -ge 12) { $ZooFullAlertTextOffset } else { $BuggyZooFullAlertTextOffset })
    $zooFullAlertVa = [uint32]($PatchVa + $zooFullAlertOffset)
    $zooFullAlertTextVa = [uint32]($PatchVa + $zooFullAlertTextOffset)
    $captureZooSlotVa = $(if ($CaptureTargetValidatorVersion -ge 8) { $CapacitySlotVa } else { [uint32]($PatchVa + $LegacyCaptureZooSlotOffset) })
    $captureRewardAmountVa = [uint32]($captureZooSlotVa + 4)
    $attributeGetterVa = $(if ($CaptureTargetValidatorVersion -ge 9) { $GetAttributeVa } else { $BadGetAttributeVa })
    if ($CaptureTargetValidatorVersion -ge 6) {
        if ($CaptureTargetValidatorVersion -ge 14) {
            $captureRelation = $(if ($CaptureTargetValidatorVersion -ge 15) { [uint32]$CaptureFlagDescriptionRelation } else { [uint32]$CaptureFlagArtRelation })
            Write-Bytes $blob $PrivateCaptureTargetLegalityOffset (New-PrivateCaptureTargetLegality $privateCaptureTargetLegalityVa $captureRelation)
            Write-Bytes $blob $CapacityTargetValidatorOffset (New-DeduplicatedCaptureTargetValidator $capacityTargetValidatorVa $captureZooSlotVa $attributeGetterVa $privateCaptureTargetLegalityVa)
        }
        elseif ($CaptureTargetValidatorVersion -ge 13) {
            Write-Bytes $blob $CapacityTargetValidatorOffset (New-HostileCapacityCaptureTargetValidator $capacityTargetValidatorVa $captureZooSlotVa $attributeGetterVa)
        }
        elseif ($CaptureTargetValidatorVersion -ge 10) {
            Write-Bytes $blob $CapacityTargetValidatorOffset (New-NormalizedCapacityCaptureTargetValidatorV12 $capacityTargetValidatorVa $captureZooSlotVa $attributeGetterVa)
        }
        else {
            Write-Bytes $blob $CapacityTargetValidatorOffset (New-CapacityCaptureTargetValidator $capacityTargetValidatorVa $captureZooSlotVa $attributeGetterVa)
        }
        if ($CaptureTargetValidatorVersion -ge 14) {
            Write-Bytes $blob $CapacityCompletionTargetCheckOffset (New-DeduplicatedCaptureCompletionTargetCheck $capacityCompletionTargetCheckVa $captureZooSlotVa $attributeGetterVa $zooFullAlertVa $privateCaptureTargetLegalityVa)
            Write-Bytes $blob $zooFullAlertOffset (New-ZooFullAlert $zooFullAlertVa $zooFullAlertTextVa)
            [Text.Encoding]::ASCII.GetBytes("Couldn't place reward flag, Zoo is full.`0").CopyTo($blob, $zooFullAlertTextOffset)
        }
        elseif ($CaptureTargetValidatorVersion -ge 13) {
            Write-Bytes $blob $CapacityCompletionTargetCheckOffset (New-HostileCapacityCaptureCompletionTargetCheck $capacityCompletionTargetCheckVa $captureZooSlotVa $attributeGetterVa $zooFullAlertVa)
            Write-Bytes $blob $zooFullAlertOffset (New-ZooFullAlert $zooFullAlertVa $zooFullAlertTextVa)
            [Text.Encoding]::ASCII.GetBytes("Couldn't place reward flag, Zoo is full.`0").CopyTo($blob, $zooFullAlertTextOffset)
        }
        elseif ($CaptureTargetValidatorVersion -ge 11) {
            Write-Bytes $blob $CapacityCompletionTargetCheckOffset (New-CapacityCaptureCompletionTargetCheckV12 $capacityCompletionTargetCheckVa $captureZooSlotVa $attributeGetterVa $zooFullAlertVa)
            Write-Bytes $blob $zooFullAlertOffset (New-ZooFullAlert $zooFullAlertVa $zooFullAlertTextVa)
            [Text.Encoding]::ASCII.GetBytes("Couldn't place reward flag, Zoo is full.`0").CopyTo($blob, $zooFullAlertTextOffset)
        }
        else {
            Write-Bytes $blob $CapacityCompletionTargetCheckOffset (New-CapacityCaptureCompletionTargetCheckV10 $capacityCompletionTargetCheckVa $captureZooSlotVa $attributeGetterVa)
        }
        if ($CaptureTargetValidatorVersion -ge 12) {
            Write-Bytes $blob $CapacityArmWrapperOffset (New-AlertingCapacityArmWrapper $capacityArmWrapperVa $captureZooSlotVa $attributeGetterVa $zooFullAlertVa)
        }
        elseif ($CaptureTargetValidatorVersion -eq 11) {
            Write-Bytes $blob $CapacityArmWrapperOffset (New-AlertingCapacityArmWrapperV11 $capacityArmWrapperVa $captureZooSlotVa $attributeGetterVa $zooFullAlertVa)
        }
        else {
            Write-Bytes $blob $CapacityArmWrapperOffset (New-CapacityArmWrapper $capacityArmWrapperVa $captureZooSlotVa ($CaptureTargetValidatorVersion -ge 7))
        }
    }
    elseif ($CaptureTargetValidatorVersion -eq 5) {
        Write-Bytes $blob $CaptureTargetValidatorOffset (New-CaptureTargetValidator $captureTargetValidatorVa)
    }
    elseif ($CaptureTargetValidatorVersion -eq 4 -or $CaptureTargetValidatorVersion -eq 3) {
        Write-Bytes $blob $CaptureTargetValidatorOffset (New-ZeroCategoryCaptureTargetValidator $captureTargetValidatorVa)
    }
    elseif ($CaptureTargetValidatorVersion -eq 2) {
        Write-Bytes $blob $CaptureTargetValidatorOffset (New-StateTargetCaptureTargetValidator $captureTargetValidatorVa)
    }
    elseif ($CaptureTargetValidatorVersion -eq 1) {
        Write-Bytes $blob $CaptureTargetValidatorOffset (New-UnsafeCaptureTargetValidator $captureTargetValidatorVa)
    }
    elseif ($CaptureTargetValidatorVersion -ne 0) {
        throw "Unknown Capture target-validator payload version."
    }

    $handlerVa = [uint32]($PatchVa + $PrivateHandlerOffset)
    $vtableVa = [uint32]($PatchVa + $PrivateVtableOffset)
    Write-Bytes $blob $PrivateFactoryOffset (New-PrivateFactory ([uint32]($PatchVa + $PrivateFactoryOffset)) $vtableVa)
    $captureArmVa = $(if ($CaptureTargetValidatorVersion -ge 6) { $capacityArmWrapperVa } else { $SetFlagModeVa })
    if ($CaptureTargetValidatorVersion -ge 16) {
        Write-Bytes $blob $selectedRewardSwapOffset (New-PrivateRewardSwap $captureRewardAmountVa)
        Write-Bytes $blob $selectedActivationOffset (New-PrivateRewardActivation $privateActivationVa $privateRewardSwapVa)
        if ($CaptureTargetValidatorVersion -ge 17) {
            Write-Bytes $blob $PrivateRefreshV17Offset (New-PrivateRewardRefresh $privateRefreshVa $privateRewardSwapVa)
        }
        Write-Bytes $blob $PrivateHandlerOffset (New-PrivateRewardHandler $handlerVa $captureArmVa $captureRewardAmountVa $privateRewardSwapVa)
    }
    else {
        Write-Bytes $blob $PrivateHandlerOffset (New-PrivateHandler $handlerVa $captureArmVa)
    }

    [byte[]]$vtable = $Bytes[$StockAp41VtableOffset..($StockAp41VtableOffset + $StockAp41VtableLength - 1)]
    if ((Read-U32 $vtable 0x0C) -ne $StockAp41HandlerVa) { throw "Stock AP41 primary vtable changed." }
    [BitConverter]::GetBytes($handlerVa).CopyTo($vtable, 0x0C)
    if ($CaptureTargetValidatorVersion -ge 16) {
        if ((Read-U32 $vtable 0x04) -ne $StockAp41ActivationVa) { throw "Stock AP41 activation vtable entry changed." }
        [BitConverter]::GetBytes($privateActivationVa).CopyTo($vtable, 0x04)
        if ($CaptureTargetValidatorVersion -ge 17) {
            if ((Read-U32 $vtable 0x20) -ne $StockAp41RefreshVa) { throw "Stock AP41 refresh vtable entry changed." }
            [BitConverter]::GetBytes($privateRefreshVa).CopyTo($vtable, 0x20)
        }
    }
    Write-Bytes $blob $PrivateVtableOffset $vtable

    $registrationVa = [uint32]($PatchVa + $ModeRegistrationOffset)
    $callbackVa = [uint32]($PatchVa + $CaptureCallbackOffset)
    $prototypeNameVa = [uint32]($PatchVa + $CapturePrototypeNameOffset)
    $completionTargetCheckVa = [uint32]($PatchVa + $CaptureCompletionTargetCheckOffset)
    $validatorVa = $(if ($CaptureTargetValidatorVersion -ge 6) { $capacityTargetValidatorVa } elseif ($CaptureTargetValidatorVersion -ne 0) { $captureTargetValidatorVa } else { $StockCaptureValidatorVa })
    Write-Bytes $blob $ModeRegistrationOffset (New-CaptureModeRegistration $Bytes $registrationVa $validatorVa $callbackVa $CursorSelector)
    $callbackTargetCheckVa = $(if ($CaptureTargetValidatorVersion -ge 6) { $capacityCompletionTargetCheckVa } elseif ($CaptureTargetValidatorVersion -ge 4) { $completionTargetCheckVa } else { $StockFlagTargetCheckVa })
    Write-Bytes $blob $CaptureCallbackOffset (New-CaptureCallback $Bytes $callbackVa $prototypeNameVa $callbackTargetCheckVa)
    if ($CaptureTargetValidatorVersion -eq 5) {
        Write-Bytes $blob $CaptureCompletionTargetCheckOffset (New-CaptureCompletionTargetCheck $completionTargetCheckVa)
    }
    elseif ($CaptureTargetValidatorVersion -eq 4) {
        Write-Bytes $blob $CaptureCompletionTargetCheckOffset (New-ZeroCategoryCaptureCompletionTargetCheck $completionTargetCheckVa)
    }
    [Text.Encoding]::ASCII.GetBytes("Restore_Capture_Flag`0").CopyTo($blob, $CapturePrototypeNameOffset)
    [Text.Encoding]::ASCII.GetBytes("RestoreAbandonedZoo.ZC01.ZCF0").CopyTo($blob, 0x190)
    $blob
}

$resolvedGamePath = [IO.Path]::GetFullPath($GamePath)
$exePath = Join-Path $resolvedGamePath "MajestyHD.exe"
if (-not (Test-Path -LiteralPath $exePath -PathType Leaf)) { throw "Could not find MajestyHD.exe at $exePath." }
[byte[]]$bytes = [IO.File]::ReadAllBytes($exePath)
$pe = Get-PeInfo $bytes
$executableProfile = Get-ZooRewardDispatcherProfile $bytes
Use-ZooRewardDispatcherProfile $executableProfile
if (-not (Test-BytesEqual $bytes $PalaceHandlerOffset $PalaceHandlerSignature) -or
    -not (Test-BytesEqual $bytes $Ap41FactoryOffset $Ap41FactorySignature) -or
    -not (Test-BytesEqual $bytes $OpenDialogOffset $OpenDialogSignature) -or
    -not (Test-BytesEqual $bytes ($StockCaptureCallbackOffset + 0xCF) $StockCallbackCreateSignature)) {
    throw "MajestyHD.exe does not contain the recognized $ExecutableProfileId stock reward-panel and Attack Flag lifecycle."
}

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

$dataSection = $pe.Sections | Where-Object Name -eq $DataSectionName | Select-Object -First 1
$dataSectionIsNew = $null -eq $dataSection
if ($dataSectionIsNew) {
    $dataHeaderOffset = $pe.SectionTableOffset + (($pe.SectionCount + $(if ($sectionIsNew) { 1 } else { 0 })) * 40)
    if (($dataHeaderOffset + 40) -gt $pe.SizeOfHeaders) { throw "MajestyHD.exe has no room for the private Zoo data section header." }
    $dataRva = Align-Value ([uint32]($section.Rva + [Math]::Max($section.VirtualSize, $section.RawSize))) $pe.SectionAlignment
    $dataRawOffset = Align-Value ([uint32]($section.RawOffset + $PatchRawSize)) $pe.FileAlignment
    $dataSection = [pscustomobject]@{
        Index = $pe.SectionCount + $(if ($sectionIsNew) { 1 } else { 0 })
        HeaderOffset = $dataHeaderOffset; Name = $DataSectionName
        VirtualSize = $DataSectionVirtualSize; Rva = $dataRva
        RawSize = $DataSectionRawSize; RawOffset = $dataRawOffset
        Characteristics = $DataSectionCharacteristics
    }
}
elseif ($dataSection.Characteristics -ne $DataSectionCharacteristics -or
        $dataSection.RawSize -lt $DataSectionRawSize -or
        ($dataSection.RawOffset + $dataSection.RawSize) -gt $bytes.Length) {
    throw "MajestyHD.exe contains an incompatible .mzdt section."
}

$patchVa = [uint32]($pe.ImageBase + $section.Rva)
$captureZooSlotVa = [uint32]($pe.ImageBase + $dataSection.Rva)
[byte[]]$payload = New-PatchBlob $bytes $patchVa $CaptureCursorSelector 17 $captureZooSlotVa
[byte[]]$selector32Payload = New-PatchBlob $bytes $patchVa 0x20 17 $captureZooSlotVa
[byte[]]$staleRewardDisplayPayload = New-PatchBlob $bytes $patchVa $CaptureCursorSelector 16 $captureZooSlotVa
[byte[]]$sharedRewardPayload = New-PatchBlob $bytes $patchVa $CaptureCursorSelector 15 $captureZooSlotVa
[byte[]]$artRelationPayload = New-PatchBlob $bytes $patchVa $CaptureCursorSelector 14 $captureZooSlotVa
[byte[]]$duplicateBlindPayload = New-PatchBlob $bytes $patchVa $CaptureCursorSelector 13 $captureZooSlotVa
[byte[]]$ownershipBlindPayload = New-PatchBlob $bytes $patchVa $CaptureCursorSelector 12 $captureZooSlotVa
[byte[]]$uncleanAlertPayload = New-PatchBlob $bytes $patchVa $CaptureCursorSelector 11 $captureZooSlotVa
[byte[]]$silentCapacityPayload = New-PatchBlob $bytes $patchVa $CaptureCursorSelector 10 $captureZooSlotVa
[byte[]]$hiddenCursorPayload = New-PatchBlob $bytes $patchVa $CaptureCursorSelector 9 $captureZooSlotVa
[byte[]]$badGetterPayload = New-PatchBlob $bytes $patchVa $CaptureCursorSelector 8 $captureZooSlotVa
[byte[]]$readOnlyCapacityPayload = New-PatchBlob $bytes $patchVa $CaptureCursorSelector 7
[byte[]]$brokenCapacityPayload = New-PatchBlob $bytes $patchVa $CaptureCursorSelector 6
[byte[]]$monsterOnlyPayload = New-PatchBlob $bytes $patchVa $CaptureCursorSelector 5
[byte[]]$zeroCategoryPayload = New-PatchBlob $bytes $patchVa $CaptureCursorSelector 4
[byte[]]$validatorOnlyPayload = New-PatchBlob $bytes $patchVa $CaptureCursorSelector 3
[byte[]]$stateTargetPayload = New-PatchBlob $bytes $patchVa $CaptureCursorSelector 2
[byte[]]$unsafeTargetPayload = New-PatchBlob $bytes $patchVa $CaptureCursorSelector 1
[byte[]]$previousTargetPayload = New-PatchBlob $bytes $patchVa $CaptureCursorSelector 0
[byte[]]$previousCursorPayload = New-PatchBlob $bytes $patchVa 0x05 0
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
$payloadMatches = -not $sectionIsNew -and -not $dataSectionIsNew -and $section.RawSize -ge $PatchRawSize -and (Test-BytesEqual $bytes $section.RawOffset $payload)
$selector32PayloadMatches = -not $sectionIsNew -and -not $dataSectionIsNew -and $section.RawSize -ge $PatchRawSize -and (Test-BytesEqual $bytes $section.RawOffset $selector32Payload)
$staleRewardDisplayPayloadMatches = -not $sectionIsNew -and -not $dataSectionIsNew -and $section.RawSize -ge $PatchRawSize -and (Test-BytesEqual $bytes $section.RawOffset $staleRewardDisplayPayload)
$sharedRewardPayloadMatches = -not $sectionIsNew -and -not $dataSectionIsNew -and $section.RawSize -ge $PatchRawSize -and (Test-BytesEqual $bytes $section.RawOffset $sharedRewardPayload)
$artRelationPayloadMatches = -not $sectionIsNew -and -not $dataSectionIsNew -and $section.RawSize -ge $PatchRawSize -and (Test-BytesEqual $bytes $section.RawOffset $artRelationPayload)
$duplicateBlindPayloadMatches = -not $sectionIsNew -and -not $dataSectionIsNew -and $section.RawSize -ge $PatchRawSize -and (Test-BytesEqual $bytes $section.RawOffset $duplicateBlindPayload)
$uncleanAlertPayloadMatches = -not $sectionIsNew -and -not $dataSectionIsNew -and $section.RawSize -ge $PatchRawSize -and (Test-BytesEqual $bytes $section.RawOffset $uncleanAlertPayload)
$silentCapacityPayloadMatches = -not $sectionIsNew -and -not $dataSectionIsNew -and $section.RawSize -ge $PatchRawSize -and (Test-BytesEqual $bytes $section.RawOffset $silentCapacityPayload)
$hiddenCursorPayloadMatches = -not $sectionIsNew -and -not $dataSectionIsNew -and $section.RawSize -ge $PatchRawSize -and (Test-BytesEqual $bytes $section.RawOffset $hiddenCursorPayload)
$badGetterPayloadMatches = -not $sectionIsNew -and -not $dataSectionIsNew -and $section.RawSize -ge $PatchRawSize -and (Test-BytesEqual $bytes $section.RawOffset $badGetterPayload)
$readOnlyCapacityPayloadMatches = -not $sectionIsNew -and $section.RawSize -ge $PatchRawSize -and (Test-BytesEqual $bytes $section.RawOffset $readOnlyCapacityPayload)
$brokenCapacityPayloadMatches = -not $sectionIsNew -and $section.RawSize -ge $PatchRawSize -and (Test-BytesEqual $bytes $section.RawOffset $brokenCapacityPayload)
$monsterOnlyPayloadMatches = -not $sectionIsNew -and $section.RawSize -ge $PatchRawSize -and (Test-BytesEqual $bytes $section.RawOffset $monsterOnlyPayload)
$zeroCategoryPayloadMatches = -not $sectionIsNew -and $section.RawSize -ge $PatchRawSize -and (Test-BytesEqual $bytes $section.RawOffset $zeroCategoryPayload)
$validatorOnlyPayloadMatches = -not $sectionIsNew -and $section.RawSize -ge $PatchRawSize -and (Test-BytesEqual $bytes $section.RawOffset $validatorOnlyPayload)
$stateTargetPayloadMatches = -not $sectionIsNew -and $section.RawSize -ge $PatchRawSize -and (Test-BytesEqual $bytes $section.RawOffset $stateTargetPayload)
$unsafeTargetPayloadMatches = -not $sectionIsNew -and $section.RawSize -ge $PatchRawSize -and (Test-BytesEqual $bytes $section.RawOffset $unsafeTargetPayload)
$previousTargetPayloadMatches = -not $sectionIsNew -and $section.RawSize -ge $PatchRawSize -and (Test-BytesEqual $bytes $section.RawOffset $previousTargetPayload)
$previousCursorPayloadMatches = -not $sectionIsNew -and $section.RawSize -ge $PatchRawSize -and (Test-BytesEqual $bytes $section.RawOffset $previousCursorPayload)
$legacyPayloadMatches = -not $sectionIsNew -and (Test-BytesEqual $bytes $section.RawOffset $legacyPayload)
$payloadIsZero = -not $sectionIsNew -and (Test-ZeroRange $bytes $section.RawOffset $section.RawSize)
$installed = -not $sectionIsNew -and -not $dataSectionIsNew -and $factoryIsPatched -and $dispatchIsPatched -and $modeRegistryIsPatched -and $payloadMatches
$selector32Upgradeable = -not $sectionIsNew -and -not $dataSectionIsNew -and $factoryIsPatched -and $dispatchIsPatched -and $modeRegistryIsPatched -and $selector32PayloadMatches
$staleRewardDisplayUpgradeable = -not $sectionIsNew -and -not $dataSectionIsNew -and $factoryIsPatched -and $dispatchIsPatched -and $modeRegistryIsPatched -and $staleRewardDisplayPayloadMatches
$sharedRewardUpgradeable = -not $sectionIsNew -and -not $dataSectionIsNew -and $factoryIsPatched -and $dispatchIsPatched -and $modeRegistryIsPatched -and $sharedRewardPayloadMatches
$artRelationUpgradeable = -not $sectionIsNew -and -not $dataSectionIsNew -and $factoryIsPatched -and $dispatchIsPatched -and $modeRegistryIsPatched -and $artRelationPayloadMatches
$duplicateBlindUpgradeable = -not $sectionIsNew -and -not $dataSectionIsNew -and $factoryIsPatched -and $dispatchIsPatched -and $modeRegistryIsPatched -and $duplicateBlindPayloadMatches
$ownershipBlindPayloadMatches = -not $sectionIsNew -and -not $dataSectionIsNew -and $section.RawSize -ge $PatchRawSize -and (Test-BytesEqual $bytes $section.RawOffset $ownershipBlindPayload)
$ownershipBlindUpgradeable = -not $sectionIsNew -and -not $dataSectionIsNew -and $factoryIsPatched -and $dispatchIsPatched -and $modeRegistryIsPatched -and $ownershipBlindPayloadMatches
$uncleanAlertUpgradeable = -not $sectionIsNew -and -not $dataSectionIsNew -and $factoryIsPatched -and $dispatchIsPatched -and $modeRegistryIsPatched -and $uncleanAlertPayloadMatches
$silentCapacityUpgradeable = -not $sectionIsNew -and -not $dataSectionIsNew -and $factoryIsPatched -and $dispatchIsPatched -and $modeRegistryIsPatched -and $silentCapacityPayloadMatches
$hiddenCursorUpgradeable = -not $sectionIsNew -and -not $dataSectionIsNew -and $factoryIsPatched -and $dispatchIsPatched -and $modeRegistryIsPatched -and $hiddenCursorPayloadMatches
$badGetterUpgradeable = -not $sectionIsNew -and -not $dataSectionIsNew -and $factoryIsPatched -and $dispatchIsPatched -and $modeRegistryIsPatched -and $badGetterPayloadMatches
$readOnlyCapacityUpgradeable = -not $sectionIsNew -and $factoryIsPatched -and $dispatchIsPatched -and $modeRegistryIsPatched -and $readOnlyCapacityPayloadMatches
$brokenCapacityUpgradeable = -not $sectionIsNew -and $factoryIsPatched -and $dispatchIsPatched -and $modeRegistryIsPatched -and $brokenCapacityPayloadMatches
$monsterOnlyUpgradeable = -not $sectionIsNew -and $factoryIsPatched -and $dispatchIsPatched -and $modeRegistryIsPatched -and $monsterOnlyPayloadMatches
$zeroCategoryUpgradeable = -not $sectionIsNew -and $factoryIsPatched -and $dispatchIsPatched -and $modeRegistryIsPatched -and $zeroCategoryPayloadMatches
$validatorOnlyUpgradeable = -not $sectionIsNew -and $factoryIsPatched -and $dispatchIsPatched -and $modeRegistryIsPatched -and $validatorOnlyPayloadMatches
$stateTargetUpgradeable = -not $sectionIsNew -and $factoryIsPatched -and $dispatchIsPatched -and $modeRegistryIsPatched -and $stateTargetPayloadMatches
$unsafeTargetUpgradeable = -not $sectionIsNew -and $factoryIsPatched -and $dispatchIsPatched -and $modeRegistryIsPatched -and $unsafeTargetPayloadMatches
$targetUpgradeable = -not $sectionIsNew -and $factoryIsPatched -and $dispatchIsPatched -and $modeRegistryIsPatched -and $previousTargetPayloadMatches
$cursorUpgradeable = -not $sectionIsNew -and $factoryIsPatched -and $dispatchIsPatched -and $modeRegistryIsPatched -and $previousCursorPayloadMatches
$legacyInstalled = -not $sectionIsNew -and $factoryIsPatched -and $dispatchIsPatched -and $modeRegistryIsStock -and $legacyPayloadMatches
$installable = $sectionIsNew -and $factoryIsStock -and $modeRegistryIsStock -and ($dispatchIsStock -or $dispatchIsLegacy)
$reactivatable = -not $sectionIsNew -and $factoryIsStock -and $modeRegistryIsStock -and ($dispatchIsStock -or $dispatchIsLegacy) -and $payloadIsZero
if (-not ($installed -or $selector32Upgradeable -or $staleRewardDisplayUpgradeable -or $sharedRewardUpgradeable -or $artRelationUpgradeable -or $duplicateBlindUpgradeable -or $ownershipBlindUpgradeable -or $uncleanAlertUpgradeable -or $silentCapacityUpgradeable -or $hiddenCursorUpgradeable -or $badGetterUpgradeable -or $readOnlyCapacityUpgradeable -or $brokenCapacityUpgradeable -or $monsterOnlyUpgradeable -or $zeroCategoryUpgradeable -or $validatorOnlyUpgradeable -or $stateTargetUpgradeable -or $unsafeTargetUpgradeable -or $targetUpgradeable -or $cursorUpgradeable -or $legacyInstalled -or $installable -or $reactivatable)) {
    throw "MajestyHD.exe contains a partial or unrecognized Zoo private-panel patch; refusing to overwrite it."
}

$sectionIsLast = -not $sectionIsNew -and $dataSectionIsNew -and $section.Index -eq ($pe.SectionCount - 1) -and ($section.RawOffset + $section.RawSize) -eq $bytes.Length
$needsRawExpansion = -not $sectionIsNew -and $section.RawSize -lt $PatchRawSize
$needsHeaderRefresh = -not $sectionIsNew -and $section.VirtualSize -lt $PatchVirtualSize
$needsDataHeaderRefresh = -not $dataSectionIsNew -and $dataSection.VirtualSize -lt $DataSectionVirtualSize
if ($needsRawExpansion -and -not $sectionIsLast) { throw "The existing .mzoo section is not last and cannot be safely expanded." }

Write-Host "Majesty Gold HD Restore Abandoned Zoo private Capture Flag"
Write-Host "Executable profile: $ExecutableProfileId"
if ($installed) {
    Write-Host "MajestyHD.exe: the private ZC01/ZCF0 placement lifecycle is already installed."
}
elseif ($DryRun) {
    Write-Host ("MajestyHD.exe: would {0} .mzoo and route only ZC01 through independently priced, capacity-gated, duplicate-safe hostile-monster-only ZCF0 placement." -f $(if ($selector32Upgradeable -or $staleRewardDisplayUpgradeable -or $sharedRewardUpgradeable -or $artRelationUpgradeable -or $duplicateBlindUpgradeable -or $ownershipBlindUpgradeable -or $uncleanAlertUpgradeable -or $silentCapacityUpgradeable -or $hiddenCursorUpgradeable -or $badGetterUpgradeable -or $readOnlyCapacityUpgradeable -or $brokenCapacityUpgradeable -or $monsterOnlyUpgradeable -or $zeroCategoryUpgradeable -or $validatorOnlyUpgradeable -or $stateTargetUpgradeable -or $unsafeTargetUpgradeable -or $targetUpgradeable -or $cursorUpgradeable -or $legacyInstalled) { "upgrade" } elseif ($sectionIsNew) { "append" } else { "reactivate" }))
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
    elseif ($needsRawExpansion) {
        [byte[]]$expanded = New-Object byte[] ($section.RawOffset + $PatchRawSize)
        [Array]::Copy($bytes, 0, $expanded, 0, $bytes.Length)
        $bytes = $expanded
        Write-Bytes $bytes $section.HeaderOffset (New-SectionHeader $SectionName $PatchVirtualSize $section.Rva $PatchRawSize $section.RawOffset)
    }
    elseif ($needsHeaderRefresh) {
        # Version 10 already reserved the full 0x600 raw bytes before .mzdt.
        # Raising VirtualSize to expose the alert tail changes no RVA or file
        # layout because RawSize was already the larger section extent.
        Write-Bytes $bytes $section.HeaderOffset (New-SectionHeader $SectionName $PatchVirtualSize $section.Rva $section.RawSize $section.RawOffset)
    }
    if ($dataSectionIsNew) {
        [byte[]]$expanded = New-Object byte[] ($dataSection.RawOffset + $DataSectionRawSize)
        [Array]::Copy($bytes, 0, $expanded, 0, $bytes.Length)
        $bytes = $expanded
        Write-Bytes $bytes $dataSection.HeaderOffset (New-SectionHeader $DataSectionName $DataSectionVirtualSize $dataSection.Rva $DataSectionRawSize $dataSection.RawOffset $DataSectionCharacteristics)
        $newSectionCount = $pe.SectionCount + 1 + $(if ($sectionIsNew) { 1 } else { 0 })
        [BitConverter]::GetBytes([uint16]$newSectionCount).CopyTo($bytes, $pe.SectionCountOffset)
    }
    elseif ($needsDataHeaderRefresh) {
        # The existing writable private-data section already reserves 0x200
        # raw bytes. Expose its second DWORD for the independent Capture reward
        # without moving any section or changing another utility's RVA.
        Write-Bytes $bytes $dataSection.HeaderOffset (New-SectionHeader $DataSectionName $DataSectionVirtualSize $dataSection.Rva $dataSection.RawSize $dataSection.RawOffset $DataSectionCharacteristics)
    }
    $sizeOfImage = Align-Value ([uint32]($dataSection.Rva + $DataSectionVirtualSize)) $pe.SectionAlignment
    [BitConverter]::GetBytes([uint32]$sizeOfImage).CopyTo($bytes, $pe.SizeOfImageOffset)
    Write-Bytes $bytes $section.RawOffset $payload
    [BitConverter]::GetBytes([int32]-1).CopyTo($bytes, ($dataSection.RawOffset + 4))
    Write-Bytes $bytes $FactoryHookOffset $factoryHook
    Write-Bytes $bytes $DispatchSlotOffset $privateDispatchSlot
    Write-Bytes $bytes $ModeRegistryHookOffset $modeRegistryHook
    try { [IO.File]::WriteAllBytes($exePath, $bytes) }
    catch { throw "Cannot modify MajestyHD.exe. Close Majesty and try again. If needed, run PowerShell as administrator." }
    [byte[]]$verified = [IO.File]::ReadAllBytes($exePath)
    if (-not (Test-BytesEqual $verified $FactoryHookOffset $factoryHook) -or
        -not (Test-BytesEqual $verified $DispatchSlotOffset $privateDispatchSlot) -or
        -not (Test-BytesEqual $verified $ModeRegistryHookOffset $modeRegistryHook) -or
        -not (Test-BytesEqual $verified $section.RawOffset $payload) -or
        (Read-U32 $verified ($section.HeaderOffset + 36)) -ne $SectionCharacteristics -or
        (Read-U32 $verified ($dataSection.HeaderOffset + 8)) -lt $DataSectionVirtualSize -or
        (Read-U32 $verified ($dataSection.HeaderOffset + 36)) -ne $DataSectionCharacteristics -or
        (Read-U32 $verified ($dataSection.RawOffset + 4)) -ne [uint32]0xFFFFFFFFL) {
        throw "MajestyHD.exe verification failed after installing the private Capture Flag."
    }
    Write-Host "MajestyHD.exe: ZC01 now uses independently priced, capacity-gated, duplicate-safe hostile-monster-only private ZCF0 placement; Palace AP41 remains on stock Fl00."
}
