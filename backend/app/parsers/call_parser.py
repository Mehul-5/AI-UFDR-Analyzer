import sqlite3
from typing import Dict, List, Any, Optional
from datetime import datetime

class CallParser:
    def extract(self, cursor: sqlite3.Cursor, schema: Dict[str, List[str]], parsed: Dict[str, Any]) -> None:
        """
        Extract call logs based on schema heuristics.
        Looks for tables with 'duration', 'type', and phone number columns.
        """
        # Identify tables that look like call logs
        call_tables = [
            (t, cols) for t, cols in schema.items() 
            if self._has_columns(cols, ['number', 'type', 'duration']) or 
               self._has_columns(cols, ['caller', 'receiver', 'duration'])
        ]
        
        for t, cols in call_tables:
            try:
                colset = set(c.lower() for c in cols)
                
                # Scenario A: Explicit Caller/Receiver columns
                if {'caller', 'receiver', 'duration'} <= colset:
                    query = f"SELECT caller, receiver, duration, type, date FROM {t}"
                    for a, b, duration, call_type, date_val in cursor.execute(query):
                        parsed['call_records'].append({
                            'caller_number': a,
                            'receiver_number': b,
                            'call_type': str(call_type) if call_type is not None else 'unknown',
                            'duration': int(duration) if duration is not None else 0,
                            'timestamp': self._coerce_timestamp(date_val),
                            'metadata': {'source_table': t}
                        })
                        
                # Scenario B: Android/Standard format (Number + Type determines direction)
                else:
                    # Select columns dynamically based on what exists
                    query = f"SELECT number, number, duration, type, date FROM {t}"
                    for num, _, duration, call_type, date_val in cursor.execute(query):
                        # Logic to determine caller/receiver based on type would go here
                        # For now, we map 'number' to both to capture the connection
                        parsed['call_records'].append({
                            'caller_number': num,
                            'receiver_number': None, # Direction ambiguous without type mapping
                            'call_type': str(call_type) if call_type is not None else 'unknown',
                            'duration': int(duration) if duration is not None else 0,
                            'timestamp': self._coerce_timestamp(date_val),
                            'metadata': {'source_table': t}
                        })
            except Exception as e:
                print(f"⚠️ Call extraction error from {t}: {e}")

    def _has_columns(self, cols: List[str], required: List[str]) -> bool:
        cols_lower = set(c.lower() for c in cols)
        return all(req.lower() in cols_lower for req in required)

    def _coerce_timestamp(self, value: Any) -> Optional[datetime]:
        """Helper to convert various timestamp formats."""
        try:
            if value is None: return None
            if isinstance(value, (int, float)):
                if value > 1e12: return datetime.fromtimestamp(value / 1000.0)
                return datetime.fromtimestamp(value)
            if isinstance(value, str) and value.isdigit():
                iv = int(value)
                if iv > 1e12: return datetime.fromtimestamp(iv / 1000.0)
                return datetime.fromtimestamp(iv)
            return None
        except Exception:
            return None