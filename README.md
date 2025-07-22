
# 📘 Détection Visuelle Automatisée — Documentation Technique

##  Objectif du projet

Détecter automatiquement les **dommages** (fissures, trous, rayures) et **équipements** (prises, interrupteurs, extincteurs) dans les bâtiments à partir d’**images** envoyées via une app **iOS**.

➡ Le tout est analysé par un **serveur Flask** utilisant le modèle **Qwen-VL**.

---

##  Architecture du projet

 *App iOS* → 📤 *Upload ZIP (image + calibration.json)* → 🔍 *Serveur Flask avec Qwen-VL* → 🖼 *Image annotée + JSON des résultats*

---

## 📂 Structure du projet

```
Detection_dom_eq/
├── app.py                  # Serveur Flask principal
├── main_pro.py             # Traitement des images et interaction avec Qwen-VL
├── templates/
│   ├── index.html          # Interface web d’upload
│   └── result2.html        # Page résultat avec image annotée
├── uploads/                # Fichiers reçus
├── output/                 # Images annotées
└── requirements.txt        # Dépendances
```

---

## ⚙️ Lancer le projet

### 🧪 1. Installation et préparation de l’environnement

Commencez par créer un environnement virtuel :

```bash
python3 -m venv venv
source venv/bin/activate  # Sous Windows 
```

Clone ensuite le dépôt et installe les dépendances :

```bash
git clone https://github.com/BenouadahAlaEddine/detection_dommage_equipement.git
cd detection_dommage_equipement
pip install -r requirements.txt
```

---

### 🚀 2. Lancement local (mode développement)

Démarre le serveur Flask localement :

```bash
python app.py
```

Accède ensuite à l’interface Web via le navigateur à l'adresse :
[http://localhost:5000](http://localhost:5000)

---

### 🏭 3. Serveur de production (en arrière-plan)

Pour lancer le serveur de manière persistante :

```bash
nohup python app.py > flask.log 2>&1 &
```

- Les logs seront stockés dans `flask.log`
- Le serveur reste actif même après fermeture de la session

---

### 🌍 4. Exposition au réseau via Ngrok

1. Crée un compte sur [https://ngrok.com/](https://ngrok.com/) et installe Ngrok :

```bash
wget https://bin.equinox.io/c/4VmDzA7iaHb/ngrok-stable-linux-amd64.zip
unzip ngrok-stable-linux-amd64.zip
sudo mv ngrok /usr/local/bin
```

2. Authentifie de compte Ngrok :

```bash
ngrok config add-authtoken VOTRE_TOKEN_NGROK
```

3. Lance le tunnel vers le port 5000 :

```bash
nohup ngrok http 5000 --log=stdout > ngrok.log 2>&1 &
```

🔗 Une URL publique du type `https://xyz123.ngrok-free.app` sera générée automatiquement.  
➡️ Cette URL est à utiliser dans  l'application iOS pour envoyer les fichiers ZIP au serveur.

Pour afficher url :
```bash
cat ngrok.log | grep "https"
```
---

##  Fonctionnement du traitement (`main_pro.py`)

- Décompression du `.zip`
- Lecture de `calibration.json`
- Analyse de l’image avec Qwen-VL via prompts textuels
- Calcul des dimensions physiques (mm)
- Position du dommage dans l’image
- Génération image annotée + réponse structurée

---

## 🖥 Interface Web

Accessible via `http://localhost:5000`

- Upload fichier `.zip`
- Choix entre "dommages" ou "équipements"
- Résultat affiché avec :
  - Type détecté
  - Dimensions (mm)
  - Surface
  - Position
  - Image annotée

---

## 📲 Fonctionnement de l’app iOS

1. Prend une photo
2. Crée un `.zip` contenant `image.jpg` + `calibration.json`
3. Envoie automatique via `POST /upload_zip`
4. Reçoit JSON avec dimensions, type, position, et image annotée

---

##  API REST

### Endpoint : `POST /upload_zip`

#### Contenu attendu : `.zip` avec image + calibration

#### Réponse exemple :

```json
{
  "damage_type": "hole",
  "width_mm": 13,
  "height_mm": 15,
  "surface_mm2": 195,
  "position": "au milieu au centre",
  "annotated_image_url": "http://.../output/image.jpg"
}
```

---

##  Modèle Qwen-VL

Modèle vision/langage (transformer) utilisé pour :
- Identifier objets/dommages
- Dessiner des boîtes englobantes
- Retourner le type de dommage

L’interaction est faite via des **prompts textuels** générés dynamiquement.

---

## 📧 Auteur

Benouadah Alaeddine
