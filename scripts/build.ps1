$projectPath = (get-item $PSScriptRoot ).parent.FullName

# CONFIG
$ffmpegVersion = "4.4.1-3"
$ffmpegUrl = "https://repo.jellyfin.org/releases/server/windows/versions/jellyfin-ffmpeg/4.4.1-3/jellyfin-ffmpeg_4.4.1-3-windows_win64.zip"
$nodeVersion = "16.15.0"
$nodeUrl = "https://nodejs.org/dist/v$nodeVersion/node-v$nodeVersion-win-x64.zip"

# Ensure the dependencies directory exists
if (!(Test-Path "$projectPath\build\dependencies")) {
    New-Item $projectPath\build\dependencies -ItemType Directory
    Write-Host "Dependencies directory created successfully"
}

# Create venv
Write-Output "Setup Python build environment"
Set-Location -Path $projectPath
# Ensure venv exists
if (!(Test-Path "$projectPath\venv")) {
    python -m venv venv
}
# Activate the venv
.\venv\Scripts\Activate.ps1
# Install Unmanic Launcher Python dependencies
python -m pip install --upgrade -r requirements.txt -r requirements-dev.txt


# Create wheels for all Unmanic Launcher dependencies
Write-Output "Create wheels for all Unmanic Launcher dependencies"
Set-Location -Path $projectPath
if (Test-Path "$projectPath\build\dependencies\wheels") {
    Remove-Item -Recurse -Force "$projectPath\build\dependencies\wheels"
}
python -m pip wheel --wheel-dir build\dependencies\wheels -r requirements.txt


# Fetch NodeJS
Write-Output "Fetch NodeJS"
Set-Location -Path $projectPath
if (!(Test-Path "build\dependencies\node-v$nodeVersion-win-x64.zip")) {
    Invoke-WebRequest -Uri $nodeUrl -OutFile build\dependencies\node-v$nodeVersion-win-x64.zip
    if (Test-Path "$projectPath\build\dependencies\node\node.exe") {
        Remove-Item -Path "$projectPath\build\dependencies\node\node.exe"
    }
}
if (!(Test-Path "$projectPath\build\dependencies\node\node.exe")) {
    if (Test-Path "$projectPath\build\dependencies\node-v$nodeVersion-win-x64") {
        Remove-Item -Recurse -Force "$projectPath\build\dependencies\node-v$nodeVersion-win-x64"
    }
    Expand-Archive -LiteralPath $projectPath\build\dependencies\node-v$nodeVersion-win-x64.zip -DestinationPath $projectPath\build\dependencies
    if (Test-Path "$projectPath\build\dependencies\node") {
        Remove-Item -Recurse -Force "$projectPath\build\dependencies\node"
    }
    Rename-Item $projectPath\build\dependencies\node-v$nodeVersion-win-x64 $projectPath\build\dependencies\node
}


# Fetch FFmpeg
Write-Output "Fetch FFmpeg"
Set-Location -Path $projectPath
if (!(Test-Path "build\dependencies\jellyfin-ffmpeg-$ffmpegVersion.zip")) {
    Invoke-WebRequest -Uri $ffmpegUrl -OutFile build\dependencies\jellyfin-ffmpeg-$ffmpegVersion.zip
    if (Test-Path "$projectPath\build\dependencies\ffmpeg\ffmpeg.exe") {
        Remove-Item -Path "$projectPath\build\dependencies\ffmpeg\ffmpeg.exe"
    }
}
if (!(Test-Path "$projectPath\build\dependencies\ffmpeg\ffmpeg.exe")) {
    if (Test-Path "$projectPath\build\dependencies\ffmpeg") {
        Remove-Item -Recurse -Force "$projectPath\build\dependencies\ffmpeg"
    }
    Expand-Archive -LiteralPath $projectPath\build\dependencies\jellyfin-ffmpeg-$ffmpegVersion.zip -DestinationPath $projectPath\build\dependencies\ffmpeg
}


# Set project version
Write-Output "Set project version"
Set-Location -Path $projectPath
$semVer = build\tools\gitversion\gitversion.exe /showvariable SemVer
(Get-Content config\windows\installer.cfg ) -Replace 'version=0.0.1', "version=$semVer" | Set-Content installer.configured.cfg


# Pack project
Write-Output "Pack project v$semVer"
Set-Location -Path $projectPath
python -m nsist installer.configured.cfg --no-makensis

# Print next steps
$makensisPath = (python -c "import nsist; print(nsist.find_makensis_win())") -join "`n"
Write-Output "Project built. To package the project, run:"
Write-Output "      & '$makensisPath' .\build\nsis\installer.nsi\"
