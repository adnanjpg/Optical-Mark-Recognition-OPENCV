import cv2
import numpy as np
import utils

########################################################################
webCamFeed = True
pathImage = "input/1.jpg"

heightImg = 1000
widthImg  = 1000

questions = 5
choices = 5
ans = [1,2,0,2,4]
########################################################################

if webCamFeed:
    cap = cv2.VideoCapture(0)
    #TODO
    cap.set(10,160)
else: img = cv2.imread(pathImage)

# endless loop
while True:

    if webCamFeed:
        success, img = cap.read()

    # RESIZE IMAGE
    img = cv2.resize(img, (widthImg, heightImg)) 

    imgFinal = img.copy()

    # np.zeros will create a matrix filled with zeros,
    # which means a black image.
    # this will be used to draw the images that will fail
    # (fall into exception)
    imgBlank = np.zeros((heightImg,widthImg, 3), np.uint8)

    # CONVERT IMAGE TO GRAY SCALE
    # will be put on screen and also used to apply gaussian blur
    imgGray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # ADD GAUSSIAN BLUR
    # will only used to create imgCanny
    imgBlur = cv2.GaussianBlur(imgGray, (5,5), 1) 

    # APPLY CANNY 
    imgCanny = cv2.Canny(imgBlur,10,70)

    # will be only used to display
    imgContours = img.copy() 
    
    # FIND ALL CONTOURS
    contours, hierarchy = cv2.findContours(imgCanny, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE) 

    # DRAW ALL DETECTED CONTOURS
    cv2.drawContours(imgContours, contours, -1, (0, 255, 0), 10)

    try:
 
        # COPY IMAGE FOR DISPLAY PURPOSES
        imgBigContour = img.copy() 

        # FILTER FOR RECTANGLE CONTOURS
        rectCon = utils.rectContour(contours) 

        # GET CORNER POINTS OF THE BIGGEST RECTANGLE
        biggestPoints = utils.getCornerPoints(rectCon[0]) 

        # GET CORNER POINTS OF THE SECOND BIGGEST RECTANGLE
        gradePoints = utils.getCornerPoints(rectCon[1]) 

        if biggestPoints.size != 0 and gradePoints.size != 0:

            # BIGGEST RECTANGLE WARPING
            biggestPoints = utils.reorder(biggestPoints) # REORDER FOR WARPING
            cv2.drawContours(imgBigContour, biggestPoints, -1, (0, 255, 0), 20) # DRAW THE BIGGEST CONTOUR
            pts1 = np.float32(biggestPoints) # PREPARE POINTS FOR WARP
            pts2 = np.float32([[0, 0],[widthImg, 0], [0, heightImg],[widthImg, heightImg]]) # PREPARE POINTS FOR WARP
            matrix = cv2.getPerspectiveTransform(pts1, pts2) # GET TRANSFORMATION MATRIX
            imgWarpColored = cv2.warpPerspective(img, matrix, (widthImg, heightImg)) # APPLY WARP PERSPECTIVE

            # SECOND BIGGEST RECTANGLE WARPING
            cv2.drawContours(imgBigContour, gradePoints, -1, (255, 0, 0), 20) # DRAW THE BIGGEST CONTOUR

            gradePoints = utils.reorder(gradePoints) # REORDER FOR WARPING
            ptsG1 = np.float32(gradePoints)  # PREPARE POINTS FOR WARP
            ptsG2 = np.float32([[0, 0], [325, 0], [0, 150], [325, 150]])  # PREPARE POINTS FOR WARP
            matrixG = cv2.getPerspectiveTransform(ptsG1, ptsG2)# GET TRANSFORMATION MATRIX
            imgGradeDisplay = cv2.warpPerspective(img, matrixG, (325, 150)) # APPLY WARP PERSPECTIVE

            # APPLY THRESHOLD
            imgWarpGray = cv2.cvtColor(imgWarpColored,cv2.COLOR_BGR2GRAY) # CONVERT TO GRAYSCALE
            imgThresh = cv2.threshold(imgWarpGray, 170, 255,cv2.THRESH_BINARY_INV )[1] # APPLY THRESHOLD AND INVERSE

            boxes = utils.splitBoxes(imgThresh) # GET INDIVIDUAL BOXES
            cv2.imshow("Split Test ", boxes[3])
            countR = 0
            countC = 0
            myPixelVal = np.zeros((questions,choices)) # TO STORE THE NON ZERO VALUES OF EACH BOX
            for image in boxes:
                #cv2.imshow(str(countR)+str(countC),image)
                totalPixels = cv2.countNonZero(image)
                myPixelVal[countR][countC]= totalPixels
                countC += 1
                if (countC==choices): countC = 0; countR += 1

            # FIND THE USER ANSWERS AND PUT THEM IN A LIST
            myIndex = []
            for x in range (0,questions):
                arr = myPixelVal[x]
                myIndexVal = np.where(arr == np.amax(arr))
                myIndex.append(myIndexVal[0][0])
            #print("USER ANSWERS",myIndex)

            # COMPARE THE VALUES TO FIND THE CORRECT ANSWERS
            grading = []
            for x in range(0,questions):
                if ans[x] == myIndex[x]:
                    grading.append(1)
                else:grading.append(0)

            score = (sum(grading)/questions)*100 # FINAL GRADE

            # DISPLAYING ANSWERS
            utils.showAnswers(imgWarpColored,myIndex,grading,ans) # DRAW DETECTED ANSWERS
            utils.drawGrid(imgWarpColored) # DRAW GRID
            imgRawDrawings = np.zeros_like(imgWarpColored) # NEW BLANK IMAGE WITH WARP IMAGE SIZE
            utils.showAnswers(imgRawDrawings, myIndex, grading, ans) # DRAW ON NEW IMAGE
            invMatrix = cv2.getPerspectiveTransform(pts2, pts1) # INVERSE TRANSFORMATION MATRIX
            imgInvWarp = cv2.warpPerspective(imgRawDrawings, invMatrix, (widthImg, heightImg)) # INV IMAGE WARP

            # DISPLAY GRADE
            imgRawGrade = np.zeros_like(imgGradeDisplay,np.uint8) # NEW BLANK IMAGE WITH GRADE AREA SIZE
            cv2.putText(imgRawGrade,str(int(score))+"%",(70,100)
                        ,cv2.FONT_HERSHEY_COMPLEX,3,(0,255,255),3) # ADD THE GRADE TO NEW IMAGE
            invMatrixG = cv2.getPerspectiveTransform(ptsG2, ptsG1) # INVERSE TRANSFORMATION MATRIX
            imgInvGradeDisplay = cv2.warpPerspective(imgRawGrade, invMatrixG, (widthImg, heightImg)) # INV IMAGE WARP

            # SHOW ANSWERS AND GRADE ON FINAL IMAGE
            imgFinal = cv2.addWeighted(imgFinal, 1, imgInvWarp, 1,0)
            imgFinal = cv2.addWeighted(imgFinal, 1, imgInvGradeDisplay, 1,0)

            # IMAGE ARRAY FOR DISPLAY
            imageArray = ([img,imgGray,imgCanny,imgContours],
                        [imgBigContour,imgThresh,imgWarpColored,imgFinal])
            # cv2.imshow("Final Result", imgFinal)
    except:
        imageArray = ([img,imgGray,imgCanny,imgContours],
                      [imgBlank, imgBlank, imgBlank, imgBlank])

    # LABELS FOR DISPLAY
    lables = [["Original","Gray","Edges","Contours"],
              ["Biggest Contour","Threshold","Warpped","Final"]]

    stackedImage = utils.stackImages(imageArray, 1, lables)
    cv2.imshow("Result", stackedImage)

    # cv2.waitKey takes a num as an input
    # the input is n. if the input is positive
    # the program will wait for n milliseconds
    # before it continues.
    # if the input is zero ofnegative, the 
    # program will wait for a key press before
    # continuing.
    #
    # pressed key
    pressedKey = (cv2.waitKey(100) & 0xFF)
    # save image when 's' key is pressed
    if pressedKey == ord('s'):
        utils.saveScannedImg(imgFinal)
    # quit when 'q' is pressed
    if pressedKey == ord('q'):
        print('qqqqqqqqq')
        break