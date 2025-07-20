# API de Détection Visuelle Automatisée

Ce projet propose une API web pour la détection automatique de **dommages** (fissures, trous, rayures) et d’**équipements** (prises, interrupteurs, extincteurs) à partir d’images transmises via une archive `.zip`. Il s’appuie sur **Flask**, le modèle **Qwen-VL**, **OpenCV**, et une **application iOS**.

---

##  Fonctionnalités

- Analyse automatique d’images (fissures, trous, objets)
- Génération d’annotations visuelles et calcul de dimensions physiques (mm)
- Interaction par API, interface web ou application iOS
- Upload d’archives `.zip` contenant image + calibration
- Réponse structurée : type, taille, surface, position, image annotée

---

##  Prérequis

- Python 3.8+
- `pip` installé
- (Optionnel) Compte AWS si upload vers S3 est prévu

---

##  Installation

```bash
git clone https://github.com/votre-utilisateur/votre-repo.git
cd aws_llmv_ios
pip install -r requirements.txt
```

---

##  Utilisation Locale (Test du modèle)

```bash
python local.py
```

---

##  Lancement du Serveur Flask

### En mode développement

```bash
python app.py
```

### En production avec Gunicorn

```bash
gunicorn -b 0.0.0.0:5000 app:app
```

### En tâche de fond (Linux)

```bash
nohup python app.py > flask.log 2>&1 &
```

---

## 📄 Tunnel d’accès à distance avec Ngrok

```bash
nohup ngrok http 5000 --log=stdout > ngrok.log 2>&1 &
```

Une URL publique (`https://xxxxx.ngrok-free.app`) sera générée pour l’accès via l'application iOS.

---

## 📂 Structure du Projet

```
aws_llmv_ios/
├── app.py                  # Serveur Flask
├── main_pro.py        # Traitement et interaction avec Qwen-VL
├── templates/
│   ├── index.html          # Formulaire web
│   └── result2.html        # Résultats visuels
├── uploads/                # Images reçues
├── output/                 # Images annotées
└── requirements.txt
```

---

---

## 💻 Utilisation via l’Interface Web

Accédez à `http://localhost:5000` pour :

1. Choisir un `.zip` avec image + calibration
2. Sélectionner le type : "dommages" ou "équipements"
3. Visualiser les résultats (type, dimensions, image annotée)

---

## 📱 Intégration iOS

- L’utilisateur prend une photo
- L’app crée un `.zip` contenant :
  - `image.jpg`
  - `calibration.json`
- Envoi automatique via `POST` vers le serveur Flask
- Réception d’une réponse JSON affichée dans l’app

---

## 🤖 Modèle utilisé : Qwen-VL

- Modèle vision/langage (transformer) pré-entraîné
- Utilisé pour :
  - Dessiner les boîtes englobantes
  - Identifier le type de dommage
- Piloté via **prompts textuels** dynamiques (ex. : “Identify and name the damage...”)

---
