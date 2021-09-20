from gcsa.google_calendar import GoogleCalendar
from datetime import datetime
from tkinter import *
import webbrowser

root = Tk()
root.title("Google Calendar")
root.geometry("1000x700")
calendar = GoogleCalendar('yourgmail@gmail.com')

y = 10
for event in calendar:
    y += 1
    x = 0
    s = StringVar()
    s = event.start.strftime('%A')
    if datetime.now().strftime('%A') != s:
        break
    date = event.start.strftime('  %m/%d/%y')
    time = event.start.strftime("%I:%M%p")

    print(s, date, '-->', time, event.description)
    label_frame = LabelFrame(root, text=time)

    label_frame.pack(padx=10, pady=10)
    L1 = Label(label_frame, text=s)
    L1.grid(row=y, column=x, padx=10, pady=30)
    x += 10
    L2 = Label(label_frame, text=date)
    L2.grid(row=y, column=x, padx=10, pady=30)
    x += 10
    L3 = Label(label_frame, text=time)
    L3.grid(row=y, column=x, padx=10, pady=30)
    x += 10
    L4 = Label(label_frame, text=event.description)
    L4.grid(row=y, column=x, padx=10, pady=30)
    location = str(event.location)
    print(len(location))
    new = 1


    def OpenUrl(url):
        print(url)
        webbrowser.open(url, new=new)


    if len(location) != 4:
        Btn = Button(root, text="Open Google Maps", command=lambda aurl=location: OpenUrl(aurl)())
        Btn.pack()
root.mainloop()
