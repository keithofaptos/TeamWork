import os
import csv

def print_fireworks():
    print("\033[92m")  # Green color
    fireworks = """
    /$$$$$           /$$              /$$$$$$                                    /$$             /$$               /$$
   |__  $$          | $$             /$$__  $$                                  | $$            | $$              | $$
      | $$  /$$$$$$ | $$$$$$$       | $$  \__/  /$$$$$$  /$$$$$$/$$$$   /$$$$$$ | $$  /$$$$$$  /$$$$$$    /$$$$$$ | $$
      | $$ /$$__  $$| $$__  $$      | $$       /$$__  $$| $$_  $$_  $$ /$$__  $$| $$ /$$__  $$|_  $$_/   /$$__  $$| $$
 /$$  | $$| $$  \ $$| $$  \ $$      | $$      | $$  \ $$| $$ \ $$ \ $$| $$  \ $$| $$| $$$$$$$$  | $$    | $$$$$$$$|__/
| $$  | $$| $$  | $$| $$  | $$      | $$    $$| $$  | $$| $$ | $$ | $$| $$  | $$| $$| $$_____/  | $$ /$$| $$_____/    
|  $$$$$$/|  $$$$$$/| $$$$$$$/      |  $$$$$$/|  $$$$$$/| $$ | $$ | $$| $$$$$$$/| $$|  $$$$$$$  |  $$$$/|  $$$$$$$ /$$
 \______/  \______/ |_______/        \______/  \______/ |__/ |__/ |__/| $$____/ |__/ \_______/   \___/   \_______/|__/
                                                                      | $$                                            
                                                                      | $$                                            
                                                                      |__/                                            
    """
    print(fireworks)
    print("\033[0m")  # Reset to default color

# Clears the terminal screen
os.system("clear")  # For UNIX-like systems, use "cls" on Windows instead.

# Path to the data folder
data_folder_path = os.path.join(os.path.dirname(__file__), "data")

# Create the data folder if it does not exist
if not os.path.exists(data_folder_path):
    os.makedirs(data_folder_path)

# CSV output file path
output_file = os.path.join(data_folder_path, "compiled_business_listing_data.csv")

# Set to track unique business names to avoid duplicates
seen_names = set()

# Flag to ensure the header is written only once
header_written = False

# Open the output file in write mode
with open(output_file, 'w', newline='') as output_csvfile:
    output_csvwriter = csv.writer(output_csvfile)
    
    # Traverse the directory containing CSV files
    for root, _, files in os.walk(data_folder_path):
        for file in files:
            if file.startswith("google_maps_listings_") and file.endswith('.csv'):
                input_file_path = os.path.join(root, file)
                
                # Open each input file in read mode
                with open(input_file_path, 'r', newline='') as input_csvfile:
                    input_csvreader = csv.reader(input_csvfile)
                    
                    # Read the header and write to output file if not already done
                    header = next(input_csvreader)
                    if not header_written:
                        output_csvwriter.writerow(header)
                        header_written = True
                    
                    # Find indices for Email and Website columns
                    email_column_index = header.index("Email")
                    website_column_index = header.index("Website")
                    
                    # Process each row in the input CSV file
                    for row in input_csvreader:
                        email = row[email_column_index].strip()
                        
                        # Clean up email by removing URL parameters
                        if '?' in email:
                            email = email.split('?')[0]
                        
                        # Populate empty email fields with default email based on website domain
                        if email == "":
                            website = row[website_column_index]
                            domain = website.split("//")[-1].split("/")[0]  # Extract domain from URL
                            if domain:  # Check if domain is not empty
                                email = "info@" + domain
                                row[email_column_index] = email
                        
                        # Further clean up email by removing stray periods at the end
                        if email.endswith('.'):
                            email = email.rstrip('.')
                            
                        row[email_column_index] = email  # Update the email address in the row

                        name = row[0]  # Assuming the first column is "Name"
                        # Write unique names only
                        if name not in seen_names:
                            output_csvwriter.writerow(row)
                            seen_names.add(name)

# Inform the user that the process is complete
print('\033[92m' + "Compilation complete. Merged data saved to", output_file + '\033[0m')
print_fireworks()
