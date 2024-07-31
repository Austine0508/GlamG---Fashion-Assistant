import cv2
import google.generativeai as genai
import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox
from tkinter import ttk  # for progress bar
from PIL import Image, ImageTk
import threading

# genai setup
genai.configure(api_key="Insert Your API key")
generation_config = {
    "temperature": 0.1,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}
model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    generation_config=generation_config
)

global file_path
global captured_image

# Function to change button color on hover
def on_enter1(e):
    capture_btn.config(bg='red')
def on_leave1(e):
    capture_btn.config(bg='light salmon')
def on_enter2(e):
    select_btn.config(bg='red')
def on_leave2(e):
    select_btn.config(bg='light salmon')
def on_enter3(e):
    analyze_btn.config(bg='red')
def on_leave3(e):
    analyze_btn.config(bg='light salmon')
def on_enter4(e):
    get_tips_btn.config(bg='red')
def on_leave4(e):
    get_tips_btn.config(bg='light salmon')

# Function to open a dialog box and select an image
def open_img():
    global file_path
    file_path = filedialog.askopenfilename(title="Select an image",
                                           filetypes=[("Image files", "*.jpg;*.jpeg;*.png;*.gif;*.bmp"), ("All files", "*.*")])
    if file_path:
        display_image(file_path)

# Function to open the camera and capture an image
def open_camera():
    global file_path
    cap = cv2.VideoCapture(0)
    
    def show_frame():
        ret, frame = cap.read()
        if ret:
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame_rgb)
            imgtk = ImageTk.PhotoImage(image=img)
            label.imgtk = imgtk
            label.configure(image=imgtk)
            label.after(10, show_frame)
    
    def capture_image():
        ret, frame = cap.read()
        if ret:
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame_rgb)
            imgtk = ImageTk.PhotoImage(image=img)
            image_label.config(image=imgtk)
            image_label.image = imgtk
            file_path = filedialog.asksaveasfilename(defaultextension=".jpg",
                                                     filetypes=[("JPEG files", "*.jpg"), ("PNG files", "*.png"), ("BMP files", "*.bmp"), ("All files", "*.*")])
            if file_path:
                img.save(file_path)
                print(f"Image saved to {file_path}")
                display_image(file_path)
            else:
                print("Save operation cancelled.")
        else:
            print("No image captured to save.")
        cap.release()
        cv2.destroyAllWindows()
        camera_window.destroy()
    
    camera_window = tk.Toplevel(win)
    camera_window.title("Camera")
    camera_window.geometry("640x480")
    label = tk.Label(camera_window)
    label.pack()
    btn_capture = tk.Button(camera_window, text="Capture", command=capture_image)
    btn_capture.pack()
    show_frame()
    camera_window.mainloop()

# Function to display an image in the GUI
def display_image(file_path):
    img = Image.open(file_path)
    img.thumbnail((400, 400))
    img = ImageTk.PhotoImage(img)
    image_label.config(image=img)
    image_label.image = img

# Function to show loading progress
def show_progress(parent):
    progress_win = tk.Toplevel(parent)
    progress_win.title("Progress")
    progress_win.geometry("300x100")
    progress = ttk.Progressbar(progress_win, orient="horizontal", length=200, mode="indeterminate")
    progress.pack(pady=20)
    progress.start()
    return progress_win, progress

# Function to analyze the image using Google GenAI
def analyze_image():
    if not file_path:
        messagebox.showwarning("No Image", "Please select or capture an image first.")
        return

    def upload_to_gemini(path, mime_type=None):
        try:
            file = genai.upload_file(path, mime_type=mime_type)
            return file
        except Exception as e:
            print(f"Error uploading file: {e}")
            return None

    def analyze_task():
        progress_win, progress = show_progress(win)
        files = [upload_to_gemini(file_path, mime_type="image/jpeg"),]
        
        if not files[0]:
            progress_win.destroy()
            messagebox.showerror("Upload Error", "Failed to upload image to Gemini.")
            return
        
        try:
            chat_session = model.start_chat(history=[{"role": "user", "parts": [files[-1],]}])
            response = chat_session.send_message(
                "You are a personal fashion assistant. Rate the person's fashion on a scale of 0 to 10 based on how good the shirt looks. Rate it on a scale of 0 to 10 on how well it matches him/her. Only give numbers alongside marking system with summarized reasons. Nothing more."
            )
            ratings = response.text

            response2 = chat_session.send_message("How to improve this style.")
            improvements = response2.text

            progress_win.destroy()

            temp_win = tk.Toplevel(win)
            temp_win.title("Assistant Analysis")
            temp_win.geometry("600x400")

            frm1 = tk.Frame(temp_win, bg='gold', width=600, height=200)
            frm1.pack(fill=tk.BOTH, expand=True)
            lbl1 = tk.Label(frm1, text="Ratings", font=('san-serif', '20'), bg='gold')
            lbl2 = tk.Label(frm1, text=ratings, font=('san-serif', '20'), bg='gold',wraplength=1080,justify='left')
            lbl1.pack(pady=10)
            lbl2.pack(pady=10)

            frm2 = tk.Frame(temp_win, bg='light goldenrod', width=600, height=200)
            frm2.pack(fill=tk.BOTH, expand=True)
            lbl3 = tk.Label(frm2, text="Improvements", font=('san-serif', '20'), bg='light goldenrod')
            lbl4 = tk.Label(frm2, text=improvements, font=('san-serif', '20'), bg='light goldenrod',wraplength=800,justify='left')
            lbl3.pack(pady=10)
            lbl4.pack(pady=10)
        except Exception as e:
            progress_win.destroy()
            print(f"Error during analysis: {e}")
            messagebox.showerror("Analysis Error", f"An error occurred during analysis: {e}")

    threading.Thread(target=analyze_task).start()

