import csv
from tkinter import  filedialog, messagebox

def export_to_csv(user_data):
    # Ask the user where to save the file
    file_path = filedialog.asksaveasfilename(defaultextension=".csv",
                                           filetypes=[("CSV files", "*.csv")],
                                           title="Save as")
    if not file_path:
        return  # User cancelled the dialog

    try:
        with open(file_path, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            
            # Write user details
            writer.writerow(['Name', user_data['name']])
            writer.writerow(['Designation', user_data['designation']])
            writer.writerow(['Skills', user_data['skills']])
            writer.writerow(['Summary', user_data['summary']])
            writer.writerow([])
            
            # Write projects
            writer.writerow(['Projects'])
            writer.writerow(['Title', 'Description', 'Tech Used'])
            for project in user_data['projects']:
                writer.writerow([project['title'], project['description'], project['tech']])
        
        messagebox.showinfo("Success", f"Data exported successfully to {file_path}")
    
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred while exporting data: {e}")