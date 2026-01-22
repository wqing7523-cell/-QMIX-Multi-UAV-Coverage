# QMIX-Based Multi-UAV Cooperative Coverage Path Planning

This repository contains the implementation of a QMIX-based multi-agent reinforcement learning framework for cooperative coverage path planning in multi-UAV systems. The framework addresses coverage path planning challenges in large-scale environments with dense obstacles.

## Features

- **Multi-agent Reinforcement Learning**: QMIX-based centralized training and distributed execution paradigm
- **Potential-based Reward Shaping**: Unvisited distance potential and obstacle clarity potential
- **Dynamic Exploration-Recovery Mechanism**: Improves training stability in high obstacle density environments
- **Scalable Architecture**: Supports multiple map sizes (12×12, 16×16, 24×24) and UAV configurations (4-6 UAVs)
- **Comprehensive Evaluation**: Systematic experiments under 24 configurations with different obstacle densities

## Project Structure

```
├── src/                    # Source code
│   ├── envs/              # Grid world environment with obstacles
│   ├── algos/             # Algorithms (Q-Learning baseline, QMIX)
│   │   ├── qlearning/     # Q-Learning implementations
│   │   └── qmix/          # QMIX implementation
│   ├── metrics/           # Performance metrics
│   ├── runners/           # Training and evaluation scripts
│   └── utils/             # Utility functions
├── configs/                # Configuration files
│   ├── algos/             # Algorithm configurations
│   └── envs/              # Environment configurations
├── experiments/            # Experimental results
│   ├── figures/           # Generated figures
│   └── tables/            # Result tables
└── scripts/                # Helper scripts
```

## Installation

### Requirements

- Python >= 3.8
- PyTorch >= 2.0.0
- See `requirements.txt` for full dependencies

### Setup

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/REPO_NAME.git
cd REPO_NAME

# Install dependencies
pip install -r requirements.txt
```

## Usage

### Training

```bash
# Train QMIX model with default configuration
python src/algos/qmix/train_qmix.py --config configs/algos/qmix_full.yaml

# Train with custom configuration
python src/algos/qmix/train_qmix.py --config configs/algos/qmix_full.yaml --map_size 24 --num_uavs 6
```

### Evaluation

```bash
# Evaluate trained model
python src/runners/eval.py --checkpoint experiments/checkpoints/best_model.pth
```

### Running Experiments

```bash
# Run ablation experiments
python run_ablation_experiments.py
```

## Experimental Results

The framework achieves:
- **97.8%** coverage rate in obstacle-free environments
- **77.5%** average coverage rate under high obstacle density (0.20)
- **76.3%** coverage rate in 24×24 map with 6 UAVs
- **4%** training failure rate (reduced from 18% with recovery mechanism)

## Citation

If you use this code in your research, please cite:

```bibtex
@article{your_paper_2024,
  title={QMIX-Based Cooperative Coverage Path Planning for Multi-UAV Systems: Scalability and Robustness in Grid-Based Environments},
  author={Your Name and Co-authors},
  journal={Journal of Intelligent \& Robotic Systems},
  year={2024}
}
```

## License

[Specify your license here, e.g., MIT License]

## Contact

For questions or issues, please open an issue on GitHub or contact [your email].

## Acknowledgments

[Add acknowledgments if applicable]
