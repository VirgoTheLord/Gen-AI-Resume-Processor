import os
import json
import shutil
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from sqlalchemy import create_engine, Column, Integer, String, Text, ForeignKey, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from extractpdf1 import extract_text_from_pdf
from textgenerationfn import extract_resume_data
from export_as_csv import export_to_csv

# Database configuration
DATABASE_URL = 'mysql+mysqlconnector://root:@localhost/resumeparser'

# Setting up the ORM base class
Base = declarative_base()

# Defining the User model
class User(Base):
    __tablename__ = 'user'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    designation = Column(String(255), nullable=False)
    skills = Column(Text, nullable=False)
    summary = Column(Text, nullable=True)
    projects = relationship('Project', back_populates='user')

# Defining the Project model
class Project(Base):
    __tablename__ = 'project'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    tech = Column(Text, nullable=True)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    user = relationship('User', back_populates='projects')

# Creating the engine and session
engine = create_engine(DATABASE_URL, echo=True)
Session = sessionmaker(bind=engine)

# Create tables if they don't exist
Base.metadata.create_all(engine)

# Global variable to store folder path
selected_folder_path = ""

def process_pdf(api_token, repo_id, max_new_tokens, pdf_path):
    paragraph = extract_text_from_pdf(pdf_path)
    
    if not paragraph:
        print(f"Failed to extract text from the PDF: {pdf_path}")
        return
    
    session = Session()
    
    try:
        result = extract_resume_data(api_token, repo_id, max_new_tokens, paragraph)
        print("Raw LLM output:", result)
        
        # Debugging: Print the result to verify its structure
        print(f"LLM result for {pdf_path}: {result}")
        
        # Validate and load JSON data
        json_data = json.loads(result)

        user_data = json_data.get('user', {})
        name = user_data.get('name', '')
        designation = user_data.get('designation', '')
        skills = ', '.join(user_data.get('skills', []))
        summary = user_data.get('summary', '')

        print(f"Extracted Data - Name: {name}, Designation: {designation}, Skills: {skills}, Summary: {summary}")

        # Create a new User instance
        user = User(name=name, designation=designation, skills=skills, summary=summary)
        session.add(user)
        session.commit()

        print(f"Inserted User - ID: {user.id}, Name: {user.name}, Designation: {user.designation}")

        # Insert projects
        projects = json_data.get('projects', [])
        for project in projects:
            title = project.get('title', '')
            description = project.get('description', '')
            tech = project.get('tech', '')
            
            # Create a new Project instance and associate it with the user
            project_instance = Project(
                title=title, description=description, tech=tech, user_id=user.id
            )
            session.add(project_instance)
        
        session.commit()
        print(f"Data inserted successfully for {pdf_path}.")

    except json.JSONDecodeError as e:
        print(f"Error converting to JSON for {pdf_path}: {e}")
        print(f"Result content: {result}")
        session.rollback()
    except Exception as e:
        print(f"An error occurred with {pdf_path}: {e}")
        session.rollback()
    finally:
        session.close()

DESTINATION_FOLDER = "C:\\Users\\Alwin\\OneDrive\\Desktop\\Completed Processing"

def update_database(api_token, repo_id, max_new_tokens, paths):
    for pdf_path in paths:
        if pdf_path.endswith(".pdf"):
            process_pdf(api_token, repo_id, max_new_tokens, pdf_path)
            # Move the PDF to the destination folder
            try:
                shutil.move(pdf_path, os.path.join(DESTINATION_FOLDER, os.path.basename(pdf_path)))
                print(f"Moved {pdf_path} to {DESTINATION_FOLDER}")
            except Exception as e:
                print(f"Error moving {pdf_path}: {e}")

def retrieve_data(username):
    session = Session()
    try:
        # Match names starting with the typed characters
        users = session.query(User).filter(User.name.like(f"{username}%")).all()
        user_data = []
        for user in users:
            user_info = {
                'id': user.id,
                'name': user.name,
                'designation': user.designation,
                'skills': user.skills,
                'summary': user.summary,
                'projects': [
                    {
                        'title': project.title,
                        'description': project.description,
                        'tech': project.tech
                    } for project in user.projects
                ]
            }
            user_data.append(user_info)
        return user_data
    except Exception as e:
        print(f"An error occurred while retrieving data: {e}")
        return []
    finally:
        session.close()

