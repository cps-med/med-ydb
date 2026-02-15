# -----------------------------------------------------------------
# app/main.py
# -----------------------------------------------------------------
# Noodling around with Python as the language that integrates
# with YaddaDB, running within Docker container
# -----------------------------------------------------------------

# Import dependencies
import yottadb
from yottadb import YDBError

my_name = "Chuck"
rooster_count = 100 - 3 * 25 % 4

def main():
    # Print the current YottaDB release information
    release = yottadb.get("$ZYRELEASE",)
    print(f"YottaDB release: {release}\n")

    # ---------------------------------------------------------------------------
    # Create Key objects for convenient access and manipulating database nodes
    # ---------------------------------------------------------------------------

    # Create a key referencing the global variable '^hello'
    key1 = yottadb.Key('^hello')

    # Reset value to blank (if already set)
    key1.value = None

    print(f"key1 Type:  {type(key1)}")
    print(f"key1 Value: {key1}\n")

    # Display current value of '^hello'
    print(f"          {key1}: {key1.value}")

    # Set '^hello' to 'Hello world, again!!'
    key1.value = b'Hello world, again!'

    # Display updated value of '^hello'
    print(f"          {key1}: {key1.value}")

    # Add a 'cowboy' subscript to the global variable '^hello', creating a new key
    key2 = yottadb.Key('^hello')['cowboy']

    # Set '^hello('cowboy') to 'Howdy partner!'
    key2.value = b'Howdy partner!'
    print(f"{key2}: {key2.value}")

    print()

    # Add a second subscript to '^hello', creating a third key
    key3 = yottadb.Key('^hello')['chinese']

    key3.value = bytes('你好世界!', encoding="utf-8")       # Value can be set to anything that can be encoded to `bytes`
    print(key3, str(key3.value, encoding="utf-8"), "\n")   # Returned values are `bytes` objects, and so may need to be encoded

    print("Looping through subscripts of a key and printing value")
    print("-" * 55)
    # Loop through all the subscripts of a key
    for subscript in key1.subscripts:
        sub_key = key1[subscript]
        print(f"{sub_key}: {sub_key.value}")

    # Delete the value of '^hello', but not any of its child nodes
    key1.delete_node()

    print(f"{key1}: {key1.value}")     # No value is printed

    for subscript in key1.subscripts:  # The values of the child nodes are still in the database
        sub_key = key1[subscript]
        print(f"{sub_key}: {sub_key.value}")

    print("\n")

    # Explicit Write
    key1.value = b'STEVENS,CHUCK' 
    
    # Explicit Read
    raw_value = key1.value

    # Convert to string only when needed for UI/Logic
    display_name = raw_value.decode('utf-8')

    print(display_name, "\n")

if __name__ == "__main__":
    print("=" * 62)
    print(f"             Hello, {my_name}, rooster count is {rooster_count}")
    print("=" * 62, "\n")

    main()