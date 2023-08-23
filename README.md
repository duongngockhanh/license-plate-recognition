# License Plate Recognition Application in Company

*Note: This project belongs to my company, not me.*

This project focuses on developing a License Plate Recognition (LPR) application using PyQt5, a Python framework for building apps. Relevant knowledge areas include OCR, Object Detection, and Object Tracking.


To start the program, please follow my instructions,

```commandline
cd app
pip install -r requirements.txt
```

Then,

```commandline
python run.py
```

After that, the **main.ui** will appear, please click on **IN**, then the **in.ui** will appear, continue by clicking **Choose File**. Afterward, the model will start running the video and conducting License Plate Recognition. Currently, a similar task has not yet been developed for **out.ui**

---

*Optional*: If you encounter error related to cython-bbox, please install Visual Studio with C++ Desktop Development and run the following command line

```commandline
pip install -e git+https://github.com/samson-wang/cython_bbox.git#egg=cython-bbox
```
