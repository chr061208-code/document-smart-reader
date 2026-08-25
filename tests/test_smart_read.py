import argparse
import contextlib
import importlib.util
import io
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "plugins" / "document-smart-reader" / "skills" / "document-smart-reader" / "scripts" / "smart_read.py"
SPEC = importlib.util.spec_from_file_location("smart_read", SCRIPT)
smart_read = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(smart_read)

DESKTOP_SCRIPT = ROOT / "desktop" / "document_smart_reader.py"
DESKTOP_SPEC = importlib.util.spec_from_file_location("document_smart_reader", DESKTOP_SCRIPT)
desktop = importlib.util.module_from_spec(DESKTOP_SPEC)
assert DESKTOP_SPEC and DESKTOP_SPEC.loader
DESKTOP_SPEC.loader.exec_module(desktop)


class SmartReadUnitTests(unittest.TestCase):
    def test_normalize_text(self):
        self.assertEqual(smart_read.normalize_text("Ａ股\x01  ⼀\t测试"), "A股 一 测试")

    def test_chinese_and_latin_tokenization(self):
        tokens = smart_read.tokenize("复核阈值 0.73 Risk")
        self.assertIn("复核", tokens)
        self.assertIn("阈值", tokens)
        self.assertIn("risk", tokens)
        self.assertIn("73", tokens)

    def test_snippet_prefers_rare_evidence(self):
        text = "efficiency " * 80 + "The verified target is 27.5 percent."
        snippet = smart_read.make_snippet(text, "target 27.5 percent", smart_read.tokenize("target 27.5 percent"))
        self.assertIn("27.5 percent", snippet)

    def test_chunks_keep_page_anchors(self):
        chunks = smart_read.make_chunks([
            {"page": 1, "text": "alpha " * 30, "flags": []},
            {"page": 2, "text": "beta " * 30, "flags": []},
        ], target_chars=200)
        self.assertEqual(len(chunks), 2)
        self.assertIn("<!-- source-page: 2 -->", chunks[1]["text"])


class SmartReadEndToEndTests(unittest.TestCase):
    def test_pdf_prepare_query_and_reuse(self):
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "sample.pdf"
            pdf = canvas.Canvas(str(source), pagesize=A4)
            for page in range(1, 3):
                pdf.drawString(72, 780, "General introduction " * 8)
                if page == 2:
                    pdf.drawString(72, 740, "Verified threshold is 0.73 for manual review.")
                pdf.showPage()
            pdf.save()

            args = argparse.Namespace(file=str(source), output=str(root / "cache"), chunk_chars=200, force=False)
            with contextlib.redirect_stdout(io.StringIO()) as output:
                self.assertEqual(smart_read.prepare(args), 0)
            created = json.loads(output.getvalue())
            self.assertEqual(created["status"], "created")
            reader_dir = Path(created["reader_dir"])
            manifest = json.loads((reader_dir / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["tool_version"], "0.3.0")
            self.assertEqual(manifest["page_count"], 2)

            query_args = argparse.Namespace(reader_dir=str(reader_dir), question="threshold 0.73", limit=1)
            with contextlib.redirect_stdout(io.StringIO()) as output:
                self.assertEqual(smart_read.query(query_args), 0)
            result = json.loads(output.getvalue())
            self.assertEqual(result["results"][0]["page_start"], 2)
            self.assertIn("0.73", result["results"][0]["snippet"])

            with contextlib.redirect_stdout(io.StringIO()) as output:
                self.assertEqual(smart_read.prepare(args), 0)
            self.assertEqual(json.loads(output.getvalue())["status"], "reused")

    def test_programmatic_api(self):
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "api.pdf"
            pdf = canvas.Canvas(str(source), pagesize=A4)
            pdf.drawString(72, 780, "The audit finding requires a corrective action plan.")
            pdf.save()
            prepared = smart_read.prepare_document(source, root / "cache")
            queried = smart_read.query_reader(prepared["reader_dir"], "corrective action", 1)
            self.assertEqual(queried["result_count"], 1)
            self.assertIn("corrective action", queried["results"][0]["snippet"])


class DesktopHelperTests(unittest.TestCase):
    def test_prompt_contains_source_page_and_evidence(self):
        with tempfile.TemporaryDirectory() as temporary:
            chunk = Path(temporary) / "chunk.md"
            chunk.write_text("<!-- source-page: 7 -->\n\nImportant evidence.", encoding="utf-8")
            result = {"file": str(chunk), "page_start": 7, "page_end": 7, "snippet": "Important evidence."}
            prompt = desktop.build_evidence_prompt("report.pdf", "What matters?", [result], full=False)
            self.assertIn("report.pdf", prompt)
            self.assertIn("第 7 页", prompt)
            self.assertIn("Important evidence.", prompt)


class PackagingTests(unittest.TestCase):
    def test_plugin_manifest_and_marketplace(self):
        plugin = json.loads((ROOT / "plugins" / "document-smart-reader" / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))
        marketplace = json.loads((ROOT / ".agents" / "plugins" / "marketplace.json").read_text(encoding="utf-8"))
        self.assertEqual(plugin["name"], "document-smart-reader")
        self.assertEqual(plugin["version"], "0.3.0")
        self.assertEqual(plugin["license"], "MIT")
        self.assertEqual(marketplace["name"], "document-smart-reader")
        self.assertEqual(marketplace["plugins"][0]["name"], plugin["name"])


if __name__ == "__main__":
    unittest.main()