def search_user():
    # Hide any existing user details frame
    for widget in app.winfo_children():
        if isinstance(widget, tk.Frame) and widget != frm_folder and widget != frm_clear_db and widget != frm_search:
            widget.pack_forget()

    username = entry_username.get().strip()
    tree_results.delete(*tree_results.get_children())

    session = Session()
    try:
        if username:
            # Fetch users whose names start with the provided username
            users = session.query(User).filter(User.name.like(f"{username}%")).all()
        else:
            # Fetch all users if no username is provided
            users = session.query(User).all()

        if users:
            for user in users:
                tree_results.insert('', 'end', values=(user.name, user.designation, user.summary))
        else:
            tree_results.insert('', 'end', values=('No results found', '', ''))

    except Exception as e:
        print(f"An error occurred while retrieving data: {e}")
        tree_results.insert('', 'end', values=('No results found', '', ''))

    finally:
        session.close()


def open_files():
    global selected_folder_path
    selected_folder_path = filedialog.askdirectory(title="Select Folder Containing PDFs")
    if selected_folder_path:
        entry_folder.delete(0, tk.END)
        entry_folder.insert(0, selected_folder_path)

def upload_files():
    folder_path = selected_folder_path
    if not folder_path or not os.path.isdir(folder_path):
        messagebox.showerror("Error", "Please select a valid folder using the 'Browse' button.")
        return

    file_paths = [os.path.join(folder_path, file) for file in os.listdir(folder_path) if file.endswith(".pdf")]
    if file_paths:
        update_database(api_token, repo_id, max_new_tokens, file_paths)
        messagebox.showinfo("Success", "Database updated successfully!")
    else:
        messagebox.showinfo("Info", "No PDF files found in the selected folder.")


def clear_database():
    session = Session()
    try:
        session.execute(text('SET FOREIGN_KEY_CHECKS = 0;'))
        session.query(Project).delete()
        session.query(User).delete()
        session.execute(text('SET FOREIGN_KEY_CHECKS = 1;'))
        session.commit()
        messagebox.showinfo("Success", "Database cleared successfully!")
    except Exception as e:
        session.rollback()
        messagebox.showerror("Error", f"An error occurred while clearing the database: {e}")
    finally:
        session.close()

def on_closing():
    app.destroy()

