param(
    [string]$PackageRoot = ".\dist\RestoreAbandonedZoo",
    [string]$WorkshopId = "0"
)

$ErrorActionPreference = "Stop"
$repoRoot = [IO.Path]::GetFullPath((Split-Path -Parent $PSScriptRoot))
$distRoot = [IO.Path]::GetFullPath((Join-Path $repoRoot "dist"))
$package = if ([IO.Path]::IsPathRooted($PackageRoot)) {
    [IO.Path]::GetFullPath($PackageRoot)
} else {
    [IO.Path]::GetFullPath((Join-Path $repoRoot $PackageRoot))
}
$target = [IO.Path]::GetFullPath((Join-Path $distRoot "workshop-upload"))
$stage = [IO.Path]::GetFullPath(
    (Join-Path $distRoot (".workshop-upload-stage-" + [guid]::NewGuid().ToString("N")))
)
$backup = [IO.Path]::GetFullPath(
    (Join-Path $distRoot (".workshop-upload-backup-" + [guid]::NewGuid().ToString("N")))
)
$ownershipMarker = ".restore-abandoned-zoo-workshop-stage"
$projectName = "RestoreAbandonedZoo.mswproj"
$descriptionSource = Join-Path $repoRoot "WORKSHOP.md"
$previewSource = Join-Path $repoRoot "assets\workshop\workshop-preview.jpg"
$instructionsSource = Join-Path $repoRoot "release\START HERE.txt"

