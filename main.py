import login_page
from flashcards import *

app = custk.CTk()
app.title("Decks")
app.geometry("1920x1080")
app.attributes("-fullscreen", True)

file = open("customisation", "r")
prefList = file.readlines()
background_colour = prefList[0].strip()
button_colour = prefList[1].strip()
border_colour = prefList[2].strip()
file.close()
screen_width = app.winfo_screenwidth()
screen_height = app.winfo_screenheight()
#creating the scrollable frame and a scroll wheel that moves with the middle mouse scrolling
deck_scroll = custk.CTkCanvas(app, scrollregion=(0, 0, screen_width, screen_height), bg=background_colour)
deck_scroll.pack(expand=True, fill="both")
scrollbar = custk.CTkScrollbar(app, orientation = 'vertical', command = deck_scroll.yview)
deck_scroll.configure(yscrollcommand = scrollbar.set)
deck_scroll.bind('<MouseWheel>', lambda event: deck_scroll.yview_scroll(-int(event.delta / 60), "units"))
scrollbar.place(relx = 1, rely = 0, relheight = 1, anchor = 'ne')
#creating the login page
loginWindow = custk.CTkToplevel(app, fg_color=background_colour)
app.withdraw()
deck_scroll.itemconfigure(app, state='hidden')
loginWindow.title("Login Page")
loginWindow.geometry("1250x1000")
loginWindow.state('zoomed')
login_page.Log_Page(loginWindow,app,deck_scroll, background_colour, button_colour, border_colour)




app.mainloop()