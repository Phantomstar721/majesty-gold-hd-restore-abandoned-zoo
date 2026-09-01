$ZooRewardDispatcherProfiles = @(
    [pscustomobject]@{
        Id = "public-1.5.2.24"
        PeTimestamp = [uint32]0x5897B72F
        FactoryHookOffset = 0x10A020
        FactoryHookVa = 0x0050AC20
        FactoryResumeVa = 0x0050AC26
        FactoryNullVa = 0x0050C035
        FactoryReturnVa = 0x0050C037
        OperatorNewVa = 0x006D8F7E
        Ap41ConstructorVa = 0x004A94E0
        Ap41FactoryVa = 0x0050AF8F
        OpenDialogVa = 0x004B03F0
        PalaceDispatchVa = 0x004A5440
        StockAp41HandlerVa = 0x004A92F0
        StockAp41ActivationVa = 0x004A9230
        StockAp41RefreshVa = 0x004A94A0
        AttackRewardAmountVa = 0x007C17A4
        FlagModeOwnerVa = 0x007C12F0
        GetFlagModeManagerVa = 0x00454B90
        GetSelectedFlagModeVa = 0x004556D0
        SetFlagModeVa = 0x00454E70
        DispatchSlotOffset = 0x33DFA8
        PalaceHandlerOffset = 0x0A4840
        Ap41FactoryOffset = 0x10A38F
        OpenDialogOffset = 0x0AF7F0
        ModeRegistryHookOffset = 0x05D8E4
        ModeRegistryHookVa = 0x0045E4E4
        ModeRegistryResumeVa = 0x0045E4EF
        Fl00RegistrationOffset = 0x05D83E
        Fl00RegistrationVa = 0x0045E43E
        StockCaptureCallbackOffset = 0x05C800
        StockCaptureCallbackVa = 0x0045D400
        StockCaptureValidatorVa = 0x0045D360
        StockFlagTargetCheckVa = 0x0045D2D0
        GetFlagModeStateVa = 0x0045E900
        DisplayClassifierVa = 0x00508510
        GetSelectedAgentVa = 0x00467540
        GetAttributeVa = 0x005B9FD0
        BadGetAttributeVa = 0x005B93D0
        FindAttachedRelationVa = 0x005A7730
        SystemAlertOwnerVa = 0x007C1394
        PrepareSystemAlertVa = 0x0046ABE0
        PostLiteralSystemAlertVa = 0x0046ACE0
        StockAp41VtableOffset = 0x33D3B4
        FlagModeConstructorVa = 0x0059D1E0
        GetFlagModeRegistryVa = 0x0059EF30
        StockCaptureCallbackExternalCalls = @{
            0x12 = 0x0045E900; 0x19 = 0x00425D00; 0x4F = 0x006418F0
            0x66 = 0x005D8620; 0x90 = 0x00641850; 0x9A = 0x00424A00
            0xAC = 0x0045D2D0; 0xBE = 0x0045E910; 0xCA = 0x005C2060
            0xD5 = 0x0045CC90; 0x117 = 0x00641850; 0x143 = 0x0045C950
            0x163 = 0x00641990; 0x17C = 0x00641990; 0x189 = 0x0045CAF0
            0x196 = 0x0045CA40
        }
        StockDispatchSlot = [byte[]]@(0x80,0xD2,0x4B,0x00)
        LegacyPalaceDispatchSlot = [byte[]]@(0x40,0x54,0x4A,0x00)
        Ap41FactorySignature = [byte[]]@(
            0x6A,0x34,0xE8,0xE8,0xDF,0x1C,0x00,0x83,
            0xC4,0x04,0x89,0x44,0x24,0x14
        )
        StockCallbackCreateSignature = [byte[]]@(
            0x57,0x68,0x04,0xBA,0x73,0x00,0xE8,0xB6,0xF7,0xFF,0xFF
        )
    }
    [pscustomobject]@{
        Id = "beta2-1.5.2.28"
        PeTimestamp = [uint32]0x5A8A11D5
        FactoryHookOffset = 0x11A570
        FactoryHookVa = 0x0051B170
        FactoryResumeVa = 0x0051B176
        FactoryNullVa = 0x0051C585
        FactoryReturnVa = 0x0051C587
        OperatorNewVa = 0x006EE542
        Ap41ConstructorVa = 0x004A9DD0
        Ap41FactoryVa = 0x0051B4DF
        OpenDialogVa = 0x004B0CE0
        PalaceDispatchVa = 0x004A5D40
        StockAp41HandlerVa = 0x004A9BE0
        StockAp41ActivationVa = 0x004A9B20
        StockAp41RefreshVa = 0x004A9D90
        AttackRewardAmountVa = 0x007E028C
        FlagModeOwnerVa = 0x007DFDA8
        GetFlagModeManagerVa = 0x00455BC0
        GetSelectedFlagModeVa = 0x00456700
        SetFlagModeVa = 0x00455EA0
        DispatchSlotOffset = 0x356090
        PalaceHandlerOffset = 0x0A5140
        Ap41FactoryOffset = 0x11A8DF
        OpenDialogOffset = 0x0B00E0
        ModeRegistryHookOffset = 0x05E914
        ModeRegistryHookVa = 0x0045F514
        ModeRegistryResumeVa = 0x0045F51F
        Fl00RegistrationOffset = 0x05E86E
        Fl00RegistrationVa = 0x0045F46E
        StockCaptureCallbackOffset = 0x05D830
        StockCaptureCallbackVa = 0x0045E430
        StockCaptureValidatorVa = 0x0045E390
        StockFlagTargetCheckVa = 0x0045E300
        GetFlagModeStateVa = 0x0045F930
        DisplayClassifierVa = 0x0050A6E0
        GetSelectedAgentVa = 0x00468780
        GetAttributeVa = 0x005CEF70
        BadGetAttributeVa = 0x005CE370
        FindAttachedRelationVa = 0x005BC6E0
        SystemAlertOwnerVa = 0x007DFE4C
        PrepareSystemAlertVa = 0x0046BE70
        PostLiteralSystemAlertVa = 0x0046BFE0
        StockAp41VtableOffset = 0x35548C
        FlagModeConstructorVa = 0x005B2190
        GetFlagModeRegistryVa = 0x005B3EE0
        StockCaptureCallbackExternalCalls = @{
            0x12 = 0x0045F930; 0x19 = 0x00426CD0; 0x4F = 0x00656D50
            0x66 = 0x005ED920; 0x90 = 0x00656CB0; 0x9A = 0x004259D0
            0xAC = 0x0045E300; 0xBE = 0x0045F940; 0xCA = 0x005D7240
            0xD5 = 0x0045DCC0; 0x117 = 0x00656CB0; 0x143 = 0x0045D980
            0x163 = 0x00656DF0; 0x17C = 0x00656DF0; 0x189 = 0x0045DB20
            0x196 = 0x0045DA70
        }
        StockDispatchSlot = [byte[]]@(0xC0,0xDC,0x4B,0x00)
        LegacyPalaceDispatchSlot = [byte[]]@(0x40,0x5D,0x4A,0x00)
        Ap41FactorySignature = [byte[]]@(
            0x6A,0x34,0xE8,0x5C,0x30,0x1D,0x00,0x83,
            0xC4,0x04,0x89,0x44,0x24,0x14
        )
        StockCallbackCreateSignature = [byte[]]@(
            0x57,0x68,0xD4,0x4A,0x75,0x00,0xE8,0xB6,0xF7,0xFF,0xFF
        )
    }
)

