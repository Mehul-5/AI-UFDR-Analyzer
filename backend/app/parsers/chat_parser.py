import sqlite3
from typing import Dict, List, Any, Optional
from datetime import datetime

class ChatParser:
    def extract(self, cursor: sqlite3.Cursor, schema: Dict[str, List[str]], parsed: Dict[str, Any]) -> None:
        """
        Schema-driven chat extraction without regex.
        Identifies tables that look like chat messages and extracts them.
        """
        for t, cols in schema.items():
            try:
                lower_cols = [c.lower() for c in cols]
                
                # 1. Identify Candidates
                text_candidates = [c for c in lower_cols if any(k in c for k in ['data', 'message', 'body', 'text', 'content'])]
                sender_candidates = [c for c in lower_cols if any(k in c for k in ['sender', 'from', 'author', 'address', 'src', 'caller'])]
                receiver_candidates = [c for c in lower_cols if any(k in c for k in ['receiver', 'to', 'dest', 'remote', 'chat', 'recipient', 'callee'])]
                ts_candidates = [c for c in lower_cols if any(k in c for k in ['time', 'date', 'timestamp'])]
                
                # Must have at least a text column to be a chat
                if not text_candidates:
                    continue

                # 2. Build Query
                select_cols: List[str] = []
                
                # Helpers to track column order
                sel_sender = sender_candidates[0] if sender_candidates else None
                sel_receiver = receiver_candidates[0] if receiver_candidates else None
                sel_text = text_candidates[0]
                sel_ts = ts_candidates[0] if ts_candidates else None

                if sel_sender: select_cols.append(sel_sender)
                if sel_receiver: select_cols.append(sel_receiver)
                select_cols.append(sel_text)
                if sel_ts: select_cols.append(sel_ts)

                query = f"SELECT {', '.join(select_cols)} FROM {t}"
                
                # 3. Execute & Parse
                for row in cursor.execute(query):
                    idx = 0
                    sender = row[idx] if sel_sender else None
                    if sel_sender: idx += 1
                    
                    receiver = row[idx] if sel_receiver else None
                    if sel_receiver: idx += 1
                    
                    content = row[idx]
                    idx += 1
                    
                    timestamp_raw = row[idx] if sel_ts else None
                    
                    parsed['chat_records'].append({
                        'app_name': 'Chat',
                        'sender_number': sender,
                        'receiver_number': receiver,
                        'message_content': content,
                        'timestamp': self._coerce_timestamp(timestamp_raw),
                        'message_type': 'text',
                        'is_deleted': False,
                        'metadata': {'source_table': t}
                    })
            except Exception as e:
                print(f"⚠️ Chat extraction error for table {t}: {e}")
                continue

    def _coerce_timestamp(self, value: Any) -> Optional[datetime]:
        """Helper to convert various timestamp formats."""
        try:
            if value is None: return None
            if isinstance(value, (int, float)):
                # Handle common Android epoch in milliseconds
                if value > 1e12: return datetime.fromtimestamp(value / 1000.0)
                return datetime.fromtimestamp(value)
            if isinstance(value, str) and value.isdigit():
                iv = int(value)
                if iv > 1e12: return datetime.fromtimestamp(iv / 1000.0)
                return datetime.fromtimestamp(iv)
            return None
        except Exception:
            return None