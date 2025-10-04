import tkinter.messagebox
import customtkinter as custk
import mysql.connector
import flashcards

class Log_Page:

    def __init__(self, window,master, scroll, background_colour, button_colour, border_colour):
        self.master=master
        self.window=window
        self.scroll=scroll
        self.background_colour = background_colour
        self.button_colour = button_colour
        self.border_colour = border_colour
        self.log_frame = custk.CTkFrame(master=self.window, width=1000, height=1500, fg_color="#E6E6FA", border_width=2)
        self.log_frame.place(relx=0.5, rely=0.5, anchor="center")
        self.log_lbl = custk.CTkLabel(self.log_frame, text="Log In or Sign Up", font=("Helevetica", 100))
        self.log_lbl.grid(row=1, column=1, columnspan=2, pady=(30, 25), padx=15)
        self.user_entry = custk.CTkEntry(self.log_frame, placeholder_text="username", font=("Helevetica", 25), width=450,
                                    height=100)
        self.user_entry.grid(row=2, column=1, columnspan=2, pady=5)
        self.pass_entry = custk.CTkEntry(self.log_frame, placeholder_text="password", font=("Helevetica", 25), width=450,
                                    height=100, show='*')
        self.pass_entry.grid(row=3, column=1, columnspan=2, pady=5)
        self.email_entry = custk.CTkEntry(self.log_frame, placeholder_text="Email (only for signup)", font=("Helevetica", 25),
                                     width=450, height=100)
        self.email_entry.grid(row=4, column=1, columnspan=2, pady=5)
        self.sign_but = custk.CTkButton(self.log_frame, text="Sign Up", font=("Helevetica", 18), height=75, width=250, fg_color=self.button_colour,command=self.sign)
        self.sign_but.grid(row=5, column=1, columnspan=1, pady=5, padx=5)
        self.log_but = custk.CTkButton(self.log_frame, text="Log in", font=("Helevetica", 18), height=75, width=250, fg_color=self.button_colour,command=self.log)
        self.log_but.grid(row=5, column=2, columnspan=1, pady=5, padx=5)
        self.clr_but = custk.CTkButton(self.log_frame, text="Clear", font=("Helevetica", 18), height=75, width=250, fg_color=self.button_colour,command=self.clear)
        self.clr_but.grid(row=6, column=1, columnspan=2, pady=5)
        try:
            self.mydb = mysql.connector.connect(
                host="127.0.0.1",
                user="root",
                passwd="Bigvideostudious1",
                database="mydb"
            )
            self.mycursor = self.mydb.cursor()
        except:
            tkinter.messagebox.showerror(message="Error, connection is not established try again later")
            return
    def sign(self): # will check input is valid if it is will create a new user
        username = self.user_entry.get()
        password = self.pass_entry.get()
        email = self.email_entry.get()

        if username == "" or password == "" or email == "":
            tkinter.messagebox.showerror(message="All fields required")
        elif len(username)>20:
            tkinter.messagebox.showerror(message="username must at most 20 characters")
        elif len(password)>20:
            tkinter.messagebox.showerror(message="password must at most 20 characters")
        elif len(email)>254:
            tkinter.messagebox.showerror(message="invalid email")
        else:
            query = "SELECT * FROM users WHERE username=%s"
            self.mycursor.execute(query, (self.user_entry.get(),))
            existing = self.mycursor.fetchone()
            if existing != None:
                tkinter.messagebox.showerror(message="Username already in use")
            else:
                self.mycursor.execute("INSERT INTO users(username,pass,email) VALUES(%s,%s,%s)",
                                 (username, password, email,))
                self.mydb.commit()
                tkinter.messagebox.showinfo(message="Success")
                self.user_entry.delete(0, 'end')
                self.pass_entry.delete(0, 'end')
                self.email_entry.delete(0, 'end')

    def log(self): #will check if details entered are correct if they are will display users decks
        username = self.user_entry.get()
        password = self.pass_entry.get()
        if username == "" or password == "":
            tkinter.messagebox.showerror(message="Username and Password required.")
        else:
            query = "SELECT * FROM users WHERE username=%s AND pass=%s"
            self.mycursor.execute(query, (username, password))
            existing = self.mycursor.fetchone()
            if existing == None:
                tkinter.messagebox.showerror(message="Invalid username or password")
            else:
                self.master.deiconify()
                self.scroll.itemconfigure(self.master, state='normal')
                user_id = existing[0]
                deck_view=flashcards.Flashcards(self.scroll, user_id, self.master, self.background_colour, self.button_colour, self.border_colour)
                deck_view.view_decks()
                self.window.destroy()


    def clear(self):
        self.user_entry.delete(0, 'end')
        self.pass_entry.delete(0, 'end')
        self.email_entry.delete(0, 'end')