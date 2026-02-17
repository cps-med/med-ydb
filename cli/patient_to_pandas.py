import yottadb
import pandas as pd
from pathlib import Path

def get_patient_data():
    patients = []
    print("Connecting to YottaDB and fetching patient records...")
    
    try:
        # 1. Create the Key object pointing to the Global
        # We start with a Key that has NO subscripts to represent the root ^DPT
        curr_key = yottadb.Key("^DPT")
        
        while True:
            try:
                # 2. subscript_next() moves to the next sibling at the current level.
                # In 2.0.0, calling this on ^DPT moves it to ^DPT(IEN)
                curr_key = curr_key.subscript_next()
                
                # 3. Extract the IEN (it's the first element in the subscripts tuple)
                if not curr_key.subscripts:
                    break
                
                ien = curr_key.subscripts[0]
                
                # 4. Access the zero-node: ^DPT(IEN, 0)
                # We can 'branch' off the current key to get the child node
                node_val = curr_key[0].get()
                
                if node_val:
                    # Decode if bytes, else use as is
                    node_data = node_val.decode('utf-8') if isinstance(node_val, bytes) else node_val
                    pieces = node_data.split('^')
                    
                    patients.append({
                        "IEN": ien,
                        "Name": pieces[0] if len(pieces) >= 1 else "Unknown",
                        "SSN": pieces[8] if len(pieces) >= 9 else "N/A"
                    })

            except yottadb.YDBNodeEnd:
                # This exception is raised when there are no more siblings
                break
            except Exception as e:
                # If a specific IEN is weird, just skip it and move to next
                continue

    except Exception as e:
        print(f"❌ Critical Error: {e}")
        return None

    return patients

def main():
    data = get_patient_data()
    if data is None: return

    df = pd.DataFrame(data)
    print("\n--- Patient DataFrame Summary ---")
    if not df.empty:
        # Standard Pandas display
        print(df.head())
        print(f"\nTotal Patients Loaded: {len(df)}")
        
        # Save to the mounted output volume
        output_path = Path("/opt/med-ydb/output/patient_export.csv")
        df.to_csv(output_path, index=False)
        print(f"✅ Data exported to: {output_path}")
    else:
        print("No patient records found in ^DPT.")

if __name__ == "__main__":
    main()