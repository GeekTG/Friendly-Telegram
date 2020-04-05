#    Friendly Telegram (telegram userbot)
#    Copyright (C) 2018-2019 The Authors

#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.

#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.

if (Test-Path "friendly-telegram" -PathType Container) {
    if (Test-Path (Join-Path "friendly-telegram" "friendly-telegram") -PathType Container) {
        Set-Location "friendly-telegram"
    }
    python -m friendly-telegram
    exit
}

Write-Output("Downloading Python...")
Invoke-WebRequest -Uri "https://www.python.org/ftp/python/3.7.4/python-3.7.4.exe" -OutFile (Join-Path $env:TEMP "python-installer.exe")
Write-Output("Installing Python...")
Start-Process (Join-Path $env:TEMP "python-installer.exe") @("/quiet"; "InstallAllUsers=0"; "PrependPath=1"; "Include_test=0"; "InstallLauncherAllUsers=0") -Wait
Write-Output("Locating Git...")
$ret = Invoke-RestMethod -Uri "https://api.github.com/repos/git-for-windows/git/releases" -Headers @{'User-Agent'='friendly-telegram installer'}
foreach ($release in $ret) {
    $asset_id = $release.assets | Where {$_.name -Match ("^Git-[0-9]+\.[0-9]+\.[0-9]+-" +  (Get-WmiObject -Class Win32_OperatingSystem -ComputerName $env:computername -ea 0).OSArchitecture + ".exe$")} | % {$_.id}
    if (-not [string]::IsNullOrEmpty($asset_id)) {
        break
    }
}
if ([string]::IsNullOrEmpty($asset_id)) {
    Write-Error "Unable to locate Git"
    exit
}
$download_url = "https://api.github.com/repos/git-for-windows/git/releases/assets/" + $asset_id
Write-Output("Downloading Git...")
Invoke-WebRequest -Uri $download_url -OutFile (Join-Path $env:TEMP "git-scm-installer.exe") -Headers @{'User-Agent'='friendly-telegram installer'; 'Accept'='application/octet-stream'}
Write-Output("Installing Git...")
Start-Process (Join-Path $env:TEMP "git-scm-installer.exe") @("/VERYSILENT"; "/NORESTART"; "/NOCANCEL"; "/SP-"; "/CURRENTUSER"; "/NOCLOSEAPPLICATIONS"; "/NORESTARTAPPLICATIONS"; '/COMPONENTS=""') -Wait
Write-Output("Done")

# https://stackoverflow.com/a/31845512
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
git clone https://gitlab.com/friendly-telegram/friendly-telegram

Set-Location friendly-telegram
python -m pip install -r requirements.txt
python -m friendly-telegram
python -m friendly-telegram # TODO pass args
