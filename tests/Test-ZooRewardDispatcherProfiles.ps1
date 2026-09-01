param(
    [Parameter(Mandatory = $true)][string]$PublicExe,
    [Parameter(Mandatory = $true)][string]$Beta2Exe
)

$ErrorActionPreference = "Stop"
$repoRoot = [IO.Path]::GetFullPath((Split-Path -Parent $PSScriptRoot))
$install = Join-Path $repoRoot "scripts\Install-ZooRewardDispatcher.ps1"
$restore = Join-Path $repoRoot "scripts\Restore-ZooRewardDispatcher.ps1"
$profiles = Join-Path $repoRoot "scripts\ZooRewardDispatcherProfiles.ps1"

function Assert-True {
    param([bool]$Condition, [string]$Message)
    if (-not $Condition) { throw $Message }
}

function Get-PeSection {
    param([byte[]]$Bytes, [string]$Name)
    $peOffset = [BitConverter]::ToUInt32($Bytes, 0x3C)
    $count = [BitConverter]::ToUInt16($Bytes, $peOffset + 6)
    $optionalSize = [BitConverter]::ToUInt16($Bytes, $peOffset + 20)
    $optionalOffset = $peOffset + 24
    $table = $optionalOffset + $optionalSize
    for ($i = 0; $i -lt $count; $i++) {
        $offset = $table + ($i * 40)
        $sectionName = [Text.Encoding]::ASCII.GetString($Bytes[$offset..($offset + 7)]).TrimEnd([char]0)
        if ($sectionName -eq $Name) {
            return [pscustomobject]@{
                ImageBase = [BitConverter]::ToUInt32($Bytes, $optionalOffset + 28)
                Rva = [BitConverter]::ToUInt32($Bytes, $offset + 12)
                RawOffset = [BitConverter]::ToUInt32($Bytes, $offset + 20)
            }
        }
    }
    $null
}

function Get-RelativeCallTarget {
    param([byte[]]$Bytes, [int]$FileOffset, [uint32]$SourceVa)
    Assert-True ($Bytes[$FileOffset] -eq 0xE8) ("Expected CALL at file offset 0x{0:X}." -f $FileOffset)
    $relative = [BitConverter]::ToInt32($Bytes, $FileOffset + 1)
    [uint32]([int64]$SourceVa + 5 + $relative)
}

foreach ($path in @($PublicExe, $Beta2Exe, $install, $restore, $profiles)) {
    Assert-True (Test-Path -LiteralPath $path -PathType Leaf) "Required fixture or script was not found: $path"
}

. $profiles
Assert-True ($ZooRewardDispatcherProfiles.Count -eq 2) "Expected exactly two maintained executable profiles."
Assert-True (($ZooRewardDispatcherProfiles.Id -contains "public-1.5.2.24") -and
             ($ZooRewardDispatcherProfiles.Id -contains "beta2-1.5.2.28")) "Maintained executable profile IDs changed."

$testRoot = Join-Path ([IO.Path]::GetTempPath()) ("zoo-dispatcher-profiles-" + [Guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $testRoot | Out-Null
try {
    $cases = @(
        [pscustomobject]@{ Id = "public-1.5.2.24"; Source = [IO.Path]::GetFullPath($PublicExe) }
        [pscustomobject]@{ Id = "beta2-1.5.2.28"; Source = [IO.Path]::GetFullPath($Beta2Exe) }
    )
    foreach ($case in $cases) {
        $caseRoot = Join-Path $testRoot $case.Id
        New-Item -ItemType Directory -Path $caseRoot | Out-Null
        $fixture = Join-Path $caseRoot "MajestyHD.exe"
        Copy-Item -LiteralPath $case.Source -Destination $fixture
        $before = (Get-FileHash -LiteralPath $fixture -Algorithm SHA256).Hash

        $selected = Get-ZooRewardDispatcherProfile ([IO.File]::ReadAllBytes($fixture))
        Assert-True ($selected.Id -eq $case.Id) "Fixture selected $($selected.Id), expected $($case.Id)."

        & $install -GamePath $caseRoot | Out-Host
        $patched = [IO.File]::ReadAllBytes($fixture)
        Assert-True ([Text.Encoding]::ASCII.GetString($patched).Contains("RestoreAbandonedZoo.ZC01.ZCF0")) "Private payload signature missing for $($case.Id)."
        $section = Get-PeSection $patched ".mzoo"
        Assert-True ($null -ne $section) "Private .mzoo section missing for $($case.Id)."
        $patchVa = [uint32]($section.ImageBase + $section.Rva)
        $registrationOffset = 0x1C0
        $constructor = Get-RelativeCallTarget $patched ($section.RawOffset + $registrationOffset + 0x37) ([uint32]($patchVa + $registrationOffset + 0x37))
        $registry = Get-RelativeCallTarget $patched ($section.RawOffset + $registrationOffset + 0x44) ([uint32]($patchVa + $registrationOffset + 0x44))
        Assert-True ($constructor -eq $selected.FlagModeConstructorVa) "Flag-mode constructor target mismatch for $($case.Id)."
        Assert-True ($registry -eq $selected.GetFlagModeRegistryVa) "Flag-mode registry target mismatch for $($case.Id)."
        foreach ($offset in @(0x32, 0x56, 0x6E)) {
            $owner = [BitConverter]::ToUInt32($patched, $section.RawOffset + 0xE0 + $offset)
            Assert-True ($owner -eq $selected.FlagModeOwnerVa) ("Flag-mode owner mismatch at private handler +0x{0:X} for {1}." -f $offset, $case.Id)
        }
        foreach ($item in $selected.StockCaptureCallbackExternalCalls.GetEnumerator()) {
            $offset = [int]$item.Key
            $expected = $(if ($offset -eq 0xAC) { [uint32]($patchVa + 0x4F0) } else { [uint32]$item.Value })
            $target = Get-RelativeCallTarget $patched ($section.RawOffset + 0x240 + $offset) ([uint32]($patchVa + 0x240 + $offset))
            Assert-True ($target -eq $expected) ("Capture callback target mismatch at +0x{0:X} for {1}." -f $offset, $case.Id)
        }

        & $restore -GamePath $caseRoot | Out-Host
        $after = (Get-FileHash -LiteralPath $fixture -Algorithm SHA256).Hash
        Assert-True ($after -eq $before) "Install/restore did not round-trip $($case.Id) exactly."
    }
}
finally {
    if (Test-Path -LiteralPath $testRoot) {
        Remove-Item -LiteralPath $testRoot -Recurse -Force
    }
}

Write-Host "Zoo reward-dispatcher profiles passed install/restore round-trip tests."
