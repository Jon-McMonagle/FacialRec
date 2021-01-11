
'''
DESCRIPTION
===========
Facial detection script using openCV Cascades.

'''

import cv2
import sys


# Get user supplied values

imagePath = "jon.jpeg"
cascPath = "haarcascade_frontalface_default.xml"

# create the haar cascade
faceCascade = cv2.CascadeClassifier(cascPath)

# Read the image
image = cv2.imread(imagePath)
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

# Detect faces in the image
faces = faceCascade.detectMultiScale(
    gray,
    scaleFactor=1.1,
    minNeighbors=5,
    minSize=(30,50),
    #flags = cv2.CV_HAAR_SCALE_IMAGE
)

print("Found {0} faces!".format(len(faces)))

# Drawing rectangle around faces
for (x, y, w, h) in faces:
    cv2.rectangle(image, (x,y), (x+w, y+h), (0, 255, 0), 2)

cv2.imshow("Faces found:", image)
cv2.waitKey(0)
