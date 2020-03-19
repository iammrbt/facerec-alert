import face_recognition
import cv2
import smtplib
import ssl
import time
import os, shutil
from email.mime.text import MIMEText
from email.utils import formataddr
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

# This is a heavily modified version of PyImageSearch facerec_from_webcam_faster python script to work off of webcam
# or RTSP security cam to trigger an alert on an unknown face.

# Directory to store alert images to be sent out:
alertDir = "alert_image/"
# Change to specified directory

# List files in directories
print("Before saving image:")
print(os.listdir(alertDir))
# Filename for alert image
alertfile = 'alert.jpg'


#   1. Process each video frame at 1/4 resolution (though still display it at full resolution)
#   2. Only detect faces in every other frame of video.


# v- Add (image) to pushMail so that we can pass in the most recent image from the image intake folder

def pushMail():
    # User configuration
    sender_email = 'OmittedForAdamsAdvice'
    sender_name = 'OmittedForAdamsAdvice'
    password = 'OmittedForAdamsAdvice'

    # receiver_emails = ['@pushsafer.com']
    # receiver_names = ['push']
    receiver_emails = ['to@email.com']
    receiver_names = ['John Doh']
    # Email body
    email_body = 'Alert, unknown person has been detected!'
    attach_path = os.path.join(alertDir, alertfile)


    for receiver_email, receiver_name in zip(receiver_emails, receiver_names):
        print("Sending the email...")
        # Configurating user's info
        msg = MIMEMultipart()
        msg['To'] = formataddr((receiver_name, receiver_email))
        msg['From'] = formataddr((sender_name, sender_email))
        msg['Subject'] = 'UNKNOWN PERSON'

        msg.attach(MIMEText(email_body, 'html'))

        try:
            # Open PDF file in binary mode
            with open(attach_path, "rb") as attachment:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(attachment.read())

            # Encode file in ASCII characters to send by email
            encoders.encode_base64(part)

            # Add header as key/value pair to attachment part
            part.add_header(
                "Content-Disposition",
                f"attachment; filename= {attach_path}",
            )

            msg.attach(part)
        except Exception as e:
            print(f"Oh no! We didn't found the attachment!n{e}")
            break

        try:
            # Creating a SMTP session | use 587 with TLS, 465 SSL and 25
            server = smtplib.SMTP('smtp.gmail.com', 587)
            # Encrypts the email
            context = ssl.create_default_context()
            server.starttls(context=context)
            # We log in into our Google account
            server.login(sender_email, password)
            # Sending email from sender, to receiver with the email body
            server.sendmail(sender_email, receiver_email, msg.as_string())
            print('Email sent!')
        except Exception as e:
            print(f'Oh no! Something bad happened!n{e}')
            break
        finally:
            print('Closing the server...')
            server.quit()


# Get a reference to Security Camera or Webcam depending on use.

# For a IP camera with RTSP stream use the commented below:
# cam = "rtsp://username:password@ipaddress/?streamprofile=lowpro"
# video_capture = cv2.VideoCapture(cam)

# Webcam is (0) or (1) for usb add-ons.
video_capture = cv2.VideoCapture(1)


# Below I have the names of my family members:

#
brandon_image = face_recognition.load_image_file("brandon.jpg")
brandon_face_encoding = face_recognition.face_encodings(brandon_image)[0]

rachel_image = face_recognition.load_image_file("rachel.jpg")
rachel_face_encoding = face_recognition.face_encodings(rachel_image)[0]

alli_image = face_recognition.load_image_file("alli.jpg")
alli_face_encoding = face_recognition.face_encodings(alli_image)[0]

jayden_image = face_recognition.load_image_file("jayden.jpg")
jayden_face_encoding = face_recognition.face_encodings(jayden_image)[0]

# Create arrays of known face encodings and their names
known_face_encodings = [
    brandon_face_encoding,
    rachel_face_encoding,
    alli_face_encoding,
    jayden_face_encoding
]
known_face_names = [
    "Brandon",
    "Rachel",
    "Alli",
    "Jayden"
]

# Initialize some variables
face_locations = []
face_encodings = []
face_names = []
process_this_frame = True

while True:
    # Grab a single frame of video
    ret, frame = video_capture.read()

    # Resize frame of video to 1/4 size for faster face recognition processing
    small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)

    # Convert the image from BGR color (which OpenCV uses) to RGB color (which face_recognition uses)
    rgb_small_frame = small_frame[:, :, ::-1]

    # Only process every other frame of video to save time
    if process_this_frame:
        # Find all the faces and face encodings in the current frame of video
        face_locations = face_recognition.face_locations(rgb_small_frame)
        face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

        face_names = []
        for face_encoding in face_encodings:
            # See if the face is a match for the known face(s)
            matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
            # Lets call any currently unknown faces "blank" but you should never see that.
            name = "blank"

            # If a match was found in known_face_encodings, just use the first one.
            if True in matches:
                first_match_index = matches.index(True)
                name = known_face_names[first_match_index]
            else:
                # If it's detecting a face, but doesn't know who it is label it "Unknown". Acts as trigger for the alert
                name = "Unknown"

            face_names.append(name)
            # Trigger for the Alert is happening here
            if name == "Unknown":
                # Printing isn't necessary but helpful for tests and monitoring.
                print("Who the heck is this?!")
                # Join the alert directory with alert file name and save the frame of the video as its triggered.
                cv2.imwrite(os.path.join(alertDir , alertfile), frame)
                print("After saving image:")
                # After saving the image you should see the one "alert.jpg"
                print(os.listdir(alertDir))
                pushMail();
                time.sleep(30)
                # Now let's delete the alert file for the next run
                for filename in os.listdir(alertDir):
                    file_path = os.path.join(alertDir, alertfile)
                    try:
                        if os.path.isfile(file_path) or os.path.islink(file_path):
                            os.unlink(file_path)
                            print("Deleted file.")
                        elif os.path.isdir(file_path):
                            shutil.rmtree(file_path)
                            print("Dude I'm freaking out, I deleted a folder!")
                    except Exception as e:
                        print('Failed to delete %s. Reason %s' % (file_path, e))


    process_this_frame = not process_this_frame

    # Display the results
    for (top, right, bottom, left), name in zip(face_locations, face_names):
        # Scale back up face locations since the frame we detected in was scaled to 1/4 size
        top *= 4
        right *= 4
        bottom *= 4
        left *= 4

        # Draw a box around the face
        cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)

        # Draw a label with a name below the face
        cv2.rectangle(frame, (left, bottom - 35), (right, bottom), (0, 0, 255), cv2.FILLED)
        font = cv2.FONT_HERSHEY_DUPLEX
        cv2.putText(frame, name, (left + 6, bottom - 6), font, 1.0, (255, 255, 255), 1)

    # Display the resulting image
    cv2.namedWindow('Video', cv2.WINDOW_NORMAL)
    cv2.resizeWindow('Video', 600, 600)
    cv2.imshow('Video', frame)

    # Hit 'q' on the keyboard to quit!
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release handle to the camera
video_capture.release()
cv2.destroyAllWindows()
