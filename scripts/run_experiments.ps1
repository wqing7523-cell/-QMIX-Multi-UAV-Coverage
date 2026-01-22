param(
    [string]$Maps = 'grid_small grid_obstacle',
    [string]$MapIndices = '0 1 2 3 4',
    [string]$UavIndices = '0 1 2',
    [string]$Algorithms = 'qlearning qlearning_per qmix',
    [int]$Seed = 123
)

function Split-List([string]$input) {
    return ($input -split '[,\s]+' | Where-Object { $_ -ne '' })
}

$Maps = Split-List $Maps
$MapIndices = Split-List $MapIndices | ForEach-Object { [int]$_ }
$UavIndices = Split-List $UavIndices | ForEach-Object { [int]$_ }
$Algorithms = Split-List $Algorithms

Write-Host ("Maps: {0}" -f ($Maps -join ', ')) -ForegroundColor Yellow
Write-Host ("MapIndices: {0}" -f ($MapIndices -join ', ')) -ForegroundColor Yellow
Write-Host ("UavIndices: {0}" -f ($UavIndices -join ', ')) -ForegroundColor Yellow
Write-Host ("Algorithms: {0}" -f ($Algorithms -join ', ')) -ForegroundColor Yellow

$baseConfig = 'configs/base.yaml'

foreach ($map in $Maps) {
    Write-Host "Processing map: $map" -ForegroundColor Green
    $envConfig = "configs/envs/$map.yaml"
    foreach ($algo in $Algorithms) {
        Write-Host "  Algorithm: $algo" -ForegroundColor Green
        if ($algo -eq 'qlearning') {
            $algoConfig = 'configs/algos/qlearning.yaml'
            $module = 'src.algos.qlearning.train_qlearning'
        } elseif ($algo -eq 'qlearning_per') {
            $algoConfig = 'configs/algos/qlearning_per_uav.yaml'
            $module = 'src.algos.qlearning.train_qlearning'
        } else {
            $algoConfig = 'configs/algos/qmix.yaml'
            $module = 'src.algos.qmix.train_qmix'
        }
        foreach ($mapIdx in $MapIndices) {
            Write-Host "    Map index: $mapIdx" -ForegroundColor DarkCyan
            foreach ($uavIdx in $UavIndices) {
                Write-Host "      Running $algo on $map (mapIdx=$mapIdx, uavIdx=$uavIdx)" -ForegroundColor Cyan
                try {
                    .\.venv\Scripts\python.exe -m $module `
                        --base-config $baseConfig `
                        --env-config $envConfig `
                        --algo-config $algoConfig `
                        --seed $Seed `
                        --map-index $mapIdx `
                        --uav-index $uavIdx
                } catch {
                    Write-Host "      Failed: $($_.Exception.Message)" -ForegroundColor Red
                }
            }
        }
    }
}

Write-Host 'All runs completed' -ForegroundColor Green
