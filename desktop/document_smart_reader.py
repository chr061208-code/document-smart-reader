#!/usr/bin/env python3
"""Windows desktop interface for Document Smart Reader."""

from __future__ import annotations

import json
import locale
import os
import queue
import subprocess
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk


def _load_core():
    if not getattr(sys, "frozen", False):
        project_root = Path(__file__).resolve().parents[1]
        scripts = project_root / "plugins" / "document-smart-reader" / "skills" / "document-smart-reader" / "scripts"
        sys.path.insert(0, str(scripts))
    import smart_read  # type: ignore

    return smart_read


smart_read = _load_core()
APP_VERSION = "0.3.0"


def app_cache_root() -> Path:
    base = os.environ.get("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
    return Path(base) / "DocumentSmartReader" / "cache"


def page_label(result: dict) -> str:
    start, end = result.get("page_start"), result.get("page_end")
    if start is None:
        return "章节 / Section"
    return f"第 {start} 页" if start == end else f"第 {start}–{end} 页"


def read_result_text(result: dict) -> str:
    return Path(result["file"]).read_text(encoding="utf-8")


def build_evidence_prompt(source: str, question: str, results: list[dict], full: bool = False) -> str:
    mode = "完整相关原文" if full else "精简检索片段"
    blocks: list[str] = []
    for number, result in enumerate(results, 1):
        evidence = read_result_text(result) if full else result.get("snippet", "")
        blocks.append(f"### 证据 {number}（{page_label(result)}）\n{evidence.strip()}")
    evidence_text = "\n\n".join(blocks) if blocks else "[没有检索到匹配证据]"
    return (
        "请仅根据下面的文档证据回答问题。引用事实时标注原始页码；"
        "如果证据不足，请明确说明缺少什么，不要猜测。表格、图表、公式或复杂排版可能需要查看原文件复核。\n\n"
        f"文档：{Path(source).name}\n问题：{question}\n证据模式：{mode}\n\n{evidence_text}"
    )


def open_path(path: str | Path) -> None:
    target = str(Path(path).resolve())
    if sys.platform == "win32":
        os.startfile(target)  # type: ignore[attr-defined]
    elif sys.platform == "darwin":
        subprocess.Popen(["open", target])
    else:
        subprocess.Popen(["xdg-open", target])


class DocumentSmartReaderApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title(f"Document Smart Reader {APP_VERSION}")
        self.geometry("1080x720")
        self.minsize(860, 600)
        self.configure(bg="#f3f6fb")
        self.option_add("*Font", ("Microsoft YaHei UI", 10))

        self.source_path = tk.StringVar()
        self.status = tk.StringVar(value="请选择 PDF 或 DOCX。所有处理均在本机完成。")
        self.summary = tk.StringVar(value="尚未建立索引")
        self.limit = tk.IntVar(value=3)
        self.reader_dir: Path | None = None
        self.results: list[dict] = []
        self.events: queue.Queue = queue.Queue()

        self._configure_style()
        self._build_ui()
        self.after(100, self._poll_events)

    def _configure_style(self) -> None:
        style = ttk.Style(self)
        if "vista" in style.theme_names():
            style.theme_use("vista")
        style.configure("Title.TLabel", font=("Microsoft YaHei UI", 20, "bold"), foreground="#17324d", background="#f3f6fb")
        style.configure("Sub.TLabel", foreground="#52667a", background="#f3f6fb")
        style.configure("Card.TFrame", background="#ffffff", relief="solid", borderwidth=1)
        style.configure("Card.TLabel", background="#ffffff")
        style.configure("Accent.TButton", font=("Microsoft YaHei UI", 10, "bold"))

    def _build_ui(self) -> None:
        root = ttk.Frame(self, padding=(24, 20))
        root.pack(fill="both", expand=True)
        ttk.Label(root, text="智能文档阅读器", style="Title.TLabel").pack(anchor="w")
        ttk.Label(root, text="离线提取 PDF / Word 证据，带页码交给任意 AI 使用", style="Sub.TLabel").pack(anchor="w", pady=(2, 16))

        source_card = ttk.Frame(root, style="Card.TFrame", padding=14)
        source_card.pack(fill="x")
        source_row = ttk.Frame(source_card, style="Card.TFrame")
        source_row.pack(fill="x")
        ttk.Entry(source_row, textvariable=self.source_path).pack(side="left", fill="x", expand=True, padx=(0, 8))
        ttk.Button(source_row, text="选择文档", command=self.choose_document).pack(side="left", padx=(0, 8))
        self.index_button = ttk.Button(source_row, text="建立索引", style="Accent.TButton", command=self.start_prepare)
        self.index_button.pack(side="left")
        ttk.Label(source_card, textvariable=self.summary, style="Card.TLabel").pack(anchor="w", pady=(10, 0))

        question_card = ttk.Frame(root, style="Card.TFrame", padding=14)
        question_card.pack(fill="x", pady=(12, 0))
        question_row = ttk.Frame(question_card, style="Card.TFrame")
        question_row.pack(fill="x")
        ttk.Label(question_row, text="问题：", style="Card.TLabel").pack(side="left")
        self.question = ttk.Entry(question_row)
        self.question.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.question.bind("<Return>", lambda _event: self.search())
        ttk.Label(question_row, text="结果数", style="Card.TLabel").pack(side="left")
        ttk.Spinbox(question_row, from_=1, to=8, textvariable=self.limit, width=4).pack(side="left", padx=(6, 8))
        self.search_button = ttk.Button(question_row, text="搜索证据", style="Accent.TButton", command=self.search, state="disabled")
        self.search_button.pack(side="left")

        results_card = ttk.Frame(root, style="Card.TFrame", padding=10)
        results_card.pack(fill="both", expand=True, pady=(12, 0))
        panes = ttk.Panedwindow(results_card, orient="horizontal")
        panes.pack(fill="both", expand=True)
        left = ttk.Frame(panes, style="Card.TFrame")
        right = ttk.Frame(panes, style="Card.TFrame")
        panes.add(left, weight=1)
        panes.add(right, weight=3)
        self.result_list = tk.Listbox(left, width=28, height=12, borderwidth=0, highlightthickness=0, selectbackground="#2563eb", activestyle="none")
        self.result_list.pack(fill="both", expand=True)
        self.result_list.bind("<<ListboxSelect>>", self.show_selected)
        self.preview = tk.Text(right, height=12, wrap="word", borderwidth=0, padx=12, pady=8, bg="#ffffff", fg="#24384b")
        self.preview.pack(side="left", fill="both", expand=True)
        preview_scroll = ttk.Scrollbar(right, orient="vertical", command=self.preview.yview)
        preview_scroll.pack(side="right", fill="y")
        self.preview.configure(yscrollcommand=preview_scroll.set, state="disabled")

        actions = ttk.Frame(root)
        actions.pack(fill="x", pady=(12, 0))
        self.copy_short_button = ttk.Button(actions, text="复制精简证据（省 Token）", command=lambda: self.copy_prompt(False), state="disabled")
        self.copy_short_button.pack(side="left")
        self.copy_full_button = ttk.Button(actions, text="复制完整证据", command=lambda: self.copy_prompt(True), state="disabled")
        self.copy_full_button.pack(side="left", padx=(8, 0))
        ttk.Button(actions, text="打开原文件", command=self.open_source).pack(side="right")
        self.cache_button = ttk.Button(actions, text="打开 Markdown 缓存", command=self.open_cache, state="disabled")
        self.cache_button.pack(side="right", padx=(0, 8))
        ttk.Label(root, textvariable=self.status, style="Sub.TLabel").pack(anchor="w", pady=(10, 0))

    def choose_document(self) -> None:
        selected = filedialog.askopenfilename(title="选择 PDF 或 Word 文档", filetypes=[("支持的文档", "*.pdf *.docx"), ("PDF", "*.pdf"), ("Word", "*.docx")])
        if selected:
            self.source_path.set(selected)
            self.reader_dir = None
            self.results = []
            self._clear_results()
            self.summary.set("已选择文档，点击“建立索引”。")
            self.search_button.configure(state="disabled")
            self.cache_button.configure(state="disabled")

    def start_prepare(self) -> None:
        source = Path(self.source_path.get().strip())
        if not source.is_file() or source.suffix.lower() not in smart_read.SUPPORTED:
            messagebox.showwarning("无法读取", "请选择有效的 PDF 或 DOCX 文件。")
            return
        self._set_busy(True, "正在本机提取文字并建立索引……")
        threading.Thread(target=self._prepare_worker, args=(source,), daemon=True).start()

    def _prepare_worker(self, source: Path) -> None:
        try:
            result = smart_read.prepare_document(source, app_cache_root())
            manifest = json.loads(Path(result["manifest"]).read_text(encoding="utf-8"))
            self.events.put(("prepared", result, manifest))
        except Exception as exc:
            self.events.put(("error", "建立索引失败", str(exc)))

    def search(self) -> None:
        question = self.question.get().strip()
        if not self.reader_dir or not question:
            messagebox.showinfo("请输入问题", "建立索引后，请输入要查找的问题或关键词。")
            return
        try:
            result = smart_read.query_reader(self.reader_dir, question, max(1, min(8, self.limit.get())))
            self.results = result["results"]
            self._render_results()
        except Exception as exc:
            messagebox.showerror("搜索失败", str(exc))

    def _render_results(self) -> None:
        self._clear_results()
        for number, result in enumerate(self.results, 1):
            self.result_list.insert("end", f"{number}. {page_label(result)}  ·  {result['score']:.1f}")
        state = "normal" if self.results else "disabled"
        self.copy_short_button.configure(state=state)
        self.copy_full_button.configure(state=state)
        if self.results:
            self.result_list.selection_set(0)
            self.show_selected()
            self.status.set(f"找到 {len(self.results)} 个相关片段。左侧选择结果，右侧查看原文。")
        else:
            self._set_preview("没有找到匹配内容。可换用文档中可能出现的关键词。")
            self.status.set("没有找到匹配证据。")

    def show_selected(self, _event=None) -> None:
        selection = self.result_list.curselection()
        if not selection:
            return
        result = self.results[selection[0]]
        flags = ", ".join(result.get("flags", [])) or "无"
        text = read_result_text(result)
        self._set_preview(f"{page_label(result)}  |  相关度 {result['score']:.2f}  |  质量标记：{flags}\n\n{text}")

    def copy_prompt(self, full: bool) -> None:
        if not self.results:
            return
        prompt = build_evidence_prompt(self.source_path.get(), self.question.get().strip(), self.results, full)
        self.clipboard_clear()
        self.clipboard_append(prompt)
        self.update()
        self.status.set("已复制完整证据提示词。" if full else "已复制精简证据提示词，可粘贴到任意 AI。")

    def open_source(self) -> None:
        source = Path(self.source_path.get().strip())
        if source.is_file():
            open_path(source)

    def open_cache(self) -> None:
        if self.reader_dir:
            open_path(self.reader_dir)

    def _set_busy(self, busy: bool, status: str) -> None:
        self.index_button.configure(state="disabled" if busy else "normal")
        self.search_button.configure(state="disabled" if busy or not self.reader_dir else "normal")
        self.status.set(status)

    def _clear_results(self) -> None:
        self.result_list.delete(0, "end")
        self._set_preview("")
        self.copy_short_button.configure(state="disabled")
        self.copy_full_button.configure(state="disabled")

    def _set_preview(self, text: str) -> None:
        self.preview.configure(state="normal")
        self.preview.delete("1.0", "end")
        self.preview.insert("1.0", text)
        self.preview.configure(state="disabled")

    def _poll_events(self) -> None:
        try:
            while True:
                event = self.events.get_nowait()
                if event[0] == "prepared":
                    _, result, manifest = event
                    self.reader_dir = Path(result["reader_dir"])
                    pages = manifest.get("page_count")
                    page_text = f"{pages} 页" if pages is not None else "无稳定页码"
                    warning_count = len(manifest.get("warnings", []))
                    self.summary.set(f"{page_text} · {manifest['chunk_count']} 个检索片段 · {manifest['character_count']:,} 字符 · {warning_count} 条提示")
                    self._set_busy(False, "索引已复用。" if result["status"] == "reused" else "索引建立完成。现在可以输入问题。")
                    self.search_button.configure(state="normal")
                    self.cache_button.configure(state="normal")
                    self.question.focus_set()
                elif event[0] == "error":
                    _, title, detail = event
                    self._set_busy(False, detail)
                    messagebox.showerror(title, detail)
        except queue.Empty:
            pass
        self.after(100, self._poll_events)


def main() -> None:
    try:
        locale.setlocale(locale.LC_ALL, "")
    except locale.Error:
        pass
    DocumentSmartReaderApp().mainloop()


if __name__ == "__main__":
    main()
