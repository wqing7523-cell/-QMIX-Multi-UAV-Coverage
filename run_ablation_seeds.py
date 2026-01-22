"""
多 seed 消融实验脚本：只比较 Baseline vs 完整模型（表 5 用）

默认跑 3 个随机种子：
- 42
- 1234
- 2025

每个 seed 下运行两组配置：
- Baseline（无势能奖励、无动态恢复）
- Full（有势能奖励、有动态恢复）
"""
import subprocess
import sys
from pathlib import Path

# 只比较 Baseline vs Full
EXPERIMENTS = [
    {
        "name": "baseline",
        "algo_config": "configs/algos/qmix_baseline.yaml",
        "description": "Baseline（无势能奖励、无动态恢复）",
    },
    {
        "name": "full",
        "algo_config": "configs/algos/qmix_full.yaml",
        "description": "完整模型（有势能奖励、有动态恢复）",
    },
]

# 多个随机种子（你可以按需修改）
SEEDS = [42, 1234, 2025]

ENV_CONFIG = "configs/envs/grid_ablation.yaml"
BASE_CONFIG = "configs/base.yaml"


def run_single(config: dict, seed: int) -> bool:
    """运行单个配置 + 单个 seed"""
    print("\n" + "=" * 60)
    print(f"配置: {config['description']}")
    print(f"Seed: {seed}")
    print(f"算法配置: {config['algo_config']}")
    print("=" * 60 + "\n")

    cmd = [
        sys.executable,
        "-m",
        "src.algos.qmix.train_qmix",
        "--env-config",
        ENV_CONFIG,
        "--algo-config",
        config["algo_config"],
        "--seed",
        str(seed),
        "--map-index",
        "0",
        "--uav-index",
        "0",
        "--obstacle-index",
        "0",
    ]

    if Path(BASE_CONFIG).exists():
        cmd.extend(["--base-config", BASE_CONFIG])

    try:
        subprocess.run(cmd, check=True, cwd=Path.cwd())
        print(f"\n✓ Seed={seed} | {config['description']} 实验完成")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n✗ Seed={seed} | {config['description']} 实验失败: {e}")
        return False


def main():
    """多 seed 消融实验入口"""
    print("=" * 60)
    print("开始运行多 seed 消融实验：Baseline vs 完整模型")
    print("=" * 60)
    print(f"环境配置: {ENV_CONFIG}")
    print(f"随机种子列表: {SEEDS}")
    print(f"实验配置数量: {len(EXPERIMENTS)}")
    print("=" * 60)
    print(
        "\n提示：每个实验（单个 seed + 单个配置）约需 9.8 GPU·h（RTX 4060），"
        "请根据 GPU 时间预算决定 SEEDS 的数量。\n"
    )

    results = []

    for seed in SEEDS:
        for cfg in EXPERIMENTS:
            ok = run_single(cfg, seed)
            results.append((seed, cfg["name"], ok))

    # 汇总结果
    print("\n" + "=" * 60)
    print("多 seed 消融实验汇总")
    print("=" * 60)
    for seed, name, ok in results:
        status = "✓ 成功" if ok else "✗ 失败"
        print(f"seed={seed:<6} {name:<12}: {status}")

    success_count = sum(1 for _, _, ok in results if ok)
    print(f"\n完成: {success_count}/{len(results)}")

    if success_count == len(results):
        print("\n所有实验已完成！")
        print("请在 experiments/logs/qmix.log 中按时间/seed 提取结果，")
        print("或后续编写解析脚本计算 mean ± 95% CI 与 Wilcoxon 检验。")
    else:
        print("\n部分实验失败，请检查错误信息。")


if __name__ == "__main__":
    main()


