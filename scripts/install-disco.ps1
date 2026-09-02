[CmdletBinding()]
param(
    [switch]$Yes,
    [switch]$Update,
    [switch]$Uninstall,
    [string]$Version,
    [string]$InstallDir,
    [switch]$SkipBashCheck
)

$ErrorActionPreference = "Stop"
$PackageName = "@arex-skill/disco"
$MinimumNodeVersion = [version]"22.19.0"
$DefaultNodeVersion = "22.19.0"
$DefaultInstallerUrl = "https://github.com/VectorSpaceLab/AREX-Skill/releases/latest/download/install-disco.ps1"
$AgentDir = if ($env:DISCO_CODING_AGENT_DIR) { $env:DISCO_CODING_AGENT_DIR } else { Join-Path $env:USERPROFILE ".disco\agent" }
$AgentDir = [Environment]::ExpandEnvironmentVariables($AgentDir)
if ($AgentDir.StartsWith("~")) { $AgentDir = Join-Path $env:USERPROFILE $AgentDir.Substring(2) }
$ManagedRoot = if ($InstallDir) { $InstallDir } elseif ($env:DISCO_INSTALL_DIR) { $env:DISCO_INSTALL_DIR } else { Join-Path $AgentDir "install" }
$ManagedRoot = [IO.Path]::GetFullPath($ManagedRoot)
$rootPath = [IO.Path]::GetPathRoot($ManagedRoot)
if ([string]::Equals($ManagedRoot.TrimEnd('\'), $rootPath.TrimEnd('\'), [StringComparison]::OrdinalIgnoreCase) -or
    [string]::Equals($ManagedRoot.TrimEnd('\'), $AgentDir.TrimEnd('\'), [StringComparison]::OrdinalIgnoreCase) -or
    [string]::Equals($ManagedRoot.TrimEnd('\'), $env:USERPROFILE.TrimEnd('\'), [StringComparison]::OrdinalIgnoreCase)) {
    throw "refusing to use a broad managed install directory: $ManagedRoot"
}
$InstallerUrl = if ($env:DISCO_INSTALLER_URL) { $env:DISCO_INSTALLER_URL } else { $DefaultInstallerUrl }
$TemporaryRoot = Join-Path ([IO.Path]::GetTempPath()) ("disco-install-" + [guid]::NewGuid().ToString("N"))
$Mutex = $null

function Fail([string]$Message) { throw $Message }

function Download-File([string]$Url, [string]$Destination) {
    try {
        Invoke-WebRequest -Uri $Url -OutFile $Destination -UseBasicParsing -Headers @{ "User-Agent" = "AREX-Skill-DisCo-Installer" }
    } catch {
        Fail "could not download $Url`: $($_.Exception.Message)"
    }
}

function Get-Sha256([string]$Path) {
    return (Get-FileHash -Algorithm SHA256 -LiteralPath $Path).Hash.ToLowerInvariant()
}

function Get-NodeRuntime {
    $nodeCommand = Get-Command node.exe -ErrorAction SilentlyContinue
    $npmCommand = Get-Command npm.cmd -ErrorAction SilentlyContinue
    if ($nodeCommand -and $npmCommand) {
        $nodeVersionText = (& $nodeCommand.Source --version).Trim().TrimStart("v")
        try { $nodeVersion = [version]$nodeVersionText } catch { $nodeVersion = [version]"0.0.0" }
        if ($nodeVersion -ge $MinimumNodeVersion) {
            return [pscustomobject]@{ Node = $nodeCommand.Source; Npm = $npmCommand.Source; Source = "system"; Version = $nodeVersionText }
        }
    }

    $managedVersion = if ($env:DISCO_MANAGED_NODE_VERSION) { $env:DISCO_MANAGED_NODE_VERSION } else { $DefaultNodeVersion }
    try { $requestedNodeVersion = [version]$managedVersion } catch { Fail "invalid managed Node.js version: $managedVersion" }
    if ($requestedNodeVersion -lt $MinimumNodeVersion) { Fail "managed Node.js version must be >=22.19.0: $managedVersion" }
    $architecture = if ([System.Runtime.InteropServices.RuntimeInformation]::OSArchitecture -eq "Arm64") { "arm64" } else { "x64" }
    $nodeRoot = Join-Path $ManagedRoot (Join-Path "node" ("v" + $managedVersion))
    $nodeDirectory = $nodeRoot
    $managedNode = Join-Path $nodeRoot "node.exe"
    $managedNpm = Join-Path $nodeRoot "npm.cmd"
    if ((Test-Path -LiteralPath $managedNode) -and (Test-Path -LiteralPath $managedNpm)) {
        $installedVersion = (& $managedNode --version).Trim().TrimStart("v")
        if ($installedVersion -eq $managedVersion) {
            return [pscustomobject]@{ Node = $managedNode; Npm = $managedNpm; Source = "managed"; Version = $managedVersion }
        }
    }

    New-Item -ItemType Directory -Force -Path $TemporaryRoot | Out-Null
    $archiveName = "node-v{0}-win-{1}.zip" -f $managedVersion, $architecture
    $archivePath = Join-Path $TemporaryRoot $archiveName
    $checksumsPath = Join-Path $TemporaryRoot "SHASUMS256.txt"
    Download-File "https://nodejs.org/dist/v$managedVersion/$archiveName" $archivePath
    Download-File "https://nodejs.org/dist/v$managedVersion/SHASUMS256.txt" $checksumsPath
    $checksumLine = Select-String -LiteralPath $checksumsPath -Pattern ([regex]::Escape($archiveName) + "$") | Select-Object -First 1
    if (-not $checksumLine) { Fail "Node.js checksum manifest does not contain $archiveName" }
    $expected = ($checksumLine.Line -split "\s+")[0].ToLowerInvariant()
    if ((Get-Sha256 $archivePath) -ne $expected) { Fail "Node.js checksum mismatch for $archiveName" }

    $extractRoot = Join-Path $TemporaryRoot "node-extracted"
    Expand-Archive -LiteralPath $archivePath -DestinationPath $extractRoot -Force
    $extractedDirectory = Join-Path $extractRoot ("node-v{0}-win-{1}" -f $managedVersion, $architecture)
    if (-not (Test-Path -LiteralPath (Join-Path $extractedDirectory "node.exe"))) { Fail "downloaded Node.js archive is incomplete" }
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $nodeRoot) | Out-Null
    $stagedNodeRoot = "$nodeRoot.new"
    $previousNodeRoot = Join-Path $TemporaryRoot ("previous-node-" + [guid]::NewGuid().ToString("N"))
    if (Test-Path -LiteralPath $stagedNodeRoot) { Remove-Item -LiteralPath $stagedNodeRoot -Recurse -Force }
    Move-Item -LiteralPath $extractedDirectory -Destination $stagedNodeRoot
    $previousNodePresent = Test-Path -LiteralPath $nodeRoot
    if ($previousNodePresent) { Move-Item -LiteralPath $nodeRoot -Destination $previousNodeRoot }
    try {
        Move-Item -LiteralPath $stagedNodeRoot -Destination $nodeRoot
    } catch {
        if ($previousNodePresent -and (Test-Path -LiteralPath $previousNodeRoot)) { Move-Item -LiteralPath $previousNodeRoot -Destination $nodeRoot }
        throw
    }
    if ($previousNodePresent -and (Test-Path -LiteralPath $previousNodeRoot)) { Remove-Item -LiteralPath $previousNodeRoot -Recurse -Force }
    return [pscustomobject]@{ Node = $managedNode; Npm = $managedNpm; Source = "managed"; Version = $managedVersion }
}

function Get-BashPath {
    if ($env:DISCO_GIT_BASH_PATH -and (Test-Path -LiteralPath $env:DISCO_GIT_BASH_PATH)) { return $env:DISCO_GIT_BASH_PATH }
    $pathCommand = Get-Command bash.exe -ErrorAction SilentlyContinue
    if ($pathCommand -and (Test-Path -LiteralPath $pathCommand.Source)) { return $pathCommand.Source }
    $candidates = @()
    if ($env:ProgramFiles) { $candidates += Join-Path $env:ProgramFiles "Git\bin\bash.exe" }
    $programFilesX86 = [Environment]::GetEnvironmentVariable("ProgramFiles(x86)")
    if ($programFilesX86) { $candidates += Join-Path $programFilesX86 "Git\bin\bash.exe" }
    foreach ($candidate in $candidates) {
        if (Test-Path -LiteralPath $candidate) { return $candidate }
    }
    return $null
}

function Install-GitForWindows {
    $existing = Get-BashPath
    if ($existing) { return $existing }
    $winget = Get-Command winget.exe -ErrorAction SilentlyContinue
    if ($winget) {
        & $winget.Source install --id Git.Git --exact --scope user --silent --accept-source-agreements --accept-package-agreements
        $existing = Get-BashPath
        if ($existing) { return $existing }
    }

    # PortableGit is a user-local Git for Windows distribution that includes
    # bash.exe. The release API supplies a SHA-256 asset digest; refuse an
    # asset without that digest.
    New-Item -ItemType Directory -Force -Path $TemporaryRoot | Out-Null
    $release = Invoke-RestMethod -Uri "https://api.github.com/repos/git-for-windows/git/releases/latest" -Headers @{ "User-Agent" = "AREX-Skill-DisCo-Installer" }
    $gitArchitecture = if ([System.Runtime.InteropServices.RuntimeInformation]::OSArchitecture -eq "Arm64") { "arm64" } else { "64-bit" }
    $asset = $release.assets | Where-Object { $_.name -match "^PortableGit-.*-$gitArchitecture\.7z\.exe$" } | Select-Object -First 1
    if (-not $asset) { Fail "could not find a Git for Windows PortableGit asset for $gitArchitecture" }
    if (-not $asset.digest -or -not $asset.digest.StartsWith("sha256:")) { Fail "Git for Windows asset did not provide a SHA-256 digest" }
    $gitArchive = Join-Path $TemporaryRoot $asset.name
    Download-File $asset.browser_download_url $gitArchive
    if ((Get-Sha256 $gitArchive) -ne $asset.digest.Substring(7).ToLowerInvariant()) { Fail "Git for Windows checksum mismatch for $($asset.name)" }
    $gitVersion = if ($asset.name -match "^PortableGit-([0-9.]+)-") { $Matches[1] } else { $release.tag_name.TrimStart("v") }
    $gitRoot = Join-Path $ManagedRoot (Join-Path "git" $gitVersion)
    $gitStage = "$gitRoot.new"
    if (Test-Path -LiteralPath $gitStage) { Remove-Item -LiteralPath $gitStage -Recurse -Force }
    New-Item -ItemType Directory -Force -Path $gitStage | Out-Null
    & $gitArchive "-y" "-o$gitStage"
    if ($LASTEXITCODE -ne 0) {
        Remove-Item -LiteralPath $gitStage -Recurse -Force -ErrorAction SilentlyContinue
        Fail "Git for Windows PortableGit extraction failed with exit code $LASTEXITCODE"
    }
    $postInstall = Join-Path $gitStage "post-install.bat"
    if (Test-Path -LiteralPath $postInstall) {
        $postInstallResult = Start-Process -FilePath $env:ComSpec -ArgumentList @("/d", "/c", "`"$postInstall`"") -WorkingDirectory $gitStage -Wait -PassThru -WindowStyle Hidden
        if ($postInstallResult.ExitCode -ne 0) {
            Remove-Item -LiteralPath $gitStage -Recurse -Force -ErrorAction SilentlyContinue
            Fail "Git for Windows PortableGit post-install failed with exit code $($postInstallResult.ExitCode)"
        }
    }
    $bash = Join-Path $gitStage "usr\bin\bash.exe"
    if (-not (Test-Path -LiteralPath $bash)) {
        Remove-Item -LiteralPath $gitStage -Recurse -Force -ErrorAction SilentlyContinue
        Fail "Git for Windows PortableGit archive did not contain usr\bin\bash.exe"
    }
    if (Test-Path -LiteralPath $gitRoot) { Remove-Item -LiteralPath $gitRoot -Recurse -Force }
    Move-Item -LiteralPath $gitStage -Destination $gitRoot
    return (Join-Path $gitRoot "usr\bin\bash.exe")
}

function Resolve-SettingsShell([string]$BashPath) {
    if ($SkipBashCheck) { return }
    $settingsPath = Join-Path $AgentDir "settings.json"
    $settings = [pscustomobject]@{}
    if (Test-Path -LiteralPath $settingsPath) {
        $raw = Get-Content -LiteralPath $settingsPath -Raw
        if ($raw.Trim()) { $settings = $raw | ConvertFrom-Json }
    }
    $existing = if ($settings.PSObject.Properties.Name -contains "shellPath") { [string]$settings.shellPath } else { $null }
    if ($existing) {
        $expanded = $existing.Replace("~", $env:USERPROFILE)
        if (-not (Test-Path -LiteralPath $expanded)) { Fail "settings.json already has an invalid shellPath ($existing); fix it before running the managed installer" }
        return
    }
    if (-not $BashPath) { Fail "no bash.exe was found and Git for Windows could not be prepared" }
    $settings | Add-Member -NotePropertyName shellPath -NotePropertyValue $BashPath -Force
    New-Item -ItemType Directory -Force -Path $AgentDir | Out-Null
    $temporary = "$settingsPath.$([guid]::NewGuid().ToString('N')).tmp"
    try {
        Write-Utf8NoBom $temporary (($settings | ConvertTo-Json -Depth 100) + [Environment]::NewLine)
        Move-Item -LiteralPath $temporary -Destination $settingsPath -Force
    } catch {
        Remove-Item -LiteralPath $temporary -Force -ErrorAction SilentlyContinue
        throw
    }
}

function Get-ConfiguredShellPath {
    $settingsPath = Join-Path $AgentDir "settings.json"
    if (-not (Test-Path -LiteralPath $settingsPath)) { return $null }
    $raw = Get-Content -LiteralPath $settingsPath -Raw
    if (-not $raw.Trim()) { return $null }
    $settings = $raw | ConvertFrom-Json
    if ($settings.PSObject.Properties.Name -contains "shellPath" -and $settings.shellPath) {
        $expanded = ([string]$settings.shellPath).Replace("~", $env:USERPROFILE)
        if (-not (Test-Path -LiteralPath $expanded)) { Fail "settings.json already has an invalid shellPath ($($settings.shellPath)); fix it before running the managed installer" }
        return $expanded
    }
    return $null
}

function Write-Utf8NoBom([string]$Path, [string]$Content) {
    $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($Path, $Content, $utf8NoBom)
}

function ConvertTo-CmdValue([string]$Value) {
    if ($Value.Contains("%")) { Fail "managed install paths containing '%' are not supported by the Windows launcher" }
    return $Value.Replace('"', '""')
}

function Write-Launcher {
    $launcherDir = Join-Path $AgentDir "bin"
    $launcher = Join-Path $launcherDir "disco.cmd"
    New-Item -ItemType Directory -Force -Path $launcherDir | Out-Null
    if (Test-Path -LiteralPath $launcher) {
        $existing = Get-Content -LiteralPath $launcher -Raw
        if (-not $existing.Contains($ManagedRoot)) { Fail "$launcher already exists and is not owned by the DisCo managed installer" }
    }
    $content = @'
@echo off
setlocal
set "DISCO_MANAGED_INSTALL=1"
set "DISCO_MANAGED_INSTALL_DIR=__INSTALL_DIR__"
set "DISCO_MANAGED_INSTALLER=__INSTALLER__"
set "DISCO_MANAGED_INSTALL_MARKER=__MARKER__"
set "DISCO_CODING_AGENT_DIR=__AGENT_DIR__"
for /f "usebackq delims=" %%V in ("__CURRENT__") do set "DISCO_MANAGED_VERSION=%%V"
for /f "usebackq delims=" %%N in ("__NODE_FILE__") do set "DISCO_MANAGED_NODE_PATH=%%N"
set "DISCO_MANAGED_ENTRYPOINT=%DISCO_MANAGED_INSTALL_DIR%\releases\%DISCO_MANAGED_VERSION%\node_modules\@arex-skill\disco\dist\cli.js"
if not exist "%DISCO_MANAGED_ENTRYPOINT%" exit /b 1
"%DISCO_MANAGED_NODE_PATH%" "%DISCO_MANAGED_ENTRYPOINT%" %*
exit /b %ERRORLEVEL%
'@
    $content = $content.Replace("__INSTALL_DIR__", (ConvertTo-CmdValue $ManagedRoot))
    $content = $content.Replace("__INSTALLER__", (ConvertTo-CmdValue (Join-Path $ManagedRoot "install-disco.ps1")))
    $content = $content.Replace("__MARKER__", (ConvertTo-CmdValue (Join-Path $ManagedRoot "managed-install.json")))
    $content = $content.Replace("__AGENT_DIR__", (ConvertTo-CmdValue $AgentDir))
    $content = $content.Replace("__CURRENT__", (ConvertTo-CmdValue (Join-Path $ManagedRoot "current-version")))
    $content = $content.Replace("__NODE_FILE__", (ConvertTo-CmdValue (Join-Path $ManagedRoot "node-path")))
    $temporary = "$launcher.$([guid]::NewGuid().ToString('N')).tmp"
    $content | Set-Content -LiteralPath $temporary -Encoding ASCII
    Move-Item -LiteralPath $temporary -Destination $launcher -Force
}

function Write-Marker([string]$NodePath, [string]$NodeSource, [string]$NodeVersion, [string]$EntryPoint, [string]$InstallerPath, [string]$BashPath) {
    $marker = [ordered]@{
        schemaVersion = 1
        packageName = $PackageName
        activeVersion = $Version
        installDir = $ManagedRoot
        entrypoint = $EntryPoint
        nodeSource = $NodeSource
        nodeVersion = $NodeVersion
        nodePath = $NodePath
        installerPath = $InstallerPath
        bashPath = $BashPath
        platform = "windows-$([System.Runtime.InteropServices.RuntimeInformation]::OSArchitecture.ToString().ToLowerInvariant())"
    }
    $markerPath = Join-Path $ManagedRoot "managed-install.json"
    $temporary = "$markerPath.$([guid]::NewGuid().ToString('N')).tmp"
    try {
        Write-Utf8NoBom $temporary (($marker | ConvertTo-Json -Depth 10) + [Environment]::NewLine)
        Move-Item -LiteralPath $temporary -Destination $markerPath -Force
    } catch {
        Remove-Item -LiteralPath $temporary -Force -ErrorAction SilentlyContinue
        throw
    }
}

function Write-AtomicText([string]$Path, [string]$Content) {
    $temporary = "$Path.$([guid]::NewGuid().ToString('N')).tmp"
    $Content | Set-Content -LiteralPath $temporary -Encoding ASCII
    Move-Item -LiteralPath $temporary -Destination $Path -Force
}

function Save-OptionalFile([string]$Path, [string]$BackupPath) {
    if (Test-Path -LiteralPath $Path) {
        Copy-Item -LiteralPath $Path -Destination $BackupPath -Force
        return $true
    }
    return $false
}

function Restore-OptionalFile([string]$Path, [string]$BackupPath, [bool]$WasPresent) {
    if ($WasPresent) {
        Copy-Item -LiteralPath $BackupPath -Destination $Path -Force
    } elseif (Test-Path -LiteralPath $Path) {
        Remove-Item -LiteralPath $Path -Force
    }
}

function Ensure-PersistedInstaller {
    $destination = Join-Path $ManagedRoot "install-disco.ps1"
    $samePath = $PSCommandPath -and (Test-Path -LiteralPath $PSCommandPath) -and (Test-Path -LiteralPath $destination) -and ([IO.Path]::GetFullPath($PSCommandPath) -eq [IO.Path]::GetFullPath($destination))
    if ($PSCommandPath -and (Test-Path -LiteralPath $PSCommandPath) -and -not $samePath) { Copy-Item -LiteralPath $PSCommandPath -Destination $destination -Force }
    elseif (-not $samePath) { Download-File $InstallerUrl $destination }
    return $destination
}

function Resolve-PackageVersion([string]$NpmPath) {
    $resolved = $Version
    if (-not $resolved -or $resolved -eq "latest") {
        $npmArgs = @("view", "$PackageName@latest", "version", "--json")
        if ($env:DISCO_NPM_REGISTRY) { $npmArgs += @("--registry", $env:DISCO_NPM_REGISTRY) }
        $resolved = ((& $NpmPath @npmArgs) -join "").Trim().Trim('"')
        if ($LASTEXITCODE -ne 0) { Fail "could not resolve the latest $PackageName version from npm" }
    }
    if ($resolved -notmatch '^[0-9]+\.[0-9]+\.[0-9]+$') { Fail "invalid DisCo version: $resolved" }
    return $resolved
}

function Test-CommandConflict {
    $existing = Get-Command disco.cmd -ErrorAction SilentlyContinue
    if (-not $existing) { $existing = Get-Command disco -ErrorAction SilentlyContinue }
    if ($existing) {
        $managedLauncher = Join-Path $AgentDir "bin\disco.cmd"
        if ([IO.Path]::GetFullPath($existing.Source) -ne [IO.Path]::GetFullPath($managedLauncher)) { Fail "disco already resolves to $($existing.Source); refusing to overwrite an unrelated installation" }
    }
}

function Uninstall-Managed {
    $markerPath = Join-Path $ManagedRoot "managed-install.json"
    if (-not (Test-Path -LiteralPath $markerPath)) { Fail "$ManagedRoot is not a recognized DisCo managed install" }
    $marker = Get-Content -LiteralPath $markerPath -Raw | ConvertFrom-Json
    if ($marker.packageName -ne $PackageName) { Fail "managed install marker package name does not match $PackageName" }
    $launcher = Join-Path $AgentDir "bin\disco.cmd"
    if (Test-Path -LiteralPath $launcher) {
        $content = Get-Content -LiteralPath $launcher -Raw
        if ($content.Contains($ManagedRoot)) { Remove-Item -LiteralPath $launcher -Force }
    }
    Remove-Item -LiteralPath $ManagedRoot -Recurse -Force
    Write-Output "Removed DisCo managed files under $ManagedRoot; user settings, credentials, sessions, and skills were preserved."
}

try {
    if ($Uninstall -and -not (Test-Path -LiteralPath $ManagedRoot)) { Fail "$ManagedRoot is not a recognized DisCo managed install" }
    New-Item -ItemType Directory -Force -Path $ManagedRoot | Out-Null
    $Mutex = New-Object System.Threading.Mutex($false, "Local\DisCoManagedInstaller")
    if (-not $Mutex.WaitOne(0)) { Fail "another DisCo managed installer is already running" }
    if ($Uninstall) { Uninstall-Managed; exit 0 }
    if ($Update) {
        $markerPath = Join-Path $ManagedRoot "managed-install.json"
        if (-not (Test-Path -LiteralPath $markerPath)) { Fail "$ManagedRoot is not a recognized DisCo managed install" }
        $existingMarker = Get-Content -LiteralPath $markerPath -Raw | ConvertFrom-Json
        if ($existingMarker.packageName -ne $PackageName) { Fail "managed install marker package name does not match $PackageName" }
    }

    New-Item -ItemType Directory -Force -Path $TemporaryRoot | Out-Null
    $runtime = Get-NodeRuntime
    $Version = Resolve-PackageVersion $runtime.Npm
    $persistedInstaller = Ensure-PersistedInstaller
    $configuredShell = if ($SkipBashCheck) { $null } else { Get-ConfiguredShellPath }
    $bashPath = if ($SkipBashCheck -or $configuredShell) { $configuredShell } else { Install-GitForWindows }
    Resolve-SettingsShell $bashPath
    if (-not $SkipBashCheck) {
        if (-not $bashPath) { Fail "no bash.exe was found and Git for Windows could not be prepared" }
        & $bashPath "-c" "exit 0"
        if ($LASTEXITCODE -ne 0) { Fail "bash smoke check failed for $bashPath" }
    }
    Test-CommandConflict

    $releaseStage = Join-Path $ManagedRoot ("releases\.stage-$Version-" + [guid]::NewGuid().ToString("N"))
    $releaseDir = Join-Path $ManagedRoot ("releases\" + $Version)
    New-Item -ItemType Directory -Force -Path $releaseStage | Out-Null
    $npmArguments = @("install", "--prefix", $releaseStage, "--ignore-scripts", "--omit=dev", "--no-audit", "--no-fund", "$PackageName@$Version")
    if ($env:DISCO_NPM_REGISTRY) { $npmArguments += @("--registry", $env:DISCO_NPM_REGISTRY) }
    & $runtime.Npm @npmArguments
    if ($LASTEXITCODE -ne 0) { Fail "failed to install $PackageName@$Version into the managed staging directory" }

    $packageDir = Join-Path $releaseStage "node_modules\@arex-skill\disco"
    $packageJsonPath = Join-Path $packageDir "package.json"
    $entryPoint = Join-Path $packageDir "dist\cli.js"
    if (-not (Test-Path -LiteralPath $packageJsonPath) -or -not (Test-Path -LiteralPath $entryPoint)) { Fail "managed npm install did not produce a complete DisCo package" }
    $installedPackage = Get-Content -LiteralPath $packageJsonPath -Raw | ConvertFrom-Json
    if ($installedPackage.version -ne $Version) { Fail "managed package version mismatch: expected $Version, got $($installedPackage.version)" }
    & $runtime.Node $entryPoint --version | Out-Null
    if ($LASTEXITCODE -ne 0) { Fail "managed DisCo smoke check failed" }

    $rollbackDir = Join-Path $TemporaryRoot ("previous-release-" + [guid]::NewGuid().ToString("N"))
    $backupDir = Join-Path $TemporaryRoot ("previous-state-" + [guid]::NewGuid().ToString("N"))
    New-Item -ItemType Directory -Force -Path $backupDir | Out-Null
    $oldReleasePresent = Test-Path -LiteralPath $releaseDir
    $oldMarkerPresent = Save-OptionalFile (Join-Path $ManagedRoot "managed-install.json") (Join-Path $backupDir "managed-install.json")
    $oldCurrentPresent = Save-OptionalFile (Join-Path $ManagedRoot "current-version") (Join-Path $backupDir "current-version")
    $oldNodePresent = Save-OptionalFile (Join-Path $ManagedRoot "node-path") (Join-Path $backupDir "node-path")
    $oldLauncherPath = Join-Path $AgentDir "bin\disco.cmd"
    $oldLauncherPresent = Save-OptionalFile $oldLauncherPath (Join-Path $backupDir "disco.cmd")
    if ($oldReleasePresent) { Move-Item -LiteralPath $releaseDir -Destination $rollbackDir }

    try {
        Move-Item -LiteralPath $releaseStage -Destination $releaseDir
        Write-AtomicText (Join-Path $ManagedRoot "node-path") ($runtime.Node + [Environment]::NewLine)
        Write-Marker $runtime.Node $runtime.Source $runtime.Version (Join-Path $releaseDir "node_modules\@arex-skill\disco\dist\cli.js") $persistedInstaller $bashPath
        Write-Launcher
        Write-AtomicText (Join-Path $ManagedRoot "current-version") ($Version + [Environment]::NewLine)
    } catch {
        if (Test-Path -LiteralPath $releaseDir) { Remove-Item -LiteralPath $releaseDir -Recurse -Force }
        if ($oldReleasePresent) { Move-Item -LiteralPath $rollbackDir -Destination $releaseDir }
        Restore-OptionalFile (Join-Path $ManagedRoot "managed-install.json") (Join-Path $backupDir "managed-install.json") $oldMarkerPresent
        Restore-OptionalFile (Join-Path $ManagedRoot "current-version") (Join-Path $backupDir "current-version") $oldCurrentPresent
        Restore-OptionalFile (Join-Path $ManagedRoot "node-path") (Join-Path $backupDir "node-path") $oldNodePresent
        Restore-OptionalFile $oldLauncherPath (Join-Path $backupDir "disco.cmd") $oldLauncherPresent
        Fail "could not activate managed DisCo release $Version; previous release restored: $($_.Exception.Message)"
    }
    if (Test-Path -LiteralPath $rollbackDir) { Remove-Item -LiteralPath $rollbackDir -Recurse -Force }
    if (Test-Path -LiteralPath $releaseStage) { Remove-Item -LiteralPath $releaseStage -Recurse -Force }

    Write-Output "Installed $PackageName@$Version using $($runtime.Source) Node.js under $ManagedRoot"
    Write-Output "DisCo launcher: $(Join-Path $AgentDir 'bin\disco.cmd')"
    Write-Output "Add $(Join-Path $AgentDir 'bin') to PATH if it is not already present, then run: disco --version"
} catch {
    if ($releaseStage -and (Test-Path -LiteralPath $releaseStage)) {
        Remove-Item -LiteralPath $releaseStage -Recurse -Force -ErrorAction SilentlyContinue
    }
    Write-Error "error: $($_.Exception.Message)"
    exit 1
} finally {
    if ($Mutex) {
        try { $Mutex.ReleaseMutex() | Out-Null } catch {}
        $Mutex.Dispose()
    }
    if (Test-Path -LiteralPath $TemporaryRoot) { Remove-Item -LiteralPath $TemporaryRoot -Recurse -Force -ErrorAction SilentlyContinue }
}