def show_user_details_in_place(event):
    selected_item = tree_results.selection()
    if selected_item:
        selected_name = tree_results.item(selected_item[0], 'values')[0]
        user_data = retrieve_data(selected_name)
        if user_data:
            user_data = user_data[0]  # Assuming we get the exact match

            # Hide the search results and unnecessary labels
            tree_results.pack_forget()
            frm_search.pack_forget()

            # Create a frame for user details
            frm_user_details = tk.Frame(app, bg='#F5F5F5')
            frm_user_details.pack(fill='both', expand=True, padx=20, pady=20)

            # Name
            lbl_name = tk.Label(frm_user_details, text="Name:", font=('Segoe UI', 10, 'bold'), bg='#F5F5F5')
            lbl_name.grid(row=0, column=0, sticky='w', padx=10, pady=5)
            lbl_name_value = tk.Label(frm_user_details, text=user_data['name'], font=('Segoe UI', 10), bg='#F5F5F5')
            lbl_name_value.grid(row=0, column=1, sticky='w', padx=10, pady=5)

            # Designation
            lbl_designation = tk.Label(frm_user_details, text="Designation:", font=('Segoe UI', 10, 'bold'), bg='#F5F5F5')
            lbl_designation.grid(row=1, column=0, sticky='w', padx=10, pady=5)
            lbl_designation_value = tk.Label(frm_user_details, text=user_data['designation'], font=('Segoe UI', 10), bg='#F5F5F5')
            lbl_designation_value.grid(row=1, column=1, sticky='w', padx=10, pady=5)

            # Skills
            lbl_skills = tk.Label(frm_user_details, text="Skills:", font=('Segoe UI', 10, 'bold'), bg='#F5F5F5')
            lbl_skills.grid(row=2, column=0, sticky='nw', padx=10, pady=5)
            text_skills = tk.Text(frm_user_details, height=4, width=60, wrap=tk.WORD, font=('Segoe UI', 10), bg='#FFFFFF', fg='#333333')
            text_skills.grid(row=2, column=1, padx=10, pady=5, sticky='ew')
            text_skills.insert(tk.END, user_data['skills'])
            text_skills.config(state='disabled')

            # Summary
            lbl_summary = tk.Label(frm_user_details, text="Summary:", font=('Segoe UI', 10, 'bold'), bg='#F5F5F5')
            lbl_summary.grid(row=3, column=0, sticky='nw', padx=10, pady=5)
            text_summary = tk.Text(frm_user_details, height=6, width=60, wrap=tk.WORD, font=('Segoe UI', 10), bg='#FFFFFF', fg='#333333')
            text_summary.grid(row=3, column=1, padx=10, pady=5, sticky='ew')
            text_summary.insert(tk.END, user_data['summary'])
            text_summary.config(state='disabled')

            # Projects Label
            lbl_projects = tk.Label(frm_user_details, text="Projects:", font=('Segoe UI', 10, 'bold'), bg='#F5F5F5')
            lbl_projects.grid(row=4, column=0, sticky='nw', padx=10, pady=5)

            # Projects Treeview
            columns = ('Title', 'Description', 'Tech Used')
            tree_projects = ttk.Treeview(frm_user_details, columns=columns, show='headings', style='Treeview')
            tree_projects.grid(row=4, column=1, padx=10, pady=5, sticky='nsew')

            for col in columns:
                tree_projects.heading(col, text=col)
                tree_projects.column(col, minwidth=0, width=150)

            # Insert project data
            for project in user_data['projects']:
                tree_projects.insert('', 'end', values=(project['title'], project['description'], project['tech']))

            tree_projects.bind('<<TreeviewSelect>>', lambda e: show_project_details_in_place(e, user_data['projects']))

            # Frame for the Back button
            frm_back_button = tk.Frame(frm_user_details, bg='#F5F5F5')
            frm_back_button.grid(row=5, column=0, columnspan=2, pady=10, sticky='w')

            # Back button
            btn_back = tk.Button(frm_back_button, text="Back", command=lambda: show_search_results(frm_user_details))
            btn_back.pack(anchor='w', padx=10, pady=5)

            frm_user_details.grid_rowconfigure(4, weight=1)
            frm_user_details.grid_columnconfigure(1, weight=1)

