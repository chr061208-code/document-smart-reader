# Document Smart Reader（智能文档阅读器）

这是一个本地优先的智能文档阅读器。普通用户可直接运行 Windows 桌面版；Codex 用户也可安装 Skill/插件。它把 PDF、DOCX 转成带来源页码的 Markdown 缓存，只检索当前问题需要的片段，并在表格、公式、图表或复杂排版可能影响含义时要求核对原页面。

## Windows 桌面版（不需要 Codex）

从 [GitHub Releases](https://github.com/chr061208-code/document-smart-reader/releases/latest) 下载 `DocumentSmartReader.exe`，双击即可使用：选择文档、建立索引、搜索相关原文，再把带页码的证据复制给 ChatGPT、Claude 或其他 AI。

桌面版不包含 AI 模型，也不要求 API Key。它负责在本地准确、节省地找证据；最终回答可由用户选择的任意 AI 完成。详细说明见 [`desktop/README.zh-CN.md`](desktop/README.zh-CN.md)。

## 它为什么能节省 Token

仅把整份文件转成 Markdown 并不会自动节省 Token。真正的节省来自：完整转换结果保留在本地，模型每次只读取与问题相关的少量片段。

主要功能：

- PDF、DOCX 本地预处理；
- 按文件哈希复用缓存；
- Markdown 保留原始页码锚点；
- 支持中文和英文关键词检索；
- 默认只返回排名靠前的片段路径和摘要；
- 标记扫描页、少文字页和可能存在复杂版式的页面；
- 表格、公式、图表、表单和多栏内容采用原页面视觉复核。

脚本不会上传文档，也不包含网络请求。

## 支持范围

- 可搜索文字的 PDF；
- DOCX，优先使用 LibreOffice 转成 PDF，以获得稳定页码。

扫描 PDF 会被识别为少文字或无文字页面，但当前版本不内置 OCR。旧版 `.doc` 文件应先转成 `.docx` 或 PDF。

## 作为 Codex 插件安装

直接从 GitHub 发布版本安装：

```text
codex plugin marketplace add chr061208-code/document-smart-reader --ref v0.3.0
codex plugin add document-smart-reader@document-smart-reader
```

安装后新建一个 Codex 任务，让系统重新发现 Skill。

如需本地开发，可先克隆仓库，并把第一条命令替换为：

```text
codex plugin marketplace add <本仓库的绝对路径>
```

## 只安装 Skill

把下面的目录复制到 `~/.codex/skills/document-smart-reader`：

```text
plugins/document-smart-reader/skills/document-smart-reader
```

## 直接运行脚本

```bash
python -m pip install -r requirements.txt
python plugins/document-smart-reader/skills/document-smart-reader/scripts/smart_read.py prepare 材料.pdf
python plugins/document-smart-reader/skills/document-smart-reader/scripts/smart_read.py query \
  "缓存目录" "主要风险控制是什么？" --limit 3
```

可以通过环境变量 `CODEX_DOCUMENT_READER_CACHE` 指定缓存位置。

## 隐私说明

- 所有处理都在本地完成；
- 不包含遥测和联网代码；
- 缓存可能包含原文，请根据材料敏感程度妥善保存或删除；
- 永远不会修改原文件。

## 开发与测试

```bash
python -m pip install -r requirements-dev.txt
python -m unittest discover -s tests -v
```

许可证：MIT。