# Below function is to send outfit tips based on survey questions.
def survey_win():
    def submit():
        A1,A2,A3,A4,A5,A6 = a1.get(),a2.get(),a3.get(),a4.get(),a5.get(),a6.get()
        chat_session = model.start_chat(history=[{"role": "user", "parts": ["Hello"]}])
        response = chat_session.send_message(
            "Occasion: " + A1 +
            "\nTheme/Color Code: " + A2 +
            "\nGender: " + A3 +
            "\nSpecifications to note: " + A4 +
            "\nSkin Tone: " + A5 +
            "\nBody Type: " + A6 +
            "\nBased on above answers, suggest a costume for this person with reasons."
            )
        s_win.destroy()
        s_win2 = tk.Tk()
        s_win2.title("Result")
        s_win2.geometry("600x600")
        s_frm2 = tk.Frame(s_win2,bg='SkyBlue1')
        s_frm2.pack(fill=tk.BOTH,expand=True)
        s_frm_tit = tk.Label(s_frm2,text="Outfit Tips",bg='SkyBlue2',font=('san-serif','20'))
        s_output = tk.Label(s_frm2,text=response.text,bg='SkyBlue2',font=('sanserif','16'),wraplength=1400,justify='left')
        s_frm_tit.pack(pady=20)
        s_output.pack()
    s_win = tk.Tk()
    s_win.title("Survey")
    win.geometry("600x600")
    s_frame = tk.Frame(s_win,bg='SkyBlue1')
    s_frame.pack(fill=tk.BOTH,expand=True)
    sframe_title = tk.Label(s_frame,text="GET OUTFIT TIPS BASED ON FOLLOWING QUESTIONS",font=('san-serif','30'),bg='SkyBlue1')
    q1 = tk.Label(s_frame,text="1.  What occasion are you going to?",bg='SkyBlue1',font=('san-serif','20'))
    a1 = tk.Entry(s_frame,width=100,font=('san-serif','20'))
    q2 = tk.Label(s_frame,text="2.  Any particular theme/color code to follow? If yes, please specify.",bg='SkyBlue1',font=('san-serif','20'))
    a2 = tk.Entry(s_frame,width=100,font=('san-serif','20'))
    q3 = tk.Label(s_frame,text="3.  Gender you identify as.",bg='SkyBlue1',font=('san-serif','20'))
    a3 = tk.Entry(s_frame,width=100,font=('san-serif','20'))
    q4 = tk.Label(s_frame,text="4.  Any specifics to be taken into consideration?",bg='SkyBlue1',font=('san-serif','20'))
    a4 = tk.Entry(s_frame,width=100,font=('san-serif','20'))
    q5 = tk.Label(s_frame,text="5.  Your skin tone",bg='SkyBlue1',font=('san-serif','20'))
    a5 = tk.Entry(s_frame,width=100,font=('san-serif','20'))
    q6 = tk.Label(s_frame,text="6.  Your body type (chubby,skinny,muscular)",bg='SkyBlue1',font=('san-serif','20'))
    a6 = tk.Entry(s_frame,width=100,font=('san-serif','20'))
    submit_btn = tk.Button(s_frame, text="Submit", bg="DeepSkyBlue2", width=15, height=1, font=('san-serif', '25'),command=submit)
    
    sframe_title.pack(pady=25)
    q1.pack(pady=10,anchor='nw')
    a1.pack(padx=20,anchor='nw')
    q2.pack(pady=10,anchor='nw')
    a2.pack(padx=20,anchor='nw')
    q3.pack(pady=10,anchor='nw')
    a3.pack(padx=20,anchor='nw')
    q4.pack(pady=10,anchor='nw')
    a4.pack(padx=20,anchor='nw')
    q5.pack(pady=10,anchor='nw')
    a5.pack(padx=20,anchor='nw')
    q6.pack(pady=10,anchor='nw')
    a6.pack(padx=20,anchor='nw')
    submit_btn.pack(pady=20)
    
# Setup Tkinter window
win = tk.Tk()
win.title("GlamG")
win.geometry("600x600")

main_frame = tk.Frame(win, bg='tomato')
main_frame.pack(fill=tk.BOTH, expand=True)

main_frame_title = tk.Label(main_frame, text="GlamG", font=('san-serif', '30'), bg='tomato')
main_frame_title.pack(pady=25)

capture_btn = tk.Button(main_frame, text="Take A Picture", bg="light salmon", width=15, height=1, font=('san-serif', '25'), command=open_camera)
select_btn = tk.Button(main_frame, text="Select A Picture", bg="light salmon", width=15, height=1, font=('san-serif', '25'), command=open_img)
analyze_btn = tk.Button(main_frame, text="Analyze", bg="light salmon", width=15, height=1, font=('san-serif', '25'), command=analyze_image)
get_tips_btn = tk.Button(main_frame, text="Get Tips", bg="light salmon", width=15, height=1, font=('san-serif', '25'), command=survey_win)

capture_btn.bind("<Enter>", on_enter1)
capture_btn.bind("<Leave>", on_leave1)
select_btn.bind("<Enter>", on_enter2)
select_btn.bind("<Leave>", on_leave2)
analyze_btn.bind("<Enter>", on_enter3)
analyze_btn.bind("<Leave>", on_leave3)
get_tips_btn.bind("<Enter>", on_enter4)
get_tips_btn.bind("<Leave>", on_leave4)

capture_btn.pack(pady=10)
select_btn.pack(pady=10)
analyze_btn.pack(pady=10)
get_tips_btn.pack(pady=10)

image_label = tk.Label(main_frame)
image_label.pack(pady=20)

win.mainloop()
