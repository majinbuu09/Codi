import contextlib
import re
import tkinter as tk
from tkinter import ttk
from tkinter import scrolledtext
from tkinter import filedialog
import kivy
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem
from kivy.config import Config
Config.set('graphics', 'resizable', '0')
Window.size = (360, 640)
import language
from PIL import Image, ImageTk
import openai
import io
import sys
import json
import git
import torch
import speech_recognition as sr
from numpy import error_message
from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import HtmlFormatter
Builder.load_string('''
<MobileCodiUI>:
    orientation: 'vertical'
    padding: [20, 40, 20, 40]

    TextInput:
        id: user_input
        hint_text: 'Enter code here...'
        multiline: True
        size_hint_y: None
        height: 300
        font_size: '18sp'
        padding: [10, 10, 10, 10]

    Button:
        text: 'Generate'
        size_hint: (1, None)
        height: 60
        on_release: root.generate_code()

    Label:
        id: output_label
        text: ''
        size_hint_y: None
        height: 100

''')
class Codi:
    def __init__(self, root):
        self.root = root
        self.root.title("Codi")
        self.root.configure(bg="#000")
        self.container = tk.Frame(self.root, bg="#333")
        self.container.pack(padx=20, pady=20)
        self.app_picture = Image.open("codi.png") # CHANGE TO WHATEVER .png YOU WANT
        self.app_picture = self.app_picture.resize((200, 200), Image.LANCZOS)
        self.app_picture = ImageTk.PhotoImage(self.app_picture)
        self.app_picture_label = tk.Label(
            self.container, image=self.app_picture, bg="#333"
        )
        self.available_fonts = {
            "Arial": ("Arial", "normal"),
            "Times New Roman": ("Times New Roman", "normal"),
            "Courier New": ("Courier New", "normal"),
            "Verdana": ("Verdana", "normal"),
        }
        self.user_input.bind("<Return>", self.on_user_input)
        self.app_picture_label.image = self.app_picture
        self.app_picture_label.pack()
        self.user_input = scrolledtext.ScrolledText(
            self.container, wrap=tk.WORD, width=50, height=10, bg="#222", fg="#fff"
        )
        self.user_input.pack()
        self.generate_btn = tk.Button(
            self.container,
            text="Generate",
            command=self.generate_response,
            bg="#555",
            fg="#fff",
        )
        self.generate_btn.pack()
        self.clear_btn = tk.Button(
            self.container,
            text="Clear Conversation",
            command=self.clear_conversation,
            bg="#555",
            fg="#fff",
        )
        self.clear_btn.pack()
        self.conversation = tk.Text(
            self.container, wrap="none", width=60, height=10, bg="#111", fg="#ddd"
        )
        self.conversation.pack()
        self.avatar = Image.open("codi.png")
        self.avatar = self.avatar.resize((100, 100), Image.LANCZOS)
        self.avatar = ImageTk.PhotoImage(self.avatar)
        self.avatar_label = tk.Label(self.container, image=self.avatar, bg="#333")
        self.avatar_label.image = self.avatar
        self.avatar_label.pack()
        self.snippet_combobox = ttk.Combobox(self.container, values=[], state="readonly")
        self.snippet_combobox.pack()
        self.snippet_combobox.bind("<<ComboboxSelected>>", self.insert_selected_snippet)
        self.code_snippets = {
            "Factorial Function": "def factorial(n):\n    if n == 0:\n        return 1\n    else:\n        return n * factorial(n - 1)",
            "Prime Check": "def is_prime(n):\n    if n <= 1:\n        return False\n    for i in range(2, int(n ** 0.5) + 1):\n        if n % i == 0:\n            return False\n    return True",
            # Add more code snippets as needed
        }
        self.snippet_combobox["values"] = list(self.code_snippets.keys())
        self.language_var = tk.StringVar()
        self.language_combobox = ttk.Combobox(
            self.container,
            textvariable=self.language_var,
            values=["Python", "JavaScript", "Java"],
        )
        self.language_combobox.pack()
        self.conversation.tag_config("user", foreground="blue")
        self.conversation.tag_config("bot", foreground="green")
        self.generate_btn = tk.Button(
            self.container,
            text="Generate",
            command=self.generate_response,  # Use the correct function here
            bg="#555",
            fg="#fff",
        )
        self.generate_btn.pack()
        self.clear_btn = tk.Button(
            self.container,
            text="Clear Conversation",
            command=self.clear_conversation,  # Use the correct function here
            bg="#555",
            fg="#fff",
        )
        self.clear_btn.pack()
        self.generate_callback = self.generate_response
        self.clear_callback = self.clear_conversation
        self.generate_btn = tk.Button(
            self.container,
            text="Generate",
            command=self.generate_callback,
            bg="#555",
            fg="#fff",
        )
        self.generate_btn.pack()
        self.clear_btn = tk.Button(
            self.container,
            text="Clear Conversation",
            command=self.clear_callback,
            bg="#555",
            fg="#fff",
        )
        self.clear_btn.pack()
        self.suggestions_combobox = ttk.Combobox(self.container, values=[], state="readonly")
        self.suggestions_combobox.pack()

        # Create a text widget to display code execution output
        self.execution_output = scrolledtext.ScrolledText(
            self.container, wrap=tk.WORD, width=50, height=10, bg="#222", fg="#fff"
        )
        self.execution_output.pack()
        self.supported_languages = [
            "Python",
            "JavaScript",
            "Java",
            "C",
            "C++",
            "C#",
            "Ruby",
            "PHP",
            "Swift",
            "Kotlin",
            "TypeScript",
            "Rust",
            "Go",
            "Perl",
            "Haskell",
            "Scala",
            "Lua",
            "SQL",
            "HTML",
            "CSS",
            "XML",
            "JSON",
            "Markdown",
        ]
        self.language_combobox = ttk.Combobox(
            self.container, textvariable=self.language_var, values=self.supported_languages
        )
        self.language_combobox.pack()
        self.user_profile = {
            "conversation_history": [],
            "preferences": {
                "theme": "light",
                "font_family": "Arial",
                "font_size": 12,
            },
            "code_snippets": [],
        }
        self.load_user_profile()
    def on_user_input(self, event):
        user_input = self.user_input.get("1.0", tk.END).strip()
        if user_input and user_input[-1] != "\n":
            suggestions = self.generate_code_suggestions(user_input)
            self.show_suggestions(suggestions)
    def change_theme(self, theme):
        themes = {
            "light": {
                "bg_color": "#FFFFFF",
                "fg_color": "#000000",
                "highlight_color": "#DDDDDD",
                "btn_bg_color": "#0077FF",
                "btn_fg_color": "#FFFFFF",
            },
            "dark": {
                "bg_color": "#333333",
                "fg_color": "#FFFFFF",
                "highlight_color": "#555555",
                "btn_bg_color": "#22AA22",
                "btn_fg_color": "#FFFFFF",
            },
            "blue": {
                "bg_color": "#0099CC",
                "fg_color": "#FFFFFF",
                "highlight_color": "#0077AA",
                "btn_bg_color": "#DD4400",
                "btn_fg_color": "#FFFFFF",
            },
            "green": {
                "bg_color": "#00CC66",
                "fg_color": "#FFFFFF",
                "highlight_color": "#009955",
                "btn_bg_color": "#FFCC00",
                "btn_fg_color": "#333333",
            },
            "purple": {
                "bg_color": "#9933CC",
                "fg_color": "#FFFFFF",
                "highlight_color": "#7722AA",
                "btn_bg_color": "#FF6600",
                "btn_fg_color": "#FFFFFF",
            },
            "custom": {
                "bg_color": "#F5F5F5",
                "fg_color": "#333333",
                "highlight_color": "#CCCCCC",
                "btn_bg_color": "#9900CC",
                "btn_fg_color": "#FFFFFF",
            },
        }
        selected_theme = themes.get(theme)
        if selected_theme:
            self.root.configure(bg=selected_theme["bg_color"])
            self.container.configure(bg=selected_theme["bg_color"])
            self.user_input.configure(bg=selected_theme["highlight_color"], fg=selected_theme["fg_color"])
            self.generate_btn.configure(bg=selected_theme["btn_bg_color"], fg=selected_theme["btn_fg_color"])
            self.clear_btn.configure(bg=selected_theme["btn_bg_color"], fg=selected_theme["btn_fg_color"])
            self.conversation.configure(bg=selected_theme["bg_color"], fg=selected_theme["fg_color"])
            self.avatar_label.configure(bg=selected_theme["bg_color"])
            self.language_combobox.configure(bg=selected_theme["highlight_color"], fg=selected_theme["fg_color"])
            self.display_message("bot", f"Theme changed to '{theme}'")
        else:
            self.display_message("bot", f"Theme '{theme}' not found")
        self.change_theme("custom")
    def generate_code_suggestions(self, prompt):
        openai.api_key = "YOUR-API-KEY"
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=prompt,
            max_tokens=100, temperature=0.2)
        suggestions = response.choices[0].text.strip()
        return suggestions
    def show_suggestions(self, suggestions):
            self.suggestions_combobox["values"] = suggestions
            if suggestions:
                self.suggestions_combobox.current(0)
                self.suggestions_combobox.bind(
                    "<<ComboboxSelected>>", self.insert_selected_suggestion
                )
                self.suggestions_combobox.place(x=10, y=300)
    def insert_selected_suggestion(self, event):
        selected_suggestion = self.suggestions_combobox.get()
        if selected_suggestion:
            self.user_input.insert(tk.END, selected_suggestion + "\n")
            self.suggestions_combobox.place_forget()
    def execute_generated_code(self, code):
        try:
            original_stdout = sys.stdout
            captured_output = io.StringIO()
            sys.stdout = captured_output
            exec(code)
            sys.stdout = original_stdout
            execution_result = captured_output.getvalue()
            self.execution_output.insert(tk.END, execution_result + "\n")
        except Exception as e:(
            error_message) = f"Error: {str(e)}"
        self.execution_output.insert(tk.END, error_message + "\n")
        self.execution_output.see(tk.END)
    def change_font(self, font_family, font_size):
        selected_font = self.available_fonts.get(font_family)
        if selected_font:
            font_name, font_style = selected_font
            new_font = tkfont.Font(family=font_name, size=font_size, weight=font_style)
            self.user_input.configure(font=new_font)
            self.conversation.configure(font=new_font)
            self.execution_output.configure(font=new_font)
            self.display_message("bot", f"Font changed to '{font_family}'")
        else:
            self.display_message("bot", f"Font '{font_family}' not found")
    def insert_selected_snippet(self, event):
        selected_snippet = self.snippet_combobox.get()
        if selected_snippet:
            snippet = self.code_snippets.get(selected_snippet, "")
            if snippet:
                self.user_input.insert(tk.END, snippet + "\n")
    def update_supported_languages(self, languages):
        self.language_combobox["values"] = languages
    def save_user_profile(self):
        profile_filename = "user_profile.json"
        self.user_profile["conversation_history"] = self.conversation.get("1.0", tk.END).split("\n")
        self.user_profile["preferences"]["theme"] = self.current_theme
        self.user_profile["preferences"]["font_family"] = self.current_font_family
        self.user_profile["preferences"]["font_size"] = self.current_font_size
        self.user_profile["code_snippets"] = self.code_snippets
        with open(profile_filename, "w") as json_file:
            json.dump(self.user_profile, json_file, indent=4)
        self.display_message("bot", f"User profile saved to {profile_filename}")
    def load_user_profile(self):
        profile_filename = "user_profile.json"
        try:
            with open(profile_filename, "r") as json_file:
                self.user_profile = json.load(json_file)
            self.restore_previous_state()
            self.display_message("bot", f"User profile loaded from {profile_filename}")
        except FileNotFoundError:
            self.display_message("bot", "User profile not found")
    def restore_previous_state(self):
        # Restore conversation history
        conversation_history = "\n".join(self.user_profile["conversation_history"])
        self.conversation.delete("1.0", tk.END)
        self.conversation.insert(tk.END, conversation_history)
        self.change_theme(self.user_profile["preferences"]["theme"])
        self.change_font(
            self.user_profile["preferences"]["font_family"],
            self.user_profile["preferences"]["font_size"],
        )
        self.code_snippets = self.user_profile["code_snippets"]
    def get_voice_input(self):
        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            try:
                self.display_message("bot", "Listening for voice input...")
                audio = recognizer.listen(source, timeout=5)
                self.display_message("bot", "Processing voice input...")
                try:
                    user_input = recognizer.recognize_google(audio)
                    self.user_input.insert(tk.END, user_input + "\n")
                except sr.UnknownValueError:
                    self.display_message("bot", "Sorry, I couldn't understand the voice input.")
                except sr.RequestError:
                    self.display_message("bot", "There was an issue with the speech recognition service.")
            except sr.WaitTimeoutError:
                self.display_message("bot", "No voice input detected.")
    def commit_to_git(self, message):
        try:
            repo = git.Repo("path/to/your/git/repository")
            repo.git.add(all=True)
            repo.git.commit("-m", message)
            self.display_message("bot", "Code successfully committed to Git repository.")
        except git.exc.InvalidGitRepositoryError:
            self.display_message("bot", "Not a valid Git repository.")
        except git.exc.GitCommandError:
            self.display_message("bot", "Error committing code to Git repository.")


    def connect_to_collaboration(self, room_id):
        try:
            # Simulate connecting to a real-time collaboration service using the room ID
            # You may use an external library or service to establish the connection

            # For demonstration purposes, we'll print a message to indicate successful connection
            print(f"Connected to collaboration room: {room_id}")

            # You can implement the actual connection logic here, such as establishing a WebSocket connection

            # Set up a callback function to receive updates from the collaboration service
    def collaboration_update_callback(data):
        # Process collaboration updates received from the service
        # Update the UI or perform actions based on the data

        # For demonstration purposes, we'll print the received data
        print("Collaboration Update:", data)

    # Register the callback function with the collaboration service
    # Collaboration service should call this function whenever there's an update
    # Example: collaboration_service.register_callback(collaboration_update_callback)

    # Provide a way to disconnect from the collaboration service
        # Provide a way to disconnect from the collaboration service
    def disconnect_from_collaboration():
        try:
            # Implement the logic to disconnect from the collaboration service
            # Close the WebSocket connection or perform necessary cleanup

            # For demonstration purposes, we'll print a message
            print("Disconnected from collaboration")

            # You may also want to unregister the callback
            # Example: collaboration_service.unregister_callback(collaboration_update_callback)

    except Exception as e:
        error_message = f"Error disconnecting from collaboration: {str(e)}"
        self.display_message("bot", error_message)
