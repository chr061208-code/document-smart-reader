# Windows 桌面版

桌面版供没有安装 Codex 的普通用户使用。它完全在本机处理 PDF 和 DOCX，可以建立可复用的 Markdown 索引、搜索相关页，并复制带页码的证据提示词到任意 AI。

## 直接使用

从 GitHub Releases 下载 `DocumentSmartReader.exe`，双击运行即可。首次启动单文件程序可能需要等待几秒。

1. 选择 PDF 或 DOCX；
2. 点击“建立索引”；
3. 输入问题或关键词，点击“搜索证据”；
4. 查看相关页和原文；
5. 复制精简或完整证据，粘贴到 ChatGPT、Claude 或其他 AI。

文档和缓存不会上传。缓存位于 `%LOCALAPPDATA%\DocumentSmartReader\cache`，其中可能包含原文。

扫描 PDF 暂不内置 OCR。DOCX 若已安装 LibreOffice，可获得较稳定的原始页码；否则仍可提取文字，但只显示章节。

## 从源码运行

```powershell
python -m pip install -r requirements.txt
python desktop/document_smart_reader.py
```

## 构建 EXE

```powershell
python -m pip install -r requirements-dev.txt
powershell -ExecutionPolicy Bypass -File desktop/build_windows.ps1
```
