
$BASEDIR = $PSScriptRoot
$HSDATA_URL = "https://github.com/HearthSim/hsdata.git"
$HSDATA_DIR = "$BASEDIR/hsdata"
$HEARTHFORGE_URL = "https://github.com/HearthSim/hearthforge.git"
$HEARTHFORGE_DIR = "$BASEDIR/assets"

Function FetchGit() {
    Param (
        [string]$src,
        [string]$dest
    )
	Write-Host "Fetching data files from $src"
	if (-not (Test-Path $dest) -or -not (Test-Path "$dest/.git")) {
		& git clone --depth=1 "$src" "$dest"
    } else {
		& git -C "$dest" fetch
		& git -C "$dest" reset --hard origin/master
    }
}

if (Get-Command "git.exe" -ErrorAction SilentlyContinue) {
    FetchGit $HSDATA_URL $HSDATA_DIR
    FetchGit $HEARTHFORGE_URL $HEARTHFORGE_DIR
} else {
    Write-Host -ForegroundColor Red "ERROR: git is required to bootstrap this project."
}