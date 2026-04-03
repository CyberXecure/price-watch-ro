param(
    [Parameter(Mandatory = $true)]
    [int]$WatchlistId,

    [Parameter(Mandatory = $true)]
    [int]$ItemId
)

Set-Location "D:\dev\projects\price-watch-ro\services\api"
.\.venv\Scripts\Activate.ps1
python .\refresh_rendered_item.py $WatchlistId $ItemId
