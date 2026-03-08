# Angle-Resolved Polariton Fitter

中文说明 | English below

用于角分辨极化激元光谱数据的交互式选点与拟合桌面工具。当前公开版本基于 `apps/V4`，并已经提供可直接下载的 Windows Release。

## 中文下载

如果你只是想直接使用程序，优先去 GitHub Releases 下载已经打包好的版本。

推荐下载：
- `AngleResolvedPolaritonFitter-windows.zip`
  推荐给大多数用户。解压后运行文件夹中的 `AngleResolvedPolaritonFitter.exe`。

备用下载：
- `AngleResolvedPolaritonFitter.exe`
  单文件版本，分发更方便，但启动通常比 zip 版本更慢。

## 中文简介

这个工具主要用于角分辨反射或 PL 光谱中的 cavity、LP、UP 分支选点与拟合。当前版本支持：

- 对 cavity、LP、UP 分支进行交互式选点
- 对 UP 等非连续分支进行分段 trace
- 手动删点、框选删点和撤销
- `Cavity only`、`LP only`、`Coupled (LP+UP)` 三种拟合模式
- 诊断输出，包括 RMSE、weighted RMSE、LP/UP RMSE、seed source
- 导出 report、fit CSV 和工作区图像

## 中文快速流程

典型使用顺序为：`Load -> Apply -> Start -> Trace -> Fit -> Export`

1. `Load`
   导入角分辨光谱数据文件。
2. `Apply`
   完成裁剪、角度映射和预处理。
3. `Start`
   在 `Interactive trace` 图中点击一个分支上的起点。
4. `Trace`
   对当前 branch 自动追踪点列。若分支不连续，可以先 trace 一段，再继续添加下一段。
5. `Fit`
   选择拟合模式并运行拟合，查看 Session 与残差图。
6. `Export`
   导出文本报告、CSV 或工作区图像。

## 中文详细使用流程

### 1. 导入数据

点击 `Load Data`，选择反射或 PL 数据文件。程序会读取矩阵并显示原始图像。

### 2. 预处理与裁剪

在 `Data` 标签页中设置裁剪与角度映射参数，然后点击 `Apply`。

- `Auto` 裁剪模式会根据角向轮廓自动找边界。
- `Manual` 模式可以直接输入左右边界，也可以在 `Raw / crop overview` 图中拖动边界线。

### 3. 设置起点并选点

切到 `Trace` 标签页，选择当前 branch（`Cavity` / `LP` / `UP`），然后在 `Interactive trace` 图中点击起点。

- 点击 `Trace New Segment` 会生成当前待提交的 segment。
- 点击 `Add Segment To Branch` 会把这一段正式并入当前 branch。
- 对于分成左右两段的 `UP`，可以重复执行“设起点 -> Trace New Segment -> Add Segment To Branch”。

### 4. 清理异常点

如果自动 trace 结果中有视觉异常点：

- 打开 `Edit Branch`
- 用 `Pick Delete` 删除单个点
- 用 `Box Delete` 批量删除框内点
- 用 `Undo Last Delete` 撤销最近一次删除

### 5. 运行拟合

切到 `Fit` 标签页，选择：

- `Coupled (LP+UP)`：同时拟合 LP 和 UP
- `LP only`：只拟合下支
- `Cavity only`：只拟合腔模

运行后可在：
- `Workspace` 中查看拟合曲线和残差
- `Session` 中查看关键诊断
- `Session Log` 中查看完整 summary

### 6. 导出结果

可以导出：

- `Export Report (TXT)`
- `Export Fit Data (CSV)`
- 工作区图像

## 中文主要参数说明

### 预处理参数

- `Smoothing`
  自动裁剪前用于平滑角向轮廓。数值越大，轮廓越平滑；过大时可能吞掉真实边界细节。
- `Crop mode`
  `Auto` 使用自动边界检测；`Manual` 使用手动边界。
