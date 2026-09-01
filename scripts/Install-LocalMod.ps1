param(
    [string]$GamePath = "C:\Program Files (x86)\Steam\steamapps\common\Majesty HD",
    [string]$ModsRoot = "$env:USERPROFILE\Documents\My Games\MajestyHD\Mods",
    [switch]$ContentOnly
)

$ErrorActionPreference = "Stop"
$packageName = "RestoreAbandonedZoo"
$repoRoot = [IO.Path]::GetFullPath((Split-Path -Parent $PSScriptRoot))
$source = [IO.Path]::GetFullPath((Join-Path $repoRoot "dist\$packageName"))
$mods = [IO.Path]::GetFullPath($ModsRoot).TrimEnd('\', '/')
$target = [IO.Path]::GetFullPath((Join-Path $mods $packageName))

if ((Split-Path -Leaf $mods) -ine "Mods" -or
    (Split-Path -Leaf (Split-Path -Parent $mods)) -ine "MajestyHD") {
    throw "Expected a MajestyHD\Mods directory, got: $mods"
}
if (-not (Test-Path -LiteralPath $mods -PathType Container)) {
    throw "MajestyHD Mods directory does not exist: $mods"
}
if (((Get-Item -LiteralPath $mods -Force).Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
    throw "Refusing to deploy through a reparse-point Mods directory: $mods"
}
if ((Split-Path -Parent $target) -ine $mods -or (Split-Path -Leaf $target) -cne $packageName) {
    throw "Unsafe local mod target: $target"
}

& python (Join-Path $PSScriptRoot "build_mod.py") --game-path $GamePath
if ($LASTEXITCODE -ne 0) {
    throw "Zoo build failed with exit code $LASTEXITCODE"
}
& python (Join-Path $PSScriptRoot "validate_mod.py") $source
if ($LASTEXITCODE -ne 0) {
    throw "Zoo package validation failed with exit code $LASTEXITCODE"
}

if (Test-Path -LiteralPath $target) {
    $targetItem = Get-Item -LiteralPath $target -Force
    if (-not $targetItem.PSIsContainer -or
        (($targetItem.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0)) {
        throw "Refusing to replace an unsafe local mod target: $target"
    }
    Get-ChildItem -LiteralPath $target -Recurse -Force | ForEach-Object {
        if (($_.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
            throw "Refusing to replace a target containing a reparse point: $($_.FullName)"
        }
    }
    Remove-Item -LiteralPath $target -Recurse -Force
}

New-Item -ItemType Directory -Path $target | Out-Null
Get-ChildItem -LiteralPath $source -Force | Copy-Item -Destination $target -Recurse -Force

$sourceFiles = @{}
Get-ChildItem -LiteralPath $source -Recurse -File -Force | ForEach-Object {
    $relative = $_.FullName.Substring($source.Length).TrimStart('\', '/')
    $sourceFiles[$relative] = [pscustomobject]@{
        Length = $_.Length
        Hash = (Get-FileHash -Algorithm SHA256 -LiteralPath $_.FullName).Hash
    }
}
$targetFiles = @{}
Get-ChildItem -LiteralPath $target -Recurse -File -Force | ForEach-Object {
    $relative = $_.FullName.Substring($target.Length).TrimStart('\', '/')
    $targetFiles[$relative] = [pscustomobject]@{
        Length = $_.Length
        Hash = (Get-FileHash -Algorithm SHA256 -LiteralPath $_.FullName).Hash
    }
}
if ($sourceFiles.Count -eq 0 -or $targetFiles.Count -ne $sourceFiles.Count) {
    throw "Local deployment file-count verification failed"
}
foreach ($relative in $sourceFiles.Keys) {
    if (-not $targetFiles.ContainsKey($relative) -or
        $targetFiles[$relative].Length -ne $sourceFiles[$relative].Length -or
        $targetFiles[$relative].Hash -ne $sourceFiles[$relative].Hash) {
        throw "Local deployment verification failed: $relative"
    }
}

if (-not $ContentOnly) {
    & (Join-Path $PSScriptRoot "Install-ZooRewardDispatcher.ps1") -GamePath $GamePath
    if ($LASTEXITCODE -ne 0) {
        throw "Zoo reward-dispatch installation failed with exit code $LASTEXITCODE"
    }
}

Write-Host "Installed and verified $($sourceFiles.Count) files:"
Write-Host $target
if ($ContentOnly) {
    Write-Host "Skipped standalone executable dispatcher for CAM Merge Manager use."
}
