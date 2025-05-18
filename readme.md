> [!NOTE]
> the app work best with python 3.9 and this is a django project
> and use your own gemini ai api

# Demo video.

![[demo.mp4]]

# how to run the app

1. make the env using python

```bash
python3.9 -m  venv env
```

2. activate the env
```bash
.\env\Scripts\activate
```

3. pip install all the requirements seen in requirements.txt
```bash
pip install -r requirements.txt
```

4. move into Chatapp dir 
```bash
cd Chatapp
```

5. Now run the project app
```bash
python manage.py runserver
```

6. now vist ``http://127.0.0.1:8000/``


---

## where to put the gemini api key

To put api key go to  ``Chatapp\Chat\views.py line:76 and line:99``