- `Crop pad`
  自动裁剪时在检测边界外额外保留的像素数。数值越大，裁剪区域越宽。
- `Left boundary / Right boundary`
  手动裁剪边界，仅在 `Manual` 模式下直接控制裁剪范围。
- `NA`
  数值孔径，用于把横向像素映射到角度与 k 空间。设置不合理会直接影响拟合质量。
- `Auto k=0 / k0 idx`
  控制 `k=0` 的参考位置。若自动中心不理想，可关闭自动并手动指定。
- `Feature`
  `Reflectivity dip` 追踪反射谷值，`PL peak` 追踪 PL 峰值。

### Trace 参数

- `Search px`
  每一步沿能量方向搜索局部极值的窗口半宽。数值越大，允许跨越更宽的能量偏移，但也更容易跳到错误分支。
- `Prom.`
  极值显著性阈值。数值越大，选点越严格；太大时可能追踪中断，太小时可能混入噪声点。
- `Max miss`
  连续追踪失败允许的最大步数。数值越大，trace 更容易跨过局部缺口继续延伸。

### 拟合参数

- `m_r / m_0`
  相对有效质量。
- `E0`
  `k=0` 处的腔模能量。
- `k_shift`
  k 轴横向偏移，用于修正轻微的中心偏差。
- `g`
  耦合强度。
- `Eex`
  激子能量。
- `Material Preset`
  为常见材料填入一组更合理的初始猜测值，但参数仍然可以手动调整。

## 中文示例数据

示例数据位于：
- `data/example/pl/`
- `data/example/reflectivity/`

这些文件可用于熟悉基本工作流，但是否公开分发仍应以你的数据授权范围为准。

## 中文从源码运行

```bash
pip install -r requirements.txt
python apps/V4/app.py
```

如果系统中的 Python 命令不是 `python`，请改用你本机可用的解释器路径。

## 中文从源码重新打包

推荐先打 `onedir` 版本，再考虑 `onefile`。对于 `PyQt6 + matplotlib` 桌面程序，`onedir` 更稳。

### 使用 spec 打包 onedir

```powershell
pip install pyinstaller
pyinstaller AngleResolvedPolaritonFitter.spec
```

### 使用脚本打包

```powershell
./build_release.ps1
```

### 可选：打包 onefile

```powershell
./build_release.ps1 -OneFile
```

生成结果默认在 `dist/` 目录下。

---

## English Download

If you only want to use the program, download the packaged Windows assets from GitHub Releases.

Recommended asset:
- `AngleResolvedPolaritonFitter-windows.zip`
  Recommended for most users. Extract it and run `AngleResolvedPolaritonFitter.exe` from the extracted folder.

Alternative asset:
- `AngleResolvedPolaritonFitter.exe`
  Single-file build for convenience. Startup is usually slower than the zip package.

## English Overview

This tool is intended for tracing and fitting cavity, LP, and UP branches in angle-resolved reflectivity or PL spectroscopy data. The current public release supports:

- interactive tracing for cavity, LP, and UP branches
- segmented tracing for disconnected branches
- manual point cleanup with pick-delete, box-delete, and undo
- `Cavity only`, `LP only`, and `Coupled (LP+UP)` fitting modes
- diagnostics including RMSE, weighted RMSE, LP/UP RMSE, and seed source
- export of reports, fit CSV data, and workspace images

## English Workflow

Typical workflow: `Load -> Apply -> Start -> Trace -> Fit -> Export`

1. `Load`
   Import an angle-resolved reflectivity or PL dataset.
2. `Apply`
   Perform cropping, angle calibration, and preprocessing.
3. `Start`
   Click a starting point on the target branch in the `Interactive trace` view.
4. `Trace`
   Automatically trace the current branch. For disconnected branches, trace one segment at a time and add them to the branch.
5. `Fit`
   Select the fitting mode and inspect the fit curves, session summary, and residuals.