disconnect_button = tk.Button(
        self.container,
        text="Disconnect from Collaboration",
        command=disconnect_from_collaboration,
        bg="#555",
        fg="#fff",
    )
    disconnect_button.pack()
    except Exception as e:error_message = f"Error connecting to collaboration: {str(e)}"
        self.display_message("bot", error_message)
    def suggest_prompt(self, context):
        try:
            openai.api_key = "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"
            response = openai.Completion.create(
                engine="text-davinci-003", prompt=context, max_tokens=100, temperature=0.5
            )
            generated_suggestions = response.choices[0].text.strip().split("\n")
            self.suggestions_combobox["values"] = generated_suggestions
            if generated_suggestions:
                self.suggestions_combobox.current(0)
                self.suggestions_combobox.bind(
                    "<<ComboboxSelected>>", self.insert_selected_suggestion
                )
                self.suggestions_combobox.place(x=10, y=300)
        except Exception as e:\
        (error_message) = f"Error generating prompt suggestions: {str(e)}"
                self.display_message("bot", error_message)
    def explain_code(self, code):
        try:
            openai.api_key = "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"
            prompt = f"Explain the following code:\n\n{code}\n\nExplanation:"
            response = openai.Completion.create(
                engine="text-davinci-003", prompt=prompt, max_tokens=200, temperature=0.7
            )
            explanation = response.choices[0].text.strip()
            self.display_message("bot", f"Explanation:\n{explanation}")
    except Exception as e:
        error_message = f"Error generating code explanation: {str(e)}"
        self.display_message("bot", error_message)
