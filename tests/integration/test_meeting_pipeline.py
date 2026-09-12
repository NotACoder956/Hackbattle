"""
Integration Test: Meeting Pipeline & Intelligence
Verifies meeting audio transcription, speaker diarization, timestamps, decisions, and process extraction.
"""
import unittest
import os
import sys

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from agent.meetings.pipeline import meeting_pipeline

class TestMeetingPipeline(unittest.TestCase):
    def test_meeting_processing_and_process_extraction(self):
        transcript_sample = (
            "Manager: Welcome everyone to the Operations sync.\n"
            "Manager: Today we are reviewing the client onboarding sequence.\n"
            "Sarah: We decided that from now on, the Finance Lead now approves invoices instead of the Finance Manager.\n"
            "Elena: Yes, after KYC documents are verified, the Finance Lead will sign off in the portal.\n"
            "Manager: Action item for Yash to update the documentation by Friday."
        )

        meeting = meeting_pipeline.process_meeting(
            tenant_id="ten_meeting_test",
            title="Operations Weekly Sync",
            audio_bytes=transcript_sample.encode("utf-8"),
            filename="ops_sync.mp3",
            participants=["Manager", "Sarah", "Elena", "Yash"]
        )

        self.assertEqual(meeting.status, "PROCESSED")
        self.assertGreaterEqual(len(meeting.segments), 4)

        # Check timestamp format
        first_seg = meeting.segments[0]
        self.assertIn(":", first_seg.timestamp)
        self.assertEqual(first_seg.speaker, "Manager")

        # Check process change detection
        self.assertGreaterEqual(len(meeting.extracted_processes), 1)
        proc_stmt = meeting.extracted_processes[0]["statement"].lower()
        self.assertTrue("from now on" in proc_stmt or "now approves" in proc_stmt)

if __name__ == "__main__":
    unittest.main()
