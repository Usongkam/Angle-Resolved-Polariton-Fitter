# Angle-Resolved Polariton Fitter

中文说明 | English below

用于角分辨极化激元光谱数据的交互式选点与拟合桌面工具。当前公开版本以 `apps/V4` 为主。

## 中文简介

这个仓库提供一个面向角分辨反射/PL 光谱的 PyQt 桌面程序，主要功能包括：

- 对 cavity、LP、UP 分支进行交互式选点
- 支持 UP 等非连续分支的分段 trace
- 支持手动删点、框选删点和撤销
- 支持 `Cavity only`、`LP only` 和 `Coupled (LP+UP)` 拟合
- 提供 RMSE、weighted RMSE、LP/UP RMSE、seed source 等诊断信息
- 支持导出 report、fit CSV 和工作区图像

## 中文目录结构

- `apps/V4/`
  主程序与拟合后端。
- `data/example/`
  可作为示例使用的本地数据文件。
- `README.md`
  仓库说明。
- `requirements.txt`
  Python 依赖列表。

## 中文安装与运行

```bash
pip install -r requirements.txt
python apps/V4/app.py
```

如果系统中的 Python 命令不是 `python`，请改用你本机可用的解释器路径。

## English Overview

This repository provides an interactive desktop tool for tracing and fitting angle-resolved polariton spectroscopy data. The public release is centered on `apps/V4`.

Main capabilities:

- interactive tracing for cavity, LP, and UP branches
- segmented tracing for disconnected branches
- manual point cleanup with pick-delete, box-delete, and undo
- `Cavity only`, `LP only`, and `Coupled (LP+UP)` fitting modes
- diagnostics including RMSE, weighted RMSE, LP/UP RMSE, and seed source
- export of reports, fit CSV data, and workspace images

## Public Repository Layout

- `apps/V4/`
  Main application and fitting backend.
- `data/example/`
  Example local datasets.
- `README.md`
  Repository guide.
- `requirements.txt`
  Python dependencies.

## Installation and Launch

```bash
pip install -r requirements.txt
python apps/V4/app.py
```

If your system does not expose `python` directly, use the interpreter command available on your machine.
