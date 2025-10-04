import tkinter.messagebox
from tkinter import colorchooser
import customtkinter as custk
import mysql.connector
from PIL import Image
import speech_recognition as sr
import threading
import random
from datetime import datetime, timedelta
import pygame
import pyttsx3
pygame.init()

class Flashcards:
    def __init__(self, scroll, user_id, master, background_colour, button_colour, border_colour):
        self.scroll = scroll
        self.user_id = user_id
        self.original_id = user_id
        self.master = master
        self.background_colour = background_colour
        self.button_colour = button_colour
        self.border_colour = border_colour
        self.audio = custk.CTkImage(light_image=Image.open('audio.png'), size=(25, 25))
        self.x_img = custk.CTkImage(light_image=Image.open('x.png'), size=(30, 30))
        self.l_arrow = custk.CTkImage(light_image=Image.open('l_arrorw.png'), size=(40, 40))
        self.edit_icon = custk.CTkImage(light_image=Image.open('edit.png'), size=(30, 30))
        self.plus_icon = custk.CTkImage(light_image=Image.open('plus.png'), size=(30, 30))
        self.tick_icon = custk.CTkImage(light_image=Image.open('tick.png'), size=(25, 25))
        self.settings_icon = custk.CTkImage(light_image=Image.open('settings.png'), size=(25, 25))
        self.mic = custk.CTkImage(light_image=Image.open('mic.png'), size=(25,25))
        self.muted = custk.CTkImage(light_image=Image.open('muted.png'), size=(20,25))
        self.stop_event = threading.Event()
        self.stop_event.set()
        self.difficulty = 0.3
        self.repetition = False
        try:
            self.mydb = mysql.connector.connect(
                host="localhost",
                user="root",
                passwd="Bigvideostudious1",
                database="mydb"
            )
            # mycursor = mydb.cursor(buffered=True , dictionary=True) # returns a dictionary with table name and contents rather than tuple
            self.mycursor = self.mydb.cursor(buffered=True)
        except:
            tkinter.messagebox.showerror(message="Error, connection is not established try again later")
            return


    def stt(self, screen):  # subroutine for speech to text
        rec = sr.Recognizer()

        while not self.stop_event.is_set():
            print(self.stop_event.is_set())
            try:
                with sr.Microphone() as mic:
                    rec.adjust_for_ambient_noise(mic, duration=0.2)
                    audio = rec.listen(mic)
                    text = rec.recognize_google(audio)
                    text = text.lower()
                    if not self.stop_event.is_set():
                        print("Did you say ", text)
                        screen.clipboard_clear()
                        screen.clipboard_append(text)

            except sr.RequestError as e:
                print("Could not request results; {0}".format(e))
            except sr.UnknownValueError:
                print("unknown error occurred")

    def button_handler(self, stt_button, screen):  # subroutine for handling the child thread created when the stt_button is clicked
        if not self.stop_event.is_set():  # if when the button is clicked the stop event if False
            self.stop_event.set()  # set stop event to True
            stt_button.configure(text="Stop Speaking")
            stt_button.configure(image=self.muted)
        else:
            self.stop_event.clear()  # set stop event to false
            stt_button.configure(text="Start Speaking")
            stt_button.configure(image=self.mic)
            # start the speech recognition thread
            speech_thread = threading.Thread(target=self.stt, args=(screen,))
            speech_thread.start()

    def view_decks(self):
        # method that will display all the users decks, settings button, add deck button and a search for other users
        self.mycursor.execute('SELECT deck_name FROM decks WHERE user_id = %s', (self.user_id,))
        decks = self.mycursor.fetchall()
        # when the enter key is pressed will search for users with similar name if empty will show original user
        select_user = custk.CTkEntry(self.scroll, placeholder_text="Select a user", width=200, height=50,
                                     font=("Helevetica", 18))
        select_user.pack(pady=10)
        select_user.bind("<Return>", lambda event: self.display_users(select_user))
        for deck_name in decks:
            self.mycursor.execute('SELECT deck_id FROM decks WHERE deck_name =%s', (deck_name))
            ids = self.mycursor.fetchone()
            custk.CTkButton(self.scroll, text=deck_name[0], command=lambda ids=ids: self.show_flashcards(ids),
                            fg_color=self.button_colour, height=75, width=250,
                            font=("Helevetica", 18), border_color=self.border_colour,
                            border_width=5, corner_radius=15).pack(pady=10)
            print(deck_name[0])
            print(ids[0])
        settings = custk.CTkButton(self.scroll, text="Settings", fg_color=self.button_colour,
                                   height=75, width=250, font=("Helevetica", 18), border_color=self.border_colour,
                                   border_width=5, corner_radius=15, image=self.settings_icon,
                                   command=self.change_settings)
        settings.place(relx=0.85, rely=0.005)
        # note if method called with brackets,self.add_decks() will call the method without clicking the button
        if self.user_id == self.original_id:
            new_dk = custk.CTkButton(self.scroll, text="New Deck", command=self.add_decks,
                                     fg_color=self.button_colour, height=75, width=250,
                                     font=("Helevetica", 18), border_color=self.border_colour,
                                     border_width=5, corner_radius=15, image=self.plus_icon)
            new_dk.place(relx=0.02, rely=0.005)

    def superMemo2(self, question, ids, right_wrong):
        # this is the method for determining when the flashcard should next be reviewed in spaced learning and how difficult the user finds a particular card
        # takes card_detais (question), the id for a particular flashcard and whether the user answered correctly (right_wrong) as input
            reviewDiff = question[self.question_id][5]

            if right_wrong == "right":
                performanceRating = 0.6
            else:
                performanceRating = 0.3
            overdue = self.calculate_overdue(question[self.question_id])
            self.difficulty += overdue *(1/17)*(8-9*performanceRating)
            diffcultyWeight = 3-(1.7*self.difficulty)


            if right_wrong == "right":
                if reviewDiff == None:
                    reviewDiff = 1
                else:
                    reviewDiff *= 1+(diffcultyWeight - 1) * overdue *random.uniform(0.95, 1.05)
            else:
                if reviewDiff == None:
                    reviewDiff = 0.00347222 # 5 minutes in days
                else:
                    reviewDiff *= 1/(1+3*self.difficulty)
            time = datetime.now()
            if reviewDiff <0.00347222:
                reviewDiff=0.00347222 # ensure the minimum difference between reviews is 5 minutes
            self.mycursor.execute("""UPDATE flashcards SET difficulty=%s, daysBetweenReviews=%s, dateLastReviewed=%s
                                  WHERE flashcard_id = %s""", (self.difficulty, reviewDiff, time, ids))
            self.mydb.commit()

    def calculate_overdue(self, question):
        # calculates how overdue a card is, takes card_details as an input(question) and returns the overdue_value
        # question is card_details
        current_datetime = datetime.now()
        if question[6] != None:
            #print(question[6])
            overdue_value = min(2, (current_datetime - question[6]).days / question[5])
        else:
            overdue_value = 1
        return overdue_value


    def show_flashcards(self, dk_id):
        # method that will display page which will contain the flashcards, options to edit them, quiz mode and spaced repetition
        self.question_id = 0
        self.answer_id = 0
        score = 0
        print("eeee")
        print(dk_id)
        self.mycursor.execute("""SELECT question, answer, score, flashcard_id, difficulty,
                                      daysBetweenReviews, dateLastReviewed FROM flashcards where deck_id=%s ORDER BY score""",
                              (dk_id[0],))
        card_details = self.mycursor.fetchall()
        print(card_details)
        card_scr = custk.CTkToplevel(self.master, fg_color=self.background_colour)
        card_scr.title("Flashcards")
        card_scr.state('zoomed')
        card_scr.columnconfigure((0, 1, 2, 3, 4), weight=1, uniform='a')
        card_scr.rowconfigure((0, 1, 2, 3, 4), weight=1, uniform='a')
        self.master.withdraw()
        print(card_details)

        if self.repetition == True:
            for i in range(len(card_details) - 1, -1, -1):
            # error caused when item is removed as index is updated so will go through items in reverse order so index is unaffected
                print(card_details[i])
                if card_details[i][6] != None:
                    delta = timedelta(days=card_details[i][5])
                    if card_details[i][6] + delta > datetime.now():
                            card_details.pop(i)
            card_details=sorted(card_details, key=self.calculate_overdue, reverse=True)
            if len(card_details) > 20:
                card_details = card_details[:20]

        if card_details != []:
            # print(card_details[ques_id])
            card = custk.CTkButton(card_scr, text=card_details[self.question_id][self.answer_id],
                                   command=lambda: self.next_card(card, card_details, card_scr),
                                   text_color_disabled='#DCE4EE', font=("Helevetica", 18),
                                   fg_color=self.button_colour, border_color=self.border_colour,
                                   border_width=5, corner_radius=15)
            card.grid(row=2, column=1, sticky='NESW', rowspan=2, columnspan=3, padx=100)
            card._text_label.configure(wraplength=800)
            # _text_label is a protected member of a class, this may cause problems in later version
            card.bind("<Button-3>", lambda event: self.previous_card(event, card, card_details))

        listen_button = custk.CTkButton(card_scr, text="listen", font=("Helevetica", 18), fg_color=self.button_colour, border_color=self.border_colour,
                                        border_width=5, corner_radius=15, image=self.audio, command=lambda: self.listen(card_details))
        listen_button.grid(row=4, column=0, sticky='NESW', pady=50, padx=50)
        if self.user_id == self.original_id:
            add_card = custk.CTkButton(card_scr, text="New Card", command=lambda: self.add_flashcards(dk_id, card_scr),
                                       font=("Helevetica", 18), fg_color=self.button_colour,border_color=self.border_colour,
                                       border_width=5, corner_radius=15, image=self.plus_icon)
            add_card.grid(row=0, column=1, sticky='NESW', pady=50, padx=50)
            edit_card = custk.CTkButton(card_scr, text="Edit Cards", font=("Helevetica", 18),
                                        command=lambda: self.flashcard_changes(card_scr, dk_id), fg_color=self.button_colour,
                                        border_color=self.border_colour,border_width=5, corner_radius=15, image=self.edit_icon)
            edit_card.grid(row=0, column=2, sticky='NESW', pady=50, padx=50)
            delete_deck = custk.CTkButton(card_scr, text="Delete Deck", font=("Helevetica", 18),
                                          command=lambda: self.delete_deck(dk_id[0], card_scr), fg_color=self.button_colour,
                                          border_color=self.border_colour,border_width=5, corner_radius=15, image=self.x_img)
            delete_deck.grid(row=0, column=3, sticky='NESW', pady=50, padx=50)
        if self.repetition == False:
            return_todecks = custk.CTkButton(card_scr, text="Go Back", font=("Helevetica", 18),
                                             command=lambda: [card_scr.destroy(), self.master.deiconify()], fg_color=self.button_colour,
                                             border_color=self.border_colour,border_width=5, corner_radius=15, image=self.l_arrow)
            return_todecks.grid(row=4, column=4, sticky='NESW', pady=50, padx=50)
            if self.user_id == self.original_id:
                spaced_learning = custk.CTkButton(card_scr, text="Spaced Learning", font=("Helevetica", 18),
                                                  command=lambda: [setattr(self, "repetition", not self.repetition), self.refresh(card_scr,dk_id)],
                                                  fg_color=self.button_colour,border_color=self.border_colour,border_width=5, corner_radius=15)
                spaced_learning.grid(row=0, column=4, sticky='NESW', pady=50, padx=50)
        else:
            return_todecks = custk.CTkButton(card_scr, text="Go Back", font=("Helevetica", 18),
                                             command=lambda: [setattr(self, "repetition", not self.repetition),self.refresh(card_scr, dk_id)],
                                             fg_color=self.button_colour, border_color=self.border_colour,border_width=5, corner_radius=15,
                                             image=self.l_arrow)
            return_todecks.grid(row=4, column=4, sticky='NESW', pady=50, padx=50)
        if len(card_details) >=12:
            quiz = custk.CTkButton(card_scr, text="Quiz", font=("Helevetica", 18),fg_color=self.button_colour, border_color=self.border_colour,
                                   border_width=5, corner_radius=15, command = lambda: self.play_quiz(card_details, card_scr, dk_id, score))
            quiz.grid(row=0, column=0, sticky="NESW", pady=50, padx=50)

    def refresh(self, window, additional_info):
        # method for refreshing the contents of a page
        for child in window.winfo_children():
            child.destroy()
        if window == self.scroll:
            self.view_decks()
        elif additional_info != "":
            window.destroy()
            self.show_flashcards(additional_info)

    def refresh_quiz(self, quiz_wn, c_details, card_wn, dk_id, score, highscore):
        # method for refreshing the contents of the quiz window
        quiz_wn.destroy()
        if len(c_details) >4:
            self.play_quiz(c_details, card_wn, dk_id, score)
        else:
            # creates a new window that displays score and high score, commits new score to file if larger than high score
            score_wn = custk.CTkToplevel(card_wn, fg_color=self.background_colour)
            score_wn.geometry("500x600")
            score_wn.grab_set()
            score_wn.title("Finished")
            high_label = custk.CTkLabel(score_wn, text="High score:" + str(highscore), font=("Helevetica", 18))
            high_label.pack(pady=10)
            score_label = custk.CTkLabel(score_wn, text="Score:" + str(score), font=("Helevetica", 18))
            score_label.pack(pady=10)
            if score > int(highscore):
                congrats_label = custk.CTkLabel(score_wn, text="Congrats you got a new high score", font=("Helevetica", 18))
                congrats_label.pack(pady=10)
                with open("customisation", "r") as file:
                    file_data = file.readlines()
                    file_data[-1] = str(score)
                with open("customisation", "w") as file:
                    file.writelines(file_data)
            elif score == int(highscore):
                close_label = custk.CTkLabel(score_wn, text="So close", font=("Helevetica", 18))
                close_label.pack(pady=10)
            else:
                less_label = custk.CTkLabel(score_wn, text="Better luck next time", font=("Helevetica", 18))
                less_label.pack(pady=10)
            self.show_flashcards(dk_id)

    def add_decks(self):
        # method for displaying the add deck page
        dk_screen = custk.CTkToplevel(self.scroll, fg_color=self.background_colour)
        dk_screen.title("Add Deck")
        dk_screen.grab_set()
        dk_screen.geometry("250x200")
        dk_name_en = custk.CTkEntry(dk_screen, placeholder_text="Name of the deck")
        dk_name_en.pack(pady=10)
        confirm_but = custk.CTkButton(dk_screen, command=lambda: self.create_dk(self.user_id, dk_name_en), fg_color=self.button_colour,
                                      border_color=self.border_colour,border_width=5, corner_radius=15, text = "Confirm",
                                      image=self.tick_icon)
        confirm_but.pack()
        stt_button = custk.CTkButton(dk_screen, text="Speech to text", image=self.mic,
                                     command=lambda: self.button_handler(stt_button, dk_screen), fg_color=self.button_colour,
                                     border_color=self.border_colour,border_width=5, corner_radius=15)
        stt_button.pack(pady=10)

    def create_dk(self, user_id, name_entry):
        # method for inserting a deck into the database
        ins_name = name_entry.get()
        if ins_name == "":
            tkinter.messagebox.showerror(message="Deck name can't be blank")
        elif len(ins_name)>100:
            tkinter.messagebox.showerror(message="Deck name is too long")
        else:
            self.mycursor.execute("INSERT INTO decks(deck_name, user_id) VALUES(%s,%s)", (ins_name, user_id))
            self.mydb.commit()
            self.refresh(self.scroll, "")


    def display_users(self, user):
        # method for creating a page that displays all user with a similar name to that entered by user

        username = user.get()
        if username == "":
            self.user_id = self.original_id
            self.master.deiconify()
            for child in self.scroll.winfo_children():
                child.destroy()
            self.view_decks()
        else:
            self.mycursor.execute("SELECT username, user_id FROM users WHERE username LIKE %s",
                                  ('%' + username + '%',))
            user_list = self.mycursor.fetchall()
            if user_list == []:
                tkinter.messagebox.showerror(message="user doesn't exist")
                print(user_list)
            else:
                self.master.withdraw()
                user_wn = custk.CTkToplevel(self.master, fg_color=self.background_colour)
                user_wn.title('Users')
                user_wn.geometry("750x600")
                user_wn.state('zoomed')
                for person in user_list:
                    custk.CTkButton(user_wn, text=person[0],
                                    command=lambda person=person: [self.change_user(person[1]), user_wn.destroy()],
                                    fg_color=self.button_colour,border_color=self.border_colour,
                                    border_width=5, corner_radius=15, height=75, width=250, font=("Helevetica", 18)).pack(pady=10)

    def change_user(self, new_id):
        self.user_id = new_id
        self.master.deiconify()
        self.refresh(self.scroll, "")

    def previous_card(self, event, card, c_details):
        # when the right click button is pressed this method will display the previous flashcard
        if self.answer_id == 0 or self.question_id == len(c_details) - 1:
            self.answer_id = 0
            card.configure(state="enabled")
            if self.question_id != 0:
                self.question_id -= 1
                card.configure(text=c_details[self.question_id][self.answer_id])
            else:
                blockSound = pygame.mixer.Sound("block.wav")
                blockSound.play()

    def next_card(self, card, c_details, window):
        # method for displaying the next card and calculating the score/when the card should next be shown
        # window = card_scr

        score = c_details[self.question_id][2]
        ids = c_details[self.question_id][3]

        def change_score(right_wrong, score, ids, gd_button, bd_button, card, c_details):
            if self.repetition == True:
                self.superMemo2(c_details, ids, right_wrong)
            else:
                if right_wrong == "right":
                    score *= 2
                else:
                    score /= 2

                self.mycursor.execute("UPDATE flashcards SET score = %s WHERE flashcard_id = %s", ((score), (ids)))
                self.mydb.commit()
            gd_button.destroy()
            bd_button.destroy()
            if self.question_id != len(c_details) - 1:
                card.configure(state="normal")
                self.answer_id = 0
                self.question_id += 1
                card.configure(text=c_details[self.question_id][self.answer_id])
        if self.question_id == len(c_details) - 1 and self.answer_id == 1:
                blockSound =pygame.mixer.Sound("block.wav")
                blockSound.play()


        if self.answer_id == 0:
            good_button = custk.CTkButton(window, text="Good", command=lambda: change_score("right", score, ids, good_button, bad_button, card, c_details),
                                          font=("Helevetica", 18),border_color=self.border_colour, border_width=5, corner_radius=15,
                                          fg_color="#008000")
            good_button.grid(row=4, column=1, sticky='NESW', pady=50, padx=50)
            bad_button = custk.CTkButton(window, text="Bad", command=lambda: change_score("wrong", score, ids, good_button, bad_button, card, c_details),
                                         font=("Helevetica", 18),border_color=self.border_colour, border_width=5, corner_radius=15,
                                         fg_color="#ff0000")
            bad_button.grid(row=4, column=3, sticky='NESW', pady=50, padx=50)
        if self.answer_id <1:
            self.answer_id += 1
        card.configure(text=c_details[self.question_id][self.answer_id])
        if self.question_id != len(c_details) -1:
            card.configure(state='disabled')


    def add_flashcards(self, dk_id, window):
        # method for displaying the add flashcards page
        # window = card_scr
        flash_screen = custk.CTkToplevel(window, fg_color=self.background_colour)
        flash_screen.grab_set()
        flash_screen.geometry("500x600")
        flash_screen.title('Add Flashcards')
        question_en = custk.CTkEntry(flash_screen, placeholder_text="Question", height=50, width=250,
                                     font=("Helevetica", 18))
        question_en.pack(pady=10)
        answer_en = custk.CTkEntry(flash_screen, placeholder_text="Answer",height=50, width=250,
                                     font=("Helevetica", 18))
        answer_en.pack(pady=10)
        stt_button = custk.CTkButton(flash_screen, text="Speech to text", image=self.mic,
                                     command=lambda: self.button_handler(stt_button, flash_screen),fg_color=self.button_colour,
                                     border_color=self.border_colour, border_width=5, corner_radius=15, height=50,
                                     width=250, font=("Helevetica", 18))
        stt_button.pack(pady=10)
        flash_confirm = custk.CTkButton(flash_screen, text="Confirm",
                                        command=lambda: self.create_flash(question_en, answer_en, dk_id, window),
                                        fg_color=self.button_colour, border_color=self.border_colour, border_width=5, corner_radius=15,
                                        height=50, width=250, font=("Helevetica", 18), image=self.tick_icon)
        flash_confirm.pack()

    def create_flash(self, question_entry, answer_entry, deck_id, window):
        # method for adding a new flashcard to the flashcards table
        # window = card_scr

        question = question_entry.get()
        answer = answer_entry.get()
        if question != "" and answer != "":
            if len(question) > 1500:
                tkinter.messagebox.showerror(message="Question is too long")
            elif len(answer) > 1500:
                tkinter.messagebox.showerror(message="Answer is too long")
            else:
                print(len(question))
                print("t")
                self.mycursor.execute("INSERT INTO flashcards(question, answer, deck_id) VALUES(%s, %s, %s)",
                                      (question, answer, deck_id[0]))
                self.mydb.commit()
                self.refresh(window, deck_id)
        else:
            tkinter.messagebox.showerror(message="All fields required")

    def flashcard_changes(self, window, dk_id):
        # method that creates a window which displays all questions and answers in a deck as buttons, takes the deck id as input and card_scr window

        display_wn = custk.CTkToplevel(window, fg_color=self.background_colour)
        display_wn.geometry("1000x600")
        display_wn.state('zoomed')
        display_wn.title('Flashcards')
        window.withdraw()
        flash_scroll = custk.CTkCanvas(display_wn, scrollregion=(0, 0, 1000, 5000), bg=self.background_colour)
        flash_scroll.pack(expand=True, fill="both")
        scrollbar = custk.CTkScrollbar(display_wn, orientation='vertical', command=flash_scroll.yview)
        flash_scroll.configure(yscrollcommand=scrollbar.set)
        flash_scroll.bind('<MouseWheel>', lambda event: flash_scroll.yview_scroll(-int(event.delta / 60), "units"))
        scrollbar.place(relx=1, rely=0, relheight=1, anchor='ne')
        return_button = custk.CTkButton(flash_scroll, text="Go Back", command=lambda: self.refresh(window, dk_id),fg_color=self.button_colour,
                                        border_color=self.border_colour, border_width=5, corner_radius=15,
                                        width=250, height=50, font=("Helevetica", 18),image=self.l_arrow)
        return_button.pack()

        self.mycursor.execute('SELECT question, answer, flashcard_id FROM flashcards WHERE deck_id = %s', (dk_id[0],))
        display = self.mycursor.fetchall()
        for card in display:
            question = card[0]
            answer = card[1]
            flash_id = card[2]
            custk.CTkButton(flash_scroll, text="Q: " + question + " " + "A: " + answer,
                            command=lambda question=question, answer=answer, flash_id=flash_id: flashcard_edit(flash_scroll, question, answer, flash_id, window,
                                                           dk_id, display_wn),
                            fg_color=self.button_colour,border_color=self.border_colour, border_width=5, corner_radius=15,
                            width=300, height=50, font=("Helevetica", 18)).pack(pady=10)

        def flashcard_edit(window, question, answer, flash_id, master, dk_id, display_wn):
            # method that creates a new window with entry boxes to allow the user to alter a card
            # window= flash_scroll, master = card_scr

            edit_wn = custk.CTkToplevel(window, fg_color=self.background_colour)
            edit_wn.grab_set()
            edit_wn.title('Edit Flashcards')
            edit_wn.geometry("500x600")
            ques_edit = custk.CTkEntry(edit_wn, placeholder_text="Question", width=250, height=50, font=("Helevetica", 18))
            ques_edit.pack(pady=10)
            ques_edit.insert(0, question)
            answer_edit = custk.CTkEntry(edit_wn, placeholder_text="Question", width=250, height=50, font=("Helevetica", 18))
            answer_edit.pack(pady=10)
            answer_edit.insert(0, answer)
            stt_button = custk.CTkButton(edit_wn, text="Speech to text", image=self.mic,
                                         command=lambda: self.button_handler(stt_button, edit_wn),fg_color=self.button_colour,
                                         border_color=self.border_colour, border_width=5, corner_radius=15,
                                         width=250, height=50, font=("Helevetica", 18))
            stt_button.pack(pady=10)
            confirm_button = custk.CTkButton(edit_wn, text="Confirm Edits",
                                             command=lambda: self.updates(ques_edit, answer_edit, flash_id, display_wn,master, dk_id),
                                             fg_color=self.button_colour,border_color=self.border_colour, border_width=5, corner_radius=15,
                                             width=250, height=50, font=("Helevetica", 18), image=self.tick_icon)
            confirm_button.pack(pady=10)
            delete_button = custk.CTkButton(edit_wn, text="Delete",
                                            command=lambda: self.delete_flash(flash_id, display_wn, master, dk_id),
                                            fg_color=self.button_colour, border_color=self.border_colour, border_width=5, corner_radius=15,
                                            width=250, height=50, font=("Helevetica", 18), image=self.x_img)
            delete_button.pack(pady=10)

    def updates(self, question_entry, answer_entry, flash_id, window, master, dk_id):
        # method to commit the updates to the flashcard to the database
        # window = display_wn, master = card_scr
        print(flash_id)
        print(question_entry.get())
        print(answer_entry.get())
        if question_entry.get() != "" and answer_entry.get() != "":
            if len(question_entry.get())>1500:
                tkinter.messagebox.showerror(message="Question is too long")
            elif len(answer_entry.get())>1500:
                tkinter.messagebox.showerror(message="Answer is too long")
            else:
                print(len(question_entry.get()))
                self.mycursor.execute("UPDATE flashcards SET question = %s, answer=%s WHERE flashcard_id=%s",
                                      (question_entry.get(), answer_entry.get(), flash_id))
                self.mydb.commit()
                window.destroy()
                self.flashcard_changes(master, dk_id)
        else:
            tkinter.messagebox.showerror(message="Question and Answer cannot be left blank")

    def delete_deck(self, id, window):
        # window = card_scr
        if tkinter.messagebox.askokcancel(title="delete deck",message="Are you sure you want to delete this deck"):
            self.mycursor.execute("DELETE FROM flashcards WHERE deck_id = %s", (id,))
            self.mydb.commit()
            self.mycursor.execute("DELETE FROM DECKS WHERE deck_id = %s", (id,))
            self.mydb.commit()
            window.destroy()
            self.master.deiconify()
            for child in self.scroll.winfo_children():
                child.destroy()
            self.view_decks()

    def delete_flash(self, id, window, master, deck_id):
        # window = display_wn, master = card_scr
        if tkinter.messagebox.askokcancel(title="delete flashcard", message="Are you sure you want to delete this flashcard"):
            self.mycursor.execute("DELETE FROM flashcards WHERE flashcard_id =%s", (id,))
            self.mydb.commit()
            window.destroy()
            self.flashcard_changes(master, deck_id)

    def listen(self, card_details):
        engine = pyttsx3.init()
        engine.say(card_details[self.question_id][self.answer_id])
        engine.runAndWait()

    def change_settings(self):
        # method to display window that allows user to select what item they want to change colour
        settings_wn = custk.CTkToplevel(self.master, fg_color=self.background_colour)
        settings_wn.title("Settings")
        settings_wn.geometry("750x600")
        settings_wn.grab_set()

        def change_colour(change):
            # method for selecting colours to use and committing changes to the file
            def change_settings(settings, background_button, button_button, border_button, return_to_original, exit_button):
                # method change colour of buttons and window on settings window
                settings.configure(fg_color=self.background_colour)
                background_button.configure(fg_color=self.button_colour)
                button_button.configure(fg_color=self.button_colour)
                border_button.configure(fg_color=self.button_colour)
                return_to_original.configure(fg_color=self.button_colour)
                exit_button.configure(fg_color=self.button_colour)
                background_button.configure(border_color=self.border_colour)
                button_button.configure(border_color=self.border_colour)
                border_button.configure(border_color=self.border_colour)
                return_to_original.configure(border_color=self.border_colour)
                exit_button.configure(border_color=self.border_colour)


            if change != "original":
                color = colorchooser.askcolor()[1]
            if change == "background":
                if color != None:
                    self.background_colour = color
                    self.scroll.configure(bg=self.background_colour)
                    self.master.configure(fg_color=self.background_colour)
                    self.refresh(self.scroll, "")
                    change_settings(settings_wn, background_button, button_button, border_button, return_to_original,exit_button)
            elif change == "button":
                if color != None:
                    self.button_colour = color
                    change_settings(settings_wn, background_button, button_button, border_button, return_to_original, exit_button)
                    self.refresh(self.scroll, "")
            elif change == "border":
                if color != None:
                    self.border_colour = color
                    change_settings(settings_wn, background_button, button_button, border_button, return_to_original,exit_button)
                    self.refresh(self.scroll, "")
            else:
                file = open("customisation", "r")
                prefList = file.readlines()
                print(prefList)
                self.background_colour = prefList[3].strip()
                self.button_colour = prefList[4].strip()
                self.border_colour = prefList[5].strip()
                self.scroll.configure(bg=self.background_colour)
                self.master.configure(fg_color=self.background_colour)
                change_settings(settings_wn, background_button, button_button, border_button, return_to_original,exit_button)
                self.refresh(self.scroll, "")
            with open('customisation', "r") as file:
                existing_preferences = file.readlines()
            new_preferences= [self.background_colour, self.button_colour, self.border_colour]
            remaining_preferences = existing_preferences[3:]
            with open('customisation', "w") as file:
                file.writelines("\n".join(new_preferences) + "\n" + "".join(remaining_preferences))



        background_button = custk.CTkButton(settings_wn, text="change background colour", command=lambda:change_colour("background"),
                                            fg_color=self.button_colour, width=250, height=50, font=("Helevetica", 18),
                                            border_color=self.border_colour, border_width=5, corner_radius=15
                                            )
        background_button.pack(pady=10)
        button_button = custk.CTkButton(settings_wn, text="change button colour", command=lambda:change_colour("button"),
                                        fg_color=self.button_colour, width=250, height=50, font=("Helevetica", 18),
                                        border_color=self.border_colour, border_width=5, corner_radius=15)
        button_button.pack(pady=10)
        border_button = custk.CTkButton(settings_wn, text="change border colour", command=lambda:change_colour("border"),
                                        fg_color=self.button_colour, width=250, height=50, font=("Helevetica", 18),
                                        border_color=self.border_colour, border_width=5, corner_radius=15
                                        )
        border_button.pack(pady=10)


        return_to_original = custk.CTkButton(settings_wn, text="return to original", command=lambda:change_colour("original"),
                                        fg_color=self.button_colour, width=250, height=50, font=("Helevetica", 18),
                                        border_color=self.border_colour, border_width=5, corner_radius=15)
        return_to_original.pack(pady=10)
        exit_button = custk.CTkButton(settings_wn, text="Go Back", command=lambda:(settings_wn.destroy(),self.refresh(self.scroll, "")),
                                        fg_color=self.button_colour, width=250, height=50, font=("Helevetica", 18),
                                        border_color=self.border_colour, border_width=5, corner_radius=15,
                                        image=self.l_arrow)
        exit_button.pack()

    def play_quiz(self, card_details, window, dk_id, score):
        # method for displaying the possible answer choices and the question
        # window is card_scr

        file = open("customisation", "r")
        highscore = file.readlines()[6].strip()
        file.close()
        def check_answers(answers, answer_id, dk_id, score, label):
            # subroutine for checking if the user clicked the correct button and updates the score
            if answers == card_details[random_cards[0]][1]:
                answer_list[answer_id].configure(fg_color="#008000", hover_color="#008000")
                correctSound = pygame.mixer.Sound("correct.mp3")
                correctSound.play()
                score += 100
                label.configure(text="score:"+str(score))
                card_details.remove((card_details[random_cards[0]]))
            else:
                answer_list[answer_id].configure(fg_color="#ff0000", hover_color="#ff0000")
                wrongSound = pygame.mixer.Sound("wrong.mp3")
                wrongSound.play()
                if score >=300:
                    score -= 300
                else:
                    score = 0
                label.configure(text="score:" + str(score))
            for j in range(len(answer_list)):
                answer_list[j].configure(state='disabled')
            if quiz_scr.winfo_exists():
                print(quiz_scr.winfo_exists())
                print("e")
                window.after(1000, lambda: self.refresh_quiz(quiz_scr, card_details, window, dk_id, score, highscore))
            #self.refresh(quiz_scr, card_details)

        window.withdraw()
        quiz_scr = custk.CTkToplevel(window, fg_color=self.background_colour)
        quiz_scr.state('zoomed')
        quiz_scr.title("Quiz")
        quiz_scr.columnconfigure((0, 1, 2, 3), weight=1, uniform='a')
        quiz_scr.rowconfigure((0, 1, 2), weight=1, uniform='a')
        random_cards=random.sample(range(0, (len(card_details))),4)
        question_card = custk.CTkButton(quiz_scr, text=card_details[random_cards[0]][0],
                            fg_color=self.button_colour, font=("Helevetica", 18),
                            border_color=self.border_colour, border_width=5, corner_radius=15, text_color_disabled='#DCE4EE')
        question_card.grid(row=0, column=1, columnspan=2, sticky='NESW', padx=50, pady=50)
        question_card._text_label.configure(wraplength=1100)
        question_card.configure(state='disabled')
        # button is disabled to add aesthetic as border can't be added for a label don't know to how to add wraplength with a label
        score_label = custk.CTkLabel(quiz_scr, text="score:"+ str(score), font=("Helevetica", 18))
        score_label.grid(row=0, column=3)
        highscore_label = custk.CTkLabel(quiz_scr, text="high score:" + str(highscore), font=("Helevetica", 18))
        highscore_label.grid(row=0, column=0)
        return_button = custk.CTkButton(quiz_scr, text="Go Back", command=lambda:[quiz_scr.destroy(), window.deiconify()], font=("Helevetica", 18), image=self.l_arrow,
                                        border_width=5, corner_radius=15, border_color=self.border_colour, fg_color=self.button_colour, height=150, width=150)
        return_button.grid(row=2, column=3, sticky="ESW", pady=50, padx=100)
        random_answer = random.sample(range(0, 4), 4)
        answer_list=[]
        for i in range(4):
            answer_card = custk.CTkButton(quiz_scr, text=card_details[random_cards[random_answer[i]]][1],
                                          fg_color=self.button_colour, font=("Helevetica", 20), border_color=self.border_colour, border_width=5, corner_radius=15,
                                          command=lambda text=card_details[random_cards[random_answer[i]]][1], card_id=i: check_answers(text, card_id, dk_id, score, score_label))
            answer_card.grid(row=(1+i//2), column=(1+i%2), sticky='NESW', pady=25, padx=25)
            answer_card._text_label.configure(wraplength=400)
            answer_list.append(answer_card)