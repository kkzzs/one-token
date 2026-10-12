# MiniMax-H3 / native Sol-H3 model backup

原生 Sol-H3 的模型权重备份（2026-10-12），配合之前保存的 HBK 代码包使用。

包含官方原始 FL2VA 基座、FastH3 dense-datafree adapter，以及 Qwen50 文本编码器新增分片、索引和配置。总计约 148.23 GB。超过 1.8 GB 的原文件按字节拆分，通过 Git LFS 保存；恢复时逐片校验 SHA256 并拼接，不改变权重精度或模型内容。

不包含 SGLang 的已合并 FastH3 transformer、VDN 增量、Python 环境、运行缓存。`audio_vae_materialized` 是其他运行路径的派生权重，原生 Sol-H3 不使用，因此不包含。VAE Linear FP16 仍由原生 runner 加载时执行。

## 下载与恢复

安装 Git、Git LFS 和 Python 3。在有足够空间的新机器上执行：

```bash
GIT_LFS_SKIP_SMUDGE=1 git clone git@github.com:kkzzs/one-token.git
cd one-token
git lfs install --local --skip-smudge
git lfs fetch origin main
python3 restore_weights.py --destination /root
```

恢复脚本直接读取 LFS 对象缓存，避免额外生成一套工作目录分片；LFS 缓存和恢复后的权重合计需要约 297 GB 空间，另留系统余量。可以用 `--destination /path/to/restore` 先恢复到其他目录，但 HBK 的原生 runner 默认读取 `/root/models` 和 `/root/hbk/h3-repro/models`。

脚本拒绝覆盖已有权重。恢复后会建立 Qwen50 到基础文本权重的相对符号链接，不重复存储未改变的分片。可用以下命令只校验下载内容：

```bash
python3 restore_weights.py --destination /root --verify-only
```

最终恢复位置：

- `/root/models/MiniMax-H3-official-fl2va/`：基础模型、完整文本编码器、音视频 VAE 和配置。
- `/root/hbk/h3-repro/models/fast-h3-adapter/`：adapter。
- `/root/hbk/h3-repro/models/minimax-h3-fasth3-qwen50/FL2VA/text_encoder/`：Qwen50 文本编码器。

详细文件和分片 SHA256 见 `weights-manifest.json`、`small-file-sha256.json`；Qwen50 链接关系见 `restore-links.json`。使用该目录前，还需恢复代码和依赖环境。源模型的许可及使用条款仍适用。
