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
- `AngleResolvedPolaritonFitter.spec`
  PyInstaller 的 onedir 打包配置。
- `build_release.ps1`
  Windows 下的打包脚本。
- `requirements.txt`
  运行依赖列表。

## 中文安装与运行

```bash
pip install -r requirements.txt
python apps/V4/app.py
```

如果系统中的 Python 命令不是 `python`，请改用你本机可用的解释器路径。

## 中文打包发布

推荐先打 `onedir` 版本，再考虑 `onefile`。对于 `PyQt6 + matplotlib` 桌面程序，`onedir` 更稳，也更容易排查缺失依赖。

### 方式 1：使用 spec 打包 onedir

```powershell
pip install pyinstaller
pyinstaller AngleResolvedPolaritonFitter.spec
```

### 方式 2：使用脚本打包

```powershell
./build_release.ps1
```

### 可选：打包 onefile

```powershell
./build_release.ps1 -OneFile
```

生成结果默认在 `dist/` 目录下。建议将 `dist/AngleResolvedPolaritonFitter/` 压缩为 zip 后上传到 GitHub Release。

### 中文发布建议

- 先在本机完整测试 `Load -> Apply -> Trace -> Fit -> Export`
- 优先发布 `onedir` 版本
- GitHub Release 建议上传一个 Windows zip，例如 `AngleResolvedPolaritonFitter-windows.zip`
- 如果示例数据要随 release 一起提供，请只放可公开的样例数据

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
- `AngleResolvedPolaritonFitter.spec`
  PyInstaller spec for the onedir build.
- `build_release.ps1`
  Windows packaging helper.
- `requirements.txt`
  Python dependencies.

## Installation and Launch

```bash
pip install -r requirements.txt
python apps/V4/app.py
```

If your system does not expose `python` directly, use the interpreter command available on your machine.

## English Packaging and Release

The recommended release path is `onedir` first, then `onefile` only if you specifically need a single executable. For `PyQt6 + matplotlib`, `onedir` is usually more reliable.

### Option 1: Build from the spec file

```powershell
pip install pyinstaller
pyinstaller AngleResolvedPolaritonFitter.spec
```

### Option 2: Build with the helper script

```powershell
./build_release.ps1
```

### Optional: Build onefile

```powershell
./build_release.ps1 -OneFile
```

Build artifacts are written to `dist/`. For GitHub Release uploads, package `dist/AngleResolvedPolaritonFitter/` into a zip archive and publish that archive.

### Release Notes Guidance

- test the full `Load -> Apply -> Trace -> Fit -> Export` workflow before publishing
- prefer the `onedir` release for the first public build
- upload a Windows zip asset to GitHub Release
- only include shareable example datasets
