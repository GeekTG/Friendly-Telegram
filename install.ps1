Write-Output("Downloading Python...")
Invoke-WebRequest -Uri "https://www.python.org/ftp/python/3.7.4/python-3.7.4.exe" -OutFile (Join-Path $env:TEMP "python-installer.exe")
Write-Output("Installing Python...")
Start-Process (Join-Path $env:TEMP "python-installer.exe") @("/quiet"; "InstallAllUsers=0"; "PrependPath=1"; "Include_test=0"; "InstallLauncherAllUsers=0") -Wait
Write-Output("Locating Git...")
$ret = Invoke-RestMethod -Uri "https://api.github.com/repos/git-for-windows/git/releases/latest" -Headers @{'User-Agent'='friendly-telegram installer'}
$asset_id = $ret.assets | Where {$_.name -Match "^MinGit-[0-9]+\.[0-9]+\.[0-9]+-64-bit.exe$"} | % {$_.id}
$download_url = "https://api.github.com/repos/git-for-windows/git/releases/assets/" + $asset_id
Write-Output("Downloading Git...")
Invoke-WebRequest -Uri $download_url -OutFile (Join-Path $env:TEMP "git-scm-installer.exe") -Headers @{'User-Agent'='friendly-telegram installer'; 'Accept'='application/octet-stream'}
Write-Output("Installing Git...")
Start-Process (Join-Path $env:TEMP "git-scm-installer.exe") @("/VERYSILENT"; "/NORESTART"; "/NOCANCEL"; "/SP-"; "/CURRENTUSER"; "/NOCLOSEAPPLICATIONS"; "/NORESTARTAPPLICATIONS"; '/COMPONENTS=""') -Wait
Write-Output("Done")
git clone https://github.com/friendly-telegram/friendly-telegram
Set-Location friendly-telegram
python -m pip install -r requirements.txt
python -m friendly-telegram
python -m friendly-telegram # TODO pass args