def show_user_details_in_place(event):
    selected_item = tree_results.selection()
    if selected_item:
        selected_name = tree_results.item(selected_item[0], 'values')[0]
        user_data = retrieve_data(selected_name)
        if user_data:
            user_data = user_data[0]  # Assuming we get the exact match

            # Hide the search results
            lbl_title.pack_forget()
            frm_folder.pack_forget()
            frm_clear_db.pack_forget()
            frm_search.pack_forget()
            tree_results.pack_forget()
            lbl_select_folder.pack_forget()
            lbl_search_user.pack_forget()

            # Create a frame for user details
            frm_user_details = tk.Frame(app, bg='#F5F5F5')
            frm_user_details.pack(fill='both', expand=True, padx=20, pady=20)

            # Name
            lbl_name = tk.Label(frm_user_details, text="Name:", font=('Segoe UI', 10, 'bold'), bg='#F5F5F5')
            lbl_name.grid(row=0, column=0, sticky='w', padx=10, pady=5)
            lbl_name_value = tk.Label(frm_user_details, text=user_data['name'], font=('Segoe UI', 10), bg='#F5F5F5')
            lbl_name_value.grid(row=0, column=1, sticky='w', padx=10, pady=5)

            # Designation
            lbl_designation = tk.Label(frm_user_details, text="Designation:", font=('Segoe UI', 10, 'bold'), bg='#F5F5F5')
            lbl_designation.grid(row=1, column=0, sticky='w', padx=10, pady=5)
            lbl_designation_value = tk.Label(frm_user_details, text=user_data['designation'], font=('Segoe UI', 10), bg='#F5F5F5')
            lbl_designation_value.grid(row=1, column=1, sticky='w', padx=10, pady=5)

            # Skills
            lbl_skills = tk.Label(frm_user_details, text="Skills:", font=('Segoe UI', 10, 'bold'), bg='#F5F5F5')
            lbl_skills.grid(row=2, column=0, sticky='nw', padx=10, pady=5)
            text_skills = tk.Text(frm_user_details, height=4, width=60, wrap=tk.WORD, font=('Segoe UI', 10), bg='#FFFFFF', fg='#333333')
            text_skills.grid(row=2, column=1, padx=10, pady=5, sticky='ew')
            text_skills.insert(tk.END, user_data['skills'])
            text_skills.config(state='disabled')

            # Summary
            lbl_summary = tk.Label(frm_user_details, text="Summary:", font=('Segoe UI', 10, 'bold'), bg='#F5F5F5')
            lbl_summary.grid(row=3, column=0, sticky='nw', padx=10, pady=5)
            text_summary = tk.Text(frm_user_details, height=6, width=60, wrap=tk.WORD, font=('Segoe UI', 10), bg='#FFFFFF', fg='#333333')
            text_summary.grid(row=3, column=1, padx=10, pady=5, sticky='ew')
            text_summary.insert(tk.END, user_data['summary'])
            text_summary.config(state='disabled')

            # Projects Label
            lbl_projects = tk.Label(frm_user_details, text="Projects:", font=('Segoe UI', 10, 'bold'), bg='#F5F5F5')
            lbl_projects.grid(row=4, column=0, sticky='nw', padx=10, pady=5)

            # Projects Treeview
            columns = ('Title', 'Description', 'Tech Used')
            tree_projects = ttk.Treeview(frm_user_details, columns=columns, show='headings', style='Treeview')
            tree_projects.grid(row=4, column=1, padx=10, pady=5, sticky='nsew')

            for col in columns:
                tree_projects.heading(col, text=col)
                tree_projects.column(col, minwidth=0, width=150)

            # Insert project data
            for project in user_data['projects']:
                tree_projects.insert('', 'end', values=(project['title'], project['description'], project['tech']))

            tree_projects.bind('<<TreeviewSelect>>', lambda e: show_project_details_in_place(e, user_data['projects']))

            # Export Results Button
            btn_export = tk.Button(frm_user_details, text="Export Results", command=lambda: export_to_csv(user_data), font=('Segoe UI', 10), bg='#0078D4', fg='#FFFFFF', relief='flat')
            btn_export.grid(row=5, column=0, columnspan=2, pady=10)
            btn_export.config(activebackground='#005A9E')

            # Back button
            btn_back = tk.Button(frm_user_details, text="Back", command=show_search_results, font=('Segoe UI', 10), bg='#0078D4', fg='#FFFFFF', relief='flat')
            btn_back.grid(row=6, column=0, columnspan=2, pady=10)
            btn_back.config(activebackground='#005A9E')

            # Configure grid weights
            frm_user_details.grid_rowconfigure(4, weight=1)
            frm_user_details.grid_columnconfigure(1, weight=1)

def show_search_results():
    # Clear the user details view
    for widget in app.winfo_children():
        if isinstance(widget, tk.Frame) and widget not in (frm_folder, frm_clear_db, frm_search):
            widget.pack_forget()
    
    # Show the search results and other initial widgets
    lbl_title.pack(pady=20)
    frm_folder.pack(fill='x', padx=20)
    frm_clear_db.pack(fill='x', padx=20, pady=10)
    frm_search.pack(fill='x', padx=20)
    tree_results.pack(fill='both', expand=True, padx=20, pady=20)


def show_project_details_in_place(event, projects):
    selected_item = event.widget.selection()
    if selected_item:
        project_data = event.widget.item(selected_item, 'values')
        project_title = project_data[0]  # Assuming the title is unique

        # Find the full project details using the title
        project_details = next((project for project in projects if project['title'] == project_title), None)
        if project_details:
            # Display project details
            project_window = tk.Toplevel(app)
            project_window.title(f"Project Details - {project_details['title']}")

            # Configure window resizing
            project_window.grid_columnconfigure(1, weight=1)
            project_window.grid_rowconfigure(1, weight=1)
            project_window.grid_rowconfigure(2, weight=1)

            # Project Title
            lbl_project_title = tk.Label(project_window, text="Title:", font=('Segoe UI', 10, 'bold'), bg='#F5F5F5')
            lbl_project_title.grid(row=0, column=0, sticky='w', padx=10, pady=5)
            lbl_project_title_value = tk.Label(project_window, text=project_details['title'], font=('Segoe UI', 10), bg='#F5F5F5')
            lbl_project_title_value.grid(row=0, column=1, sticky='w', padx=10, pady=5)

            # Description
            lbl_description = tk.Label(project_window, text="Description:", font=('Segoe UI', 10, 'bold'), bg='#F5F5F5')
            lbl_description.grid(row=1, column=0, sticky='nw', padx=10, pady=5)
            text_description = tk.Text(project_window, height=4, width=60, wrap=tk.WORD, font=('Segoe UI', 10), bg='#FFFFFF', fg='#333333')
            text_description.grid(row=1, column=1, padx=10, pady=5, sticky='nsew')
            text_description.insert(tk.END, project_details['description'])
            text_description.config(state='disabled')

            # Tech Used
            lbl_tech = tk.Label(project_window, text="Tech Used:", font=('Segoe UI', 10, 'bold'), bg='#F5F5F5')
            lbl_tech.grid(row=2, column=0, sticky='nw', padx=10, pady=5)
            text_tech = tk.Text(project_window, height=2, width=60, wrap=tk.WORD, font=('Segoe UI', 10), bg='#FFFFFF', fg='#333333')
            text_tech.grid(row=2, column=1, padx=10, pady=5, sticky='nsew')
            text_tech.insert(tk.END, project_details['tech'])
            text_tech.config(state='disabled')