try:
    class MobileCodiUI(BoxLayout):
        def generate_code(self):
            user_input_text = self.ids.user_input.text
            generated_code = f"Generated code: {user_input_text}"
            self.ids.output_label.text = generated_code

    class MobileCodiApp(App):
        def build(self):
            return MobileCodiUI()

        def on_tab_switch(self, instance, tab):
            if tab.text == 'Generate':
                print("Switched to Code Generation tab")
            elif tab.text == 'History':
                print("Switched to History tab")
            elif tab.text == 'Challenges':
                print("Switched to Challenges tab")
            elif tab.text == 'Settings':
                print("Switched to Settings tab")
            elif tab.text == 'Collaboration':
                print("Switched to Collaboration tab")
            elif tab.text == 'Analysis':
                print("Switched to Code Analysis tab")
            elif tab.text == 'Feedback':
                print("Switched to Feedback tab")
    def create_web_version(self):
        try:
            # Design and develop a web-based version of the Codi application

            # 1. Choose a web framework or library (e.g., Django, Flask, React, Vue.js) to build the web application.
            #    This will be the foundation for creating the user interface and handling interactions.

            # 2. Define the layout and components of the web UI, such as text areas, buttons, and code output displays.
            #    Ensure that the design is user-friendly and intuitive for web users.

            # 3. Implement responsive web design to ensure that the UI is accessible and usable on different devices,
            #    including desktops, laptops, tablets, and smartphones.

            # 4. Develop interactive features using HTML, CSS, and JavaScript.
            #    Implement code input and output, user interactions, and dynamic content updates.

            # 5. Integrate the code generation and interaction logic from the existing Codi application into the web version.

            # 6. Incorporate code highlighting and formatting using libraries like Prism.js or highlight.js.

            # 7. Implement features like autocomplete, syntax checking, and error highlighting to aid users in coding.

            # 8. Set up a backend to handle server-side logic, data storage, and API calls if necessary.

            # 9. Test the web version on various browsers (e.g., Chrome, Firefox, Safari, Edge) to ensure compatibility.

            # 10. Optimize the web application's performance and responsiveness for a smooth user experience.

            # 11. Secure the web application by implementing authentication and authorization mechanisms if needed.

            # 12. Deploy the web version to a web hosting platform or server, making it accessible to users on the internet.

            # Display a message indicating that the web version has been successfully created.
            self.display_message("bot", "Web version created successfully.")

        except Exception as e:
            error_message = f"Error creating web version: {str(e)}"
            self.display_message("bot", error_message)
    def execute_code(self, code):
        try:
    except Exception as e:
    def view_collaboration_history(self):
        collaboration_history = []

    def create_code_snapshot():
        current_code =  self.user_input.get("1.0", tk.END).strip()
        collaboration_history.append(current_code)
    history_listbox = self.create_history_listbox(collaboration_history)
    history_listbox.pack()
    self.populate_history_listbox(history_listbox, collaboration_history)
    def select_version(event):
        selected_index = history_listbox.curselection()[0]
        selected_version = collaboration_history[selected_index]
        self.user_input.delete("1.0", tk.END)
        self.user_input.insert(tk.END, selected_version)
    history_listbox.bind("<<ListboxSelect>>", select_version)
    def revert_to_version():
        selected_index = history_listbox.curselection()[0]
        selected_version = collaboration_history[selected_index]
        self.user_input.delete("1.0", tk.END)
        self.user_input.insert(tk.END, selected_version)
    revert_button = tk.Button(
        self.container,
        text="Revert to Selected Version",
        command=revert_to_version,
        bg="#555",
        fg="#fff",
    )
    revert_button.pack()
    self.display_message(
        "bot", "Collaboration history feature implemented successfully."
    )
    except Exception as e:error_message = f"Error implementing collaboration history: {str(e)}"
        self.display_message("bot", error_message)
    def create_history_listbox(self, collaboration_history):
        history_listbox = tk.Listbox(self.container, selectmode=tk.SINGLE)
        return history_listbox
    def populate_history_listbox(self, history_listbox, collaboration_history):
        for version in collaboration_history:
            history_listbox.insert(tk.END, f"Version {collaboration_history.index(version) + 1}")
        def analyze_code(self, code):
            try:
                # Run code analysis tools and display metrics and suggestions for improvement

                # 1. Choose or integrate code analysis libraries or tools that can analyze the provided code.
                #    These tools can check for coding standards, best practices, performance issues, and more.

                # 2. Use the selected code analysis tools to analyze the provided code and gather relevant metrics.
                #    For example, you can check for code complexity, duplicated code, unused variables, and other issues.

                # 3. Generate a report or summary of the code analysis results. This report can include metrics such as:
                #    - Code complexity score
                #    - Number of lines of code
                #    - Number of functions/methods
                #    - Number of comments
                #    - Number of warnings/errors

                # 4. Based on the analysis results, provide suggestions for code improvement.
                #    These suggestions can include refactoring tips, optimizing performance, and adhering to coding standards.

                # 5. Display the code analysis report and suggestions to the user in a user-friendly format.
                #    You can use the conversation or a separate output area to present the analysis results.

                # Display a message indicating that the code analysis feature has been successfully implemented.
                self.display_message("bot", "Code analysis feature implemented successfully.")

            except Exception as e:
                error_message = f"Error performing code analysis: {str(e)}"
                self.display_message("bot", error_message)
    def customize_preferences(self):
        try:
            # Display options for users to customize their coding environment preferences

            # 1. Create a new preferences window or dialog that allows users to customize various preferences.
            #    This window can include options such as:
            #    - Theme selection (light, dark, custom colors)
            #    - Font selection (family, size, style)
            #    - Language selection (programming languages)
            #    - Code style preferences (indentation, brackets, etc.)
            #    - Editor settings (line numbers, word wrap, etc.)

            # 2. Provide user-friendly controls (buttons, dropdowns, checkboxes) for selecting and adjusting preferences.
            #    Use Tkinter widgets to create these controls and organize them within the preferences window.

            # 3. Implement logic to apply the selected preferences to the coding environment.
            #    For example, changing the theme updates the background and text colors of the UI.
            #    Changing the font updates the font settings for the user input, conversation, and execution output areas.

            # 4. Allow users to preview their preference changes before applying them.

            # 5. Display a confirmation message to inform users that their preferences have been updated.

            # Display a message indicating that the preferences customization feature has been successfully implemented.
            self.display_message(
                "bot", "Preferences customization feature implemented successfully."
            )
        except Exception as e:
            error_message = f"Error customizing preferences: {str(e)}"
            self.display_message("bot", error_message)
    def export_code(self, code):
        try:
            file_path = filedialog.asksaveasfilename(
                defaultextension=".py",
                filetypes=[
                    ("Python Files", "*.py"),
                    ("Text Files", "*.txt"),
                    ("All Files", "*.*"),
                ],
            )
            if file_path:
                with open(file_path, "w") as f:
                    f.write(code)
                success_message = f"Code exported successfully to: {file_path}"
                self.display_message("bot", success_message)
        except Exception as e:
            error_message = f"Error exporting code: {str(e)}"
            self.display_message("bot", error_message)
    def generate_ml_response(self, prompt, language):
        try:
            openai.api_key = "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"
            language_to_engine = {
                "Python": "text-davinci-003",
                "JavaScript": "text-davinci-003",
                "Java": "text-davinci-003",
            }
            engine = language_to_engine.get(language, "text-davinci-003")
            response = openai.Completion.create(
                engine=engine,
                prompt=prompt,
                max_tokens=1000,  # Adjust max_tokens as needed
                temperature=0.5,  # Adjust temperature for creativity
            )
            generated_code = response.choices[0].text.strip()
            self.display_message("bot", generated_code)
        except Exception as e:
            # Handle any errors that may occur during the code generation process
            error_message = f"Error generating code response: {str(e)}"
            self.display_message("bot", error_message)
    def provide_feedback(self, feedback):
        try:
            if feedback.lower() == "positive":
                self.display_message(
                    "bot", "Thank you for your positive feedback! I'm glad I could help."
                )
            elif feedback.lower() == "negative":
                self.display_message(
                    "bot",
                    "I'm sorry to hear that. Please provide more details about the issue.",
                )
            else:
                self.display_message(
                    "bot", "Thank you for your feedback! Your input is valuable."
                )
        except Exception as e:
            error_message = f"Error processing feedback: {str(e)}"
            self.display_message("bot", error_message)
    def fetch_api_data(self, api_url):
        try:
            import requests
            response = requests.get(api_url)
            response_data = response.json()
            code = f"""
        # Fetch data from the API
        response = requests.get('{api_url}')
        data = response.json()
    
        # Process and display the data
        for item in data:
            print(item)
        """
            self.display_message(
                "bot", "Here's the code to fetch and process the API data:"
            )
            self.display_message("bot", code)
        except Exception as e:
            error_message = f"Error fetching API data: {str(e)}"
            self.display_message("bot", error_message)
    def offer_coding_challenges(self):
        challenges = [
            {
                "title": "FizzBuzz Challenge",
                "description": "Write a program that prints the numbers from 1 to 100. But for multiples of three, print 'Fizz' instead of the number and for the multiples of five, print 'Buzz'. For numbers which are multiples of both three and five, print 'FizzBuzz'.",
                "solution": """
        for num in range(1, 101):
            if num % 3 == 0 and num % 5 == 0:
                print('FizzBuzz')
            elif num % 3 == 0:
                print('Fizz')
            elif num % 5 == 0:
                print('Buzz')
            else:
                print(num)
        """,
            },
            {
                "title": "Palindrome Check",
                "description": "Write a function to check if a given string is a palindrome (reads the same backward as forward). Ignore spaces, punctuation, and capitalization.",
                "solution": """
        def is_palindrome(s):
            s = s.lower().replace(" ", "").replace(".", "").replace(",", "")
            return s == s[::-1]
        """,
            },
            {
                "title": "Prime Factors",
                "description": "Write a function that returns the prime factors of a given positive integer.",
                "solution": """
        def prime_factors(n):
            factors = []
            i = 2
            while i * i <= n:
                if n % i:
                    i += 1
                else:
                    n //= i
                    factors.append(i)
            if n > 1:
                factors.append(n)
            return factors
        """,
            }
        ]
        self.display_message("bot", "Welcome to the Coding Challenges!")
        for idx, challenge in enumerate(challenges, start=1):
            self.display_message("bot", f"Challenge {idx}: {challenge['title']}")
            self.display_message("bot", f"Description: {challenge['description']}")
            self.display_message("bot", "Do you want to take this challenge? (Yes/No)")
            user_response = self.user_input.get("1.0", tk.END).strip().lower()
            if user_response == "yes":
                self.display_message("bot", "Great! Here's the challenge:")
                self.display_message("bot", challenge["description"])
                self.display_message(
                    "bot",
                    "Now, it's your turn to write the code! Once you're done, you can use the 'Execute' button to test your solution.",
                )
                self.user_input.delete("1.0", tk.END)
                self.user_input.insert(tk.END, challenge["solution"])
                self.display_message(
                    "bot",
                    "Feel free to modify the code and experiment. When you're ready, you can execute it to see the results.",
                )
                self.display_message(
                    "bot",
                    "If you encounter any issues or need assistance, feel free to ask Codi for help.",
                )
            else:
                self.display_message(
                    "bot",
                    "No problem! You can always come back and take on a challenge whenever you're ready.",
                )
        self.display_message("bot", "Thank you for participating in the Coding Challenges!")
    def have_conversation(self, conversation):
        self.display_message("bot", "Hello! Let's have a conversation. Feel free to start.")
        conversation_history = []
        while True:
            user_input = self.user_input.get("1.0", tk.END).strip()
            if user_input.lower() == "exit":
                self.display_message("bot", "Goodbye! Conversation ended.")
                break
            if user_input:
                conversation_history.append(f"User: {user_input}")
                full_conversation = "\n".join(conversation_history)
                response = self.generate_response_api(
                    full_conversation, self.language_var.get(), 1000
                )
                conversation_history.append(f"Codi: {response}")
                self.conversation.delete("1.0", tk.END)
                self.display_message("bot", full_conversation)
            self.user_input.delete("1.0", tk.END)
        self.display_message(
            "bot", "Conversation ended. Feel free to start a new one anytime!"
        )
    def check_syntax(self):
        user_input = self.user_input.get("1.0", tk.END).strip()
        if user_input:
            language = self.language_var.get()
            is_valid = self.check_syntax_api(user_input, language)
            self.display_syntax_status(is_valid)
    def check_syntax_api(self, code, language):
        if language.lower() == "python":
            try:
                from pyflakes.api import check
                temp_code_file = io.StringIO(code)
                syntax_errors = []
                with contextlib.redirect_stderr(syntax_errors.append):
                    check(temp_code_file, filename="temp.py")
                temp_code_file.close()
                if syntax_errors:
                    return False
                else:
                    return True
            except Exception as e:
                # Handle any errors that may occur during the syntax check
                self.display_message("bot", f"Error checking syntax: {str(e)}")
                return False
        else:
            self.display_message("bot", f"Syntax checking is not supported for {language}.")
            return False
    def display_syntax_status(self, is_valid):
        if is_valid:
            syntax_label = tk.Label(self.container, text="Syntax is Valid", fg="green")
        else:
            syntax_label = tk.Label(self.container, text="Syntax is Invalid", fg="red")
        syntax_label.pack()
    def generate_response(self):
        user_input = self.user_input.get("1.0", tk.END).strip()
        if user_input:
            language = self.language_var.get()
            response = self.generate_response_api(user_input, language, 1000)
            self.display_message("user", user_input)
            self.display_message("bot", response)
            self.user_input.delete("1.0", tk.END)
    def generate_response_api(self, prompt, language, max_tokens):
        openai.api_key = "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"
        language_to_engine = {
            "Python": "text-davinci-003",
            "JavaScript": "text-davinci-003",
            "Java": "text-davinci-003",
        }
        engine = language_to_engine.get(language, "text-davinci-003")
        response = openai.Completion.create(
            engine=engine, prompt=prompt, max_tokens=max_tokens, temperature=0.2
        )
        return response.choices[0].text.strip()
    def code_autocompletion(self, event):
        user_input = self.user_input.get("1.0", tk.END).strip()
        if user_input:
            language = self.language_var.get()
            response = self.generate_response_api(user_input, language, 100)
            self.user_input.delete("1.0", tk.END)
            self.user_input.insert(tk.END, response)
    def clear_conversation(self):
        self.conversation.delete("1.0", tk.END)
    def display_message(self, role, content):
        self.conversation.insert(tk.END, f"{role.capitalize()}: ", role)
        if role == "user":
            self.conversation.insert(tk.END, content, "user")
        else:
            lexer = get_lexer_by_name(language.lower())
            formatter = HtmlFormatter()
            highlighted_code = highlight(content, lexer, formatter)
            highlighted_code = re.sub(r"<.*?>", "", highlighted_code)
            self.conversation.insert(tk.END, highlighted_code, "bot")
        self.conversation.insert(tk.END, "\n")
        self.conversation.see(tk.END)
        if role == "bot" and "def" in content:
            self.conversation.insert(tk.END, "Code Snippet:\n", "snippet_title")
            self.conversation.insert(tk.END, content, "snippet")
            self.conversation.see(tk.END)
    def save_code_snippet(self):
        snippet = self.conversation.get("snippet_title.first", "snippet.last")
        file_path = filedialog.asksaveasfilename(
            defaultextension=".py", filetypes=[("Python Files", "*.py")]
        )
        if file_path:
            with open(file_path, "w") as f:
                f.write(snippet)