$required = @(
    (Join-Path $package "RestoreAbandonedZoo.mmxml"),
    (Join-Path $package "mod-definition.json"),
    (Join-Path $package "Data\RestoreAbandonedZoo.bcd"),
    $descriptionSource,
    $previewSource,
    $instructionsSource
)
foreach ($path in $required) {
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
        throw "Required Workshop input is missing: $path"
    }
}
if ($WorkshopId -notmatch '^(0|[1-9][0-9]*)$') {
    throw "Workshop ID must be zero or a positive integer: $WorkshopId"
}
if (-not $package.StartsWith($distRoot + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) {
    throw "Workshop package must remain under this repository's dist directory: $package"
}
if (-not $target.StartsWith($distRoot + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) {
    throw "Workshop target escaped this repository's dist directory: $target"
}

$sourceLinks = @(
    Get-Item -LiteralPath $package -Force
    Get-ChildItem -LiteralPath $package -Recurse -Force
) | Where-Object { ($_.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0 }
if ($sourceLinks.Count -gt 0) {
    throw "Refusing to stage a package containing a link or reparse point: $($sourceLinks[0].FullName)"
}

$definition = Get-Content -LiteralPath (Join-Path $package "mod-definition.json") -Raw |
    ConvertFrom-Json
if ($definition.schema_version -ne 3) {
    throw "Workshop package is not a Mod Manager v3 package."
}
if ($definition.mod_id -ne "{d45a135f-31ca-4b53-b3e4-776e231a328c}") {
    throw "Workshop package has the wrong Restore Abandoned Zoo mod ID."
}
$requiredFeatures = @(
    "stock.mx09-ap41-reward-panel.v1",
    "stock.mx04-mx05-occupant-action-panel.v1",
    "stock.mx22-building-open-toggle.v1",
    "stock.gplmx-purchase-bazaar-tail.v1",
    "stock.controlled-follower-speed-sync.v1",
    "stock.ap41-fl00-hostile-monster-flag.v1"
)
if ((@($definition.runtime_features.type) -join "`n") -ne ($requiredFeatures -join "`n")) {
    throw "Workshop package has an incomplete or reordered runtime feature contract."
}

if (Test-Path -LiteralPath $target) {
    $targetItem = Get-Item -LiteralPath $target -Force
    if (($targetItem.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
        throw "Refusing to replace a linked Workshop staging directory: $target"
    }
    if (-not (Test-Path -LiteralPath (Join-Path $target $ownershipMarker) -PathType Leaf)) {
        throw "Refusing to replace a Workshop directory not owned by this repository: $target"
    }
}

try {
    $contentPath = Join-Path $stage "content"
    New-Item -ItemType Directory -Path $contentPath -Force | Out-Null
    Get-ChildItem -LiteralPath $package -Force |
        Copy-Item -Destination $contentPath -Recurse -Force
    Copy-Item -LiteralPath $instructionsSource -Destination (Join-Path $contentPath "START HERE.txt") -Force
    Copy-Item -LiteralPath $previewSource -Destination (Join-Path $stage "workshop-preview.jpg") -Force

    $projectId = $WorkshopId
    $visibility = "Private"
    $existingProject = Join-Path $target $projectName
    if (Test-Path -LiteralPath $existingProject -PathType Leaf) {
        $existingText = Get-Content -LiteralPath $existingProject -Raw
        $existingId = [regex]::Match($existingText, '<SteamWorkshop id="([1-9][0-9]*)"')
        if ($existingId.Success) {
            $projectId = $existingId.Groups[1].Value
        }
        $existingVisibility = [regex]::Match(
            $existingText,
            '<SteamWorkshop[^>]+visibility="(Private|Public|FriendsOnly)"'
        )
        if ($existingVisibility.Success) {
            $visibility = $existingVisibility.Groups[1].Value
        }
    }

    $finalContentPath = [Security.SecurityElement]::Escape((Join-Path $target "content"))
    $finalPreviewPath = [Security.SecurityElement]::Escape((Join-Path $target "workshop-preview.jpg"))
    $description = [Security.SecurityElement]::Escape(
        (Get-Content -LiteralPath $descriptionSource -Raw).Trim()
    )
    $projectText = @"
<Majesty>
	<SteamWorkshop id="$projectId" visibility="$visibility">
		<Title lang="en_US">Restore Abandoned Zoo</Title>
		<Description lang="en_US">$description</Description>
		<ContentPath>$finalContentPath</ContentPath>
		<PreviewImagePath>$finalPreviewPath</PreviewImagePath>
		<IDTag>Mod</IDTag>
		<IDTag>Building</IDTag>
		<IDTag>Original Rules</IDTag>
		<IDTag>Northern Expansion Rules</IDTag>
	</SteamWorkshop>
</Majesty>
"@
    $utf8NoBom = New-Object Text.UTF8Encoding($false)
    [IO.File]::WriteAllText((Join-Path $stage $projectName), $projectText, $utf8NoBom)
    [IO.File]::WriteAllText(
        (Join-Path $stage $ownershipMarker),
        "schema=1`r`n",
        [Text.Encoding]::ASCII
    )

    $contentFiles = @(
        Get-ChildItem -LiteralPath $contentPath -Recurse -File -Force |
            Sort-Object FullName
    )
    if ($contentFiles.Count -lt 13) {
        throw "Workshop content is unexpectedly incomplete: $($contentFiles.Count) files"
    }
    $manifestLines = foreach ($file in $contentFiles) {
        $relative = $file.FullName.Substring($contentPath.Length).TrimStart('\').Replace('\', '/')
        $hash = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash.ToUpperInvariant()
        "$hash  $relative"
    }
    [IO.File]::WriteAllText(
        (Join-Path $stage "SHA256.txt"),
        (($manifestLines -join "`r`n") + "`r`n"),
        [Text.Encoding]::ASCII
    )

    if (Test-Path -LiteralPath $target) {
        Move-Item -LiteralPath $target -Destination $backup
    }
    Move-Item -LiteralPath $stage -Destination $target
    if (Test-Path -LiteralPath $backup) {
        Remove-Item -LiteralPath $backup -Recurse -Force
    }
}
catch {
    if ((Test-Path -LiteralPath $backup) -and -not (Test-Path -LiteralPath $target)) {
        Move-Item -LiteralPath $backup -Destination $target
    }
    throw
}
finally {
    if (Test-Path -LiteralPath $stage) {
        Remove-Item -LiteralPath $stage -Recurse -Force
    }
}

$finalContent = Join-Path $target "content"
$finalFiles = @(Get-ChildItem -LiteralPath $finalContent -Recurse -File -Force)
$totalBytes = ($finalFiles | Measure-Object -Property Length -Sum).Sum
Write-Host "Workshop upload staged: $target"
Write-Host "  Files:   $($finalFiles.Count)"
Write-Host "  Bytes:   $totalBytes"
Write-Host "  Project: $(Join-Path $target $projectName)"
Write-Host "  Preview: $(Join-Path $target 'workshop-preview.jpg')"