function Get-ZooRewardDispatcherProfile {
    param([byte[]]$Bytes)
    if ($Bytes.Length -lt 0x100) {
        throw "Majesty executable is too small to contain a valid PE header."
    }
    $peOffset = [BitConverter]::ToUInt32($Bytes, 0x3C)
    if (($peOffset + 12) -gt $Bytes.Length -or
        [BitConverter]::ToUInt32($Bytes, $peOffset) -ne 0x00004550) {
        throw "Majesty executable does not contain a valid PE header."
    }
    $timestamp = [BitConverter]::ToUInt32($Bytes, $peOffset + 8)
    $profile = $ZooRewardDispatcherProfiles |
        Where-Object PeTimestamp -eq $timestamp |
        Select-Object -First 1
    if ($null -eq $profile) {
        throw ("Unsupported Majesty executable timestamp 0x{0:X8}; supported profiles are public-1.5.2.24 and beta2-1.5.2.28." -f $timestamp)
    }
    $profile
}

function Use-ZooRewardDispatcherProfile {
    param([pscustomobject]$Profile)
    foreach ($property in $Profile.PSObject.Properties) {
        if ($property.Name -in @("Id", "PeTimestamp")) { continue }
        Set-Variable -Scope Script -Name $property.Name -Value $property.Value
    }
    $script:ExecutableProfileId = $Profile.Id
}