6. `Export`
   Export reports, fit CSV data, or workspace images.

## English Detailed Usage

### 1. Load data

Click `Load Data` and choose a reflectivity or PL data file. The raw matrix will be displayed in the workspace.

### 2. Preprocess and crop

In the `Data` tab, configure the crop and angle-mapping parameters, then click `Apply`.

- `Auto` crop mode detects crop boundaries automatically.
- `Manual` crop mode uses explicit boundaries and supports dragging the crop lines in the raw preview.

### 3. Set a start point and trace branches

Go to the `Trace` tab, select the active branch (`Cavity`, `LP`, or `UP`), and click a starting point in `Interactive trace`.

- `Trace New Segment` creates a pending segment.
- `Add Segment To Branch` merges that segment into the active branch.
- For disconnected `UP` branches, repeat the process for each segment.

### 4. Remove outliers manually

If the traced points contain visible outliers:

- enable `Edit Branch`
- use `Pick Delete` for single points
- use `Box Delete` for batch removal inside a rectangle
- use `Undo Last Delete` to restore the most recent deletion

### 5. Run the fit

In the `Fit` tab, select:

- `Coupled (LP+UP)` for simultaneous LP and UP fitting
- `LP only` for lower-branch fitting only
- `Cavity only` for cavity-mode fitting only

After fitting, inspect:
- fit curves and residuals in `Workspace`
- the summary panel in `Session`
- the detailed text in `Session Log`

### 6. Export results

You can export:

- `Export Report (TXT)`
- `Export Fit Data (CSV)`
- workspace images

## English Key Parameters

### Preprocessing parameters

- `Smoothing`
  Smooths the angular profile before automatic crop detection. Larger values produce smoother boundaries but can blur real edge features.
- `Crop mode`
  `Auto` uses automatic crop detection; `Manual` uses explicit boundaries.
- `Crop pad`
  Extra pixels preserved outside automatically detected crop boundaries. Larger values make the crop region wider.
- `Left boundary / Right boundary`
  Manual crop limits used in `Manual` mode.
- `NA`
  Numerical aperture used for angle and k-space mapping. Incorrect values directly affect the physical fit.
- `Auto k=0 / k0 idx`
  Controls the reference position for `k=0`. Disable auto mode if you need to set the center manually.
- `Feature`
  `Reflectivity dip` follows dips in reflectivity data, while `PL peak` follows peaks in PL data.

### Trace parameters

- `Search px`
  Half-width of the local search window along energy for each trace step. Larger values allow wider jumps but also increase the chance of landing on the wrong branch.
- `Prom.`
  Prominence threshold used during tracing. Larger values make point selection stricter; too large can stop the trace early, while too small can admit noisy points.
- `Max miss`
  Maximum number of consecutive missed steps allowed before tracing stops.

### Fit parameters

- `m_r / m_0`
  Relative effective mass.
- `E0`
  Cavity energy at `k=0`.
- `k_shift`
  Horizontal k-axis offset used to correct a small center shift.
- `g`
  Coupling strength.
- `Eex`
  Exciton energy.
- `Material Preset`
  Fills in more reasonable initial guesses for common material systems, while still keeping all parameters editable.

## English Example Data

Example datasets are stored in:
- `data/example/pl/`
- `data/example/reflectivity/`

Use them to learn the workflow, but only redistribute data that you are allowed to share.

## Run From Source

```bash
pip install -r requirements.txt
python apps/V4/app.py
```

If your system does not expose `python` directly, use the interpreter command available on your machine.

## Build From Source

The recommended release path is `onedir` first, then `onefile` only if you specifically need a single executable.

### Build onedir from the spec file

```powershell
pip install pyinstaller
pyinstaller AngleResolvedPolaritonFitter.spec
```

### Build with the helper script

```powershell
./build_release.ps1
```

### Optional: build onefile

```powershell
./build_release.ps1 -OneFile
```

Build artifacts are written to `dist/`.
