import sqlite3
from typing import Dict, List, Any, Optional

class ContactParser:
    def extract(self, cursor: sqlite3.Cursor, schema: Dict[str, List[str]], parsed: Dict[str, Any]) -> None:
        """
        Extract contacts (Phonebook/Address Book).
        Looks for 'display_name', 'phone', and 'email' columns.
        """
        for t, cols in schema.items():
            try:
                lower_cols = [c.lower() for c in cols]
                
                # 1. Identify Candidate Columns
                name_cols = [c for c in lower_cols if any(k in c for k in ['display_name', 'name', 'given_name'])]
                phone_cols = [c for c in lower_cols if any(k in c for k in ['phone', 'number', 'msisdn'])]
                email_cols = [c for c in lower_cols if 'email' in c]
                
                # Must have a name column to be a contact list
                if not name_cols:
                    continue
                
                # 2. Build Query
                select_cols = [name_cols[0]]
                if phone_cols: select_cols.append(phone_cols[0])
                if email_cols: select_cols.append(email_cols[0])
                
                query = f"SELECT {', '.join(select_cols)} FROM {t}"
                
                # 3. Execute & Parse
                for row in cursor.execute(query):
                    idx = 0
                    name = row[idx]
                    idx += 1
                    
                    phone_numbers: List[str] = []
                    email_addresses: List[str] = []
                    
                    if phone_cols:
                        val = row[idx]
                        idx += 1
                        if val is not None and str(val).strip() != '':
                            phone_numbers = [str(val)]
                            
                    if email_cols:
                        val = row[idx]
                        if val is not None and str(val).strip() != '':
                            email_addresses = [str(val)]
                            
                    parsed['contacts'].append({
                        'name': name,
                        'phone_numbers': phone_numbers,
                        'email_addresses': email_addresses,
                        'metadata': {'source_table': t}
                    })
            except Exception:
                continue