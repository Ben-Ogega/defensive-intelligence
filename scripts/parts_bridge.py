import json
import os

# ===============================================
# Parts Bridge | Heavy Equipment Parts
# Author: Ben Ogega | Date: 2024-04-21
# Phase: 1 - Parts Lookup Engine
# ==============================================
"""
==========The Parts Bridge==========
        The guessing games are over now,
        The waiting ends and supply flows.
        We bridge the gap and show you how,
        The heart of heavy equipment grows.

        The specs are clear and instantly,
        Compatibility is found.
        We save your time and energy,
        With data that is safe and sound.

        For those who build and those who buy,
        The perfect tool is at your hand.
        On every part you can rely,
        Across the heavy-duty land.
"""

# Step 1: Load parts data from JSON file/database
def load_database(db_path):
    if not os.path.exists(db_path): # why check if file exists before trying to load it?
        # Checking if the file exists before attempting to load it prevents errors if the file is missing.
        # If the file doesn't exist, it allows us to handle the situation gracefully by printing a message 
        # and returning an empty dictionary, rather than crashing the program with a FileNotFoundError.
        print(f"❌ Database not found: '{db_path}'")
        return {} # why return empty dict instead of None? 
    # because it allows the rest of the code to continue functioning without crashing, 
    # and it provides a clear indication that the database is empty rather than missing. 
    # This way, the program can handle the situation gracefully and avoid potential errors down the line when trying to access parts data.
    try:
        with open(db_path, 'r') as file:
            parts_data = json.load(file)
            return parts_data
    except json.JSONDecodeError as e:
        print(f"❌ Error decoding JSON: {e}") # why print error instead of raising exception?
        # printing the error allows the program to continue running and provides feedback on what went wrong,
        # while raising an exception would stop the program and require additional error handling.
        return None
    
# Step 2: Lookup part information by part number
def find_part(part_number, database):
    '''
    1. Check if the database is available. If not, print an error message and return None.
    2. Attempt to retrieve the part information from the database using the provided part number.
    '''
    if not database:
        print("❌ No parts data available.")
        return None
    part_number = part_number.strip().upper() # why strip and upper?
    # Stripping whitespace ensures that any accidental spaces before or 
    # after the part number do not affect the lookup, while converting to uppercase standardizes the input,
    #  making it case-insensitive and improving the chances of a successful match in the database.
    part_info = database.get(part_number)
    if part_info:
        return part_info
    else:
        print(f"❌ Part number '{part_number}' not found in database.")
        return {}
    
# Step 3: Display part information in a user-friendly format
#  Display results beautifully
def display_part(part_number, part_info):
    """
    Prints a formatted report of the part
    and all its equivalents.
    """
    print("\n" + "="*55)
    print("   PartsBridge | Heavy Equipment Cross-Referencer")
    print("   East Africa | BRIDGE Framework | Ben Ogega")
    print("="*55)
    
    # Header
    print(f"\n🔍 Part Number:  {part_number}")
    print(f"📦 Description:  {part_info['description']}")
    print(f"🏭 OEM:          {part_info['oem']}")
    print(f"📊 Status:       {part_info['status']}")
    
    # OEM replacement if discontinued
    if part_info['status'] == 'DISCONTINUED':
        print(f"🔄 OEM Replace:  {part_info.get('oem_replacement', 'N/A')}")
    
    # Applications
    print(f"\n⚙️  APPLICATIONS:")
    print("-"*55)
    for app in part_info.get('applications', []):
        print(f"   • {app}")
    
    # Equivalents
    print(f"\n🔧 EQUIVALENT PARTS:")
    print("-"*55)
    print(f"   {'Manufacturer':<15} {'Part Number':<20} {'Notes'}")
    print("-"*55)
    for eq in part_info.get('equivalents', []):
        print(f"   {eq['manufacturer']:<15} "
              f"{eq['part_number']:<20} "
              f"{eq['notes']}")
    
    # Specifications
    print(f"\n📐 SPECIFICATIONS:")
    print("-"*55)
    for key, value in part_info.get('specs', {}).items():
        key_display = key.replace('_', ' ').title()
        print(f"   {key_display:<25} {value}")
    
    print("="*55)

# Step 4: Main function to run the parts lookup
def main():
    # Use environment variable or relative pathing
    path =  "C:\\Users\\User\\Desktop\\Logos\\TransformerRoadMap\\defensive-intelligence\\data\\raw\\parts_database.json"
    database = load_database(path)

    if not database:
        return

    print("🏗️  Parts Bridge Initialized. Type 'exit' to quit.")
    
    while True:
        query = input("\nEnter part number: ").strip()
        if query.lower() == 'exit':
            break
        
        result = find_part(query, database)
        if result:
            # Assume display_part is defined elsewhere
            print(f"✅ Found: {result}")
        else:
            print(f"⚠️ Part '{query}' not found.")

if __name__ == "__main__":
    main()