if __name__ == "__main__":
    root = tk.Tk()
    ui = Codi(root)
    codi_instance = Codi(root)  # Initialize your Codi instance
    codi_instance.change_font("Matrix", 14)
    codi_instance.save_user_profile()
    prompt = "Generate a Python function to calculate the factorial of a number."
    suggestions = codi_instance.generate_code_suggestions(prompt)
    print(suggestions)
    codi_instance.show_suggestions(suggestions)
    suggestions = [
        "def calculate_factorial(n):",
        "for i in range(n):",
        "if n <= 0:",
    ]
    generated_code = """
    def calculate_factorial(n):
        factorial = 1
        for i in range(1, n + 1):
            factorial *= i
        return factorial   
    result = calculate_factorial(5)
    print(result)
    """
    updated_languages = [
        "Python",
        "JavaScript",
        "Java",
        "C",
        "C++",
        "C#",
        "Ruby",
        "PHP",
        "Swift",
        "Kotlin",
        "TypeScript",
        "Rust",
        "Go",
        "Perl",
        "Haskell",
        "Scala",
        "Lua",
        "SQL",
        "HTML",
        "CSS",
        "XML",
        "JSON",
        "Markdown",
    ]
    codi_instance.update_supported_languages(updated_languages)
    codi_instance.execute_generated_code(generated_code)
    root.mainloop()
    try:
        print("Mobile version created successfully.")
        MobileCodiApp().run()
    except Exception as e:
        error_message = f"Error creating mobile version: {str(e)}"
        print(error_message)
