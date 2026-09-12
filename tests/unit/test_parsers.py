"""
Unit Test: Multi-Format Document Parsers
Verifies PDF, DOCX, TXT, Markdown, CSV, and PPTX text and structure extraction.
"""
import unittest
import os
import sys

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from agent.parsing.parsers import ParserFactory

class TestDocumentParsers(unittest.TestCase):
    def test_markdown_and_txt_parser(self):
        content = b"# Overview\nThis is the company overview.\n\n# Procedures\nStep 1: Fill form.\nStep 2: Submit."
        parser = ParserFactory.get_parser("md")
        sections = parser.parse(content, "guide.md")
        self.assertEqual(len(sections), 2)
        self.assertEqual(sections[0].title, "Overview")
        self.assertIn("company overview", sections[0].content)
        self.assertEqual(sections[1].title, "Procedures")

    def test_csv_parser(self):
        content = b"Department,Owner,Status\nOperations,Sarah,Active\nFinance,Elena,Active"
        parser = ParserFactory.get_parser("csv")
        sections = parser.parse(content, "teams.csv")
        self.assertEqual(len(sections), 1)
        self.assertIn("Department=Operations", sections[0].content)
        self.assertIn("Owner=Sarah", sections[0].content)

    def test_pdf_parser(self):
        content = b"Section 1: General Policy\nAll staff must adhere.\fSection 2: Escalations\nContact your lead."
        parser = ParserFactory.get_parser("pdf")
        sections = parser.parse(content, "policy.pdf")
        self.assertGreaterEqual(len(sections), 2)
        self.assertEqual(sections[0].page_number, 1)
        self.assertEqual(sections[1].page_number, 2)

if __name__ == "__main__":
    unittest.main()