app = tk.Tk()
app.title("Resume Processor")
app.geometry('800x600')  # Increased size for better layout

# API Configuration
api_token = "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" 
repo_id = "mistralai/Mistral-7B-Instruct-v0.3"
max_new_tokens = 2000
# Set the background color and font style
app.configure(bg='#F5F5F5')
style = ttk.Style()
style.configure('Treeview', background='#FFFFFF', foreground='#333333', fieldbackground='#FFFFFF', font=('Segoe UI', 10))
style.configure('Treeview.Heading', font=('Segoe UI', 10, 'bold'), background='#EDEDED')
style.configure('TButton', font=('Segoe UI', 10), background='#0078D4', foreground='#FFFFFF', relief='flat')
style.map('TButton', background=[('active', '#005A9E')])

lbl_title = tk.Label(app, text="Resume Processor", font=('Segoe UI', 16, 'bold'), bg='#F5F5F5', fg='#0078D4')
lbl_title.pack(pady=20)

# Select Folder
lbl_select_folder = tk.Label(app, text="Select Folder:", font=('Segoe UI', 12), bg='#F5F5F5', fg='#333333')
lbl_select_folder.pack(anchor='w', padx=20)

frm_folder = tk.Frame(app, bg='#F5F5F5')
frm_folder.pack(fill='x', padx=20)

entry_folder = tk.Entry(frm_folder, width=40, font=('Segoe UI', 10))
entry_folder.pack(side='left', fill='x', expand=True)

btn_browse = tk.Button(frm_folder, text="Browse", command=open_files)
btn_browse.pack(side='left', padx=5)

btn_upload = tk.Button(frm_folder, text="Upload", command=upload_files)
btn_upload.pack(side='left', padx=5)

# Define a Frame to hold the Clear Database button
frm_clear_db = tk.Frame(app, bg='#F5F5F5')
frm_clear_db.pack(fill='x', padx=20, pady=10)

# Clear Database Button
btn_clear = tk.Button(frm_clear_db, text="Clear Database", command=clear_database)
btn_clear.pack(side='top', padx=5, pady=5)

# Search User
lbl_search_user = tk.Label(app, text="Search User:", font=('Segoe UI', 12), bg='#F5F5F5', fg='#333333')
lbl_search_user.pack(anchor='w', padx=20, pady=10)
frm_search = tk.Frame(app, bg='#F5F5F5')
frm_search.pack(fill='x', padx=20)
entry_username = tk.Entry(frm_search, width=40, font=('Segoe UI', 10))
entry_username.pack(side='left', fill='x', expand=True)
btn_search = tk.Button(frm_search, text="Search", command=search_user)
btn_search.pack(side='right', padx=5)

# Search Results
tree_results = ttk.Treeview(app, columns=('Name', 'Designation', 'Summary'), show='headings')
tree_results.heading('Name', text='Name')
tree_results.heading('Designation', text='Designation')
tree_results.heading('Summary', text='Summary')
tree_results.pack(fill='both', expand=True, padx=20, pady=20)
tree_results.bind('<Double-1>', show_user_details_in_place)


app.protocol("WM_DELETE_WINDOW", on_closing)
app.mainloop()